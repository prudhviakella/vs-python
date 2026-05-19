import os, logging, asyncio
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import boto3
import asyncpg
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env", override=True)
log = logging.getLogger(__name__)

REGION           = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME      = os.getenv("S3_VECTOR_BUCKET", "nlq-ecom-schema-vectors")
SEMANTIC_INDEX   = os.getenv("S3_SEMANTIC_INDEX", "ecom-semantic")
PROCEDURAL_INDEX = os.getenv("S3_PROCEDURAL_INDEX", "ecom-procedural")
EMBED_MODEL      = "text-embedding-3-small"
EMBED_DIM        = 1536
TOP_K_TABLES     = 5
TOP_K_COLUMNS    = 8
TOP_K_JOINS      = 5
TOP_K_EXAMPLES   = 3


@dataclass
class ColumnInfo:
    column_name: str
    data_type:   str
    is_pk:       bool = False
    is_fk:       bool = False
    confirmed:   bool = False


@dataclass
class TableContext:
    table_name: str
    columns:    list[ColumnInfo] = field(default_factory=list)


@dataclass
class SchemaContext:
    tables:         list[TableContext]
    join_hints:     list[str]
    sql_examples:   list[str]
    token_estimate: int = 0

    def to_prompt_block(self) -> str:
        lines = ["=== RELEVANT SCHEMA ===\n"]
        for tbl in self.tables:
            lines.append(f"TABLE: {tbl.table_name}")
            lines.append("  COLUMNS:")
            for col in tbl.columns:
                pk = " [PK]" if col.is_pk else ""
                fk = " [FK]" if col.is_fk else ""
                lines.append(f"    {col.column_name:<30} {col.data_type}{pk}{fk}")
            lines.append("")
        if self.join_hints:
            lines.append("JOIN HINTS:")
            for jh in self.join_hints:
                lines.append(f"  {jh}")
            lines.append("")
        if self.sql_examples:
            lines.append("QUERY PATTERNS:")
            for ex in self.sql_examples[:2]:
                lines.append(f"  {ex[:200]}")
        return "\n".join(lines)


def _s3v():
    return boto3.client("s3vectors", region_name=REGION)

def _oai():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _embed(oai_client, text):
    return oai_client.embeddings.create(
        model=EMBED_MODEL, input=text[:8000], dimensions=EMBED_DIM
    ).data[0].embedding


def _search(s3v, index, vec, top_k, filter_expr):
    resp = s3v.query_vectors(
        vectorBucketName=BUCKET_NAME, indexName=index,
        queryVector={"float32": vec}, topK=top_k,
        returnMetadata=True, filter=filter_expr,
    )
    return resp.get("vectors", [])


async def _confirm_columns(pg_conn, table_columns: dict, schema="public"):
    confirmed = {}
    for table, cols in table_columns.items():
        if not cols:
            rows = await pg_conn.fetch(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema=$1 AND table_name=$2 ORDER BY ordinal_position",
                schema, table)
            confirmed[table] = [dict(r) for r in rows]
        else:
            rows = await pg_conn.fetch(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema=$1 AND table_name=$2 "
                "AND column_name=ANY($3::text[]) ORDER BY ordinal_position",
                schema, table, cols)
            found   = {r["column_name"] for r in rows}
            missing = set(cols) - found
            if len(missing) > len(cols) // 2:
                log.warning("%s: >50%% S3 columns not in DB — fetching all", table)
                rows = await pg_conn.fetch(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema=$1 AND table_name=$2 ORDER BY ordinal_position",
                    schema, table)
            confirmed[table] = [dict(r) for r in rows]
    return confirmed


async def retrieve_schema_context(question: str, pg_conn,
                                  pg_schema: str = "public") -> SchemaContext:
    s3v = _s3v()
    oai = _oai()
    vec = _embed(oai, question)

    # Pass 1 — semantic: identify tables
    t_results = _search(s3v, SEMANTIC_INDEX, vec, TOP_K_TABLES,
                        {"chunk_type": {"$eq": "table_overview"}})
    tables = [r["metadata"]["table"] for r in t_results
              if r.get("metadata", {}).get("table")]
    log.info("Pass 1 → tables: %s", tables)

    # Pass 2 — semantic: columns per table (zero query_example noise)
    table_s3_cols: dict[str, list[str]] = {}
    table_s3_meta: dict[str, list[dict]] = {}
    for table in tables:
        c_results = _search(s3v, SEMANTIC_INDEX, vec, TOP_K_COLUMNS,
                            {"$and": [{"chunk_type": {"$eq": "column_detail"}},
                                      {"table":      {"$eq": table}}]})
        cols = [r["metadata"].get("column", "") for r in c_results]
        cols = [c for c in cols if c]
        table_s3_cols[table] = cols
        table_s3_meta[table] = [r.get("metadata", {}) for r in c_results]
        log.info("Pass 2 → %s: %s", table, cols)

    # Pass 3 — procedural: join hints
    j_results = _search(s3v, PROCEDURAL_INDEX, vec, TOP_K_JOINS,
                        {"chunk_type": {"$eq": "relationship"}})
    join_hints = [r["metadata"].get("chunk_id", "") for r in j_results
                  if r["metadata"].get("table") in tables]
    log.info("Pass 3 → %d join hints", len(join_hints))

    # Pass 4 — procedural: query examples
    e_results = _search(s3v, PROCEDURAL_INDEX, vec, TOP_K_EXAMPLES,
                        {"chunk_type": {"$eq": "query_example"}})
    sql_examples = [r["metadata"].get("chunk_id", "") for r in e_results]
    log.info("Pass 4 → %d query examples", len(sql_examples))

    # Pass 5 — Postgres: confirm column names + data types
    confirmed = await _confirm_columns(pg_conn, table_s3_cols, pg_schema)

    # Build SchemaContext
    table_contexts = []
    for table in tables:
        pg_cols  = confirmed.get(table, [])
        s3_meta  = {m.get("column"): m for m in table_s3_meta.get(table, [])}
        col_infos = []
        for pgc in pg_cols:
            col_name = pgc["column_name"]
            sm = s3_meta.get(col_name, {})
            col_infos.append(ColumnInfo(
                column_name = col_name,
                data_type   = pgc["data_type"],
                is_pk       = sm.get("is_pk", "False") == "True",
                is_fk       = sm.get("is_fk", "False") == "True",
                confirmed   = True,
            ))
        table_contexts.append(TableContext(table_name=table, columns=col_infos))

    ctx = SchemaContext(
        tables       = table_contexts,
        join_hints   = join_hints,
        sql_examples = sql_examples,
    )
    ctx.token_estimate = len(ctx.to_prompt_block()) // 4
    log.info("Context: %d tables, %d cols, ~%d tokens",
             len(table_contexts),
             sum(len(t.columns) for t in table_contexts),
             ctx.token_estimate)
    return ctx


async def _test():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "ecom"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )
    for q in [
        "What is the total revenue last month?",
        "Top 10 best selling products by units sold",
        "Which warehouses have low stock for top selling products?",
        "Payment failure rate breakdown by provider",
        "Customers who spent more than $5000 and their favourite brand",
    ]:
        print(f"\n{'='*70}\nQ: {q}\n{'='*70}")
        ctx = await retrieve_schema_context(q, conn)
        print(ctx.to_prompt_block())
        print(f"~{ctx.token_estimate} tokens")
    await conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    asyncio.run(_test())