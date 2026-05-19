"""
test_schema_rag.py — Validates semantic + procedural memory.

Loads test cases from test_cases.json (no hardcoding).
Tests ALL query variants per case — formal English + informal/messy.
Tests procedural memory for join patterns.

Usage:
    python test_schema_rag.py                        # all tiers
    python test_schema_rag.py --tier complex         # complex only
    python test_schema_rag.py --id tc013             # single case
    python test_schema_rag.py --id tc013 --verbose   # full detail
"""

import os, json, math, argparse, logging
from pathlib import Path
from dotenv import load_dotenv
import boto3
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env", override=True)
logging.basicConfig(level=logging.WARNING)

REGION           = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME      = os.getenv("S3_VECTOR_BUCKET", "nlq-ecom-schema-vectors")
SEMANTIC_INDEX   = os.getenv("S3_SEMANTIC_INDEX", "ecom-semantic")
PROCEDURAL_INDEX = os.getenv("S3_PROCEDURAL_INDEX", "ecom-procedural")
EMBED_MODEL      = "text-embedding-3-small"
EMBED_DIM        = 1536
CASES_FILE       = Path(os.getenv("TEST_CASES_FILE",
                         str(Path(__file__).parent / "test_cases.json")))

oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
s3v = boto3.client("s3vectors", region_name=REGION)


def embed(text: str) -> list[float]:
    return oai.embeddings.create(
        model=EMBED_MODEL, input=text, dimensions=EMBED_DIM
    ).data[0].embedding


def search(index: str, vec: list[float], top_k: int, filter_expr: dict) -> list[dict]:
    return s3v.query_vectors(
        vectorBucketName=BUCKET_NAME, indexName=index,
        queryVector={"float32": vec}, topK=top_k,
        returnMetadata=True, filter=filter_expr,
    ).get("vectors", [])


def load_cases(tier_filter: str, id_filter) -> list[dict]:
    if not CASES_FILE.exists():
        raise FileNotFoundError(f"Test cases file not found: {CASES_FILE}")
    data  = json.load(open(CASES_FILE))
    cases = data["test_cases"]
    if tier_filter != "all":
        cases = [c for c in cases if c["tier"] == tier_filter]
    if id_filter:
        cases = [c for c in cases if c["id"] == id_filter]
    return cases


def test_query(query: str, tc: dict) -> dict:
    vec = embed(query)

    # Semantic Pass 1 — identify tables
    t_results    = search(SEMANTIC_INDEX, vec, 5,
                          {"chunk_type": {"$eq": "table_overview"}})
    found_tables = {r["metadata"].get("table", "") for r in t_results}
    found_tables.discard("")
    expect_t  = set(tc["expect_tables"])
    table_hit = bool(found_tables & expect_t)

    # Semantic Pass 2 — columns per identified table
    all_cols      = set()
    table_col_map = {}
    for table in found_tables:
        c_results = search(SEMANTIC_INDEX, vec, 8,
                           {"$and": [{"chunk_type": {"$eq": "column_detail"}},
                                     {"table":      {"$eq": table}}]})
        cols = {r["metadata"].get("column", "") for r in c_results}
        cols.discard("")
        all_cols |= cols
        table_col_map[table] = sorted(cols)

    expect_c  = set(tc["expect_columns"])
    threshold = math.ceil(len(expect_c) / 2)
    col_hits  = all_cols & expect_c
    col_hit   = len(col_hits) >= threshold

    # Procedural Pass 3 — relationship / join chunks
    j_results   = search(PROCEDURAL_INDEX, vec, 5,
                         {"chunk_type": {"$eq": "relationship"}})
    join_tables = {r["metadata"].get("table", "") for r in j_results}
    join_tables.discard("")
    expect_jt = set(tc.get("expect_join_tables", []))
    join_hit  = not expect_jt or bool(join_tables & expect_jt)

    # Procedural Pass 4 — query examples
    e_results   = search(PROCEDURAL_INDEX, vec, 3,
                         {"chunk_type": {"$eq": "query_example"}})
    example_ids = [r["metadata"].get("chunk_id", "") for r in e_results]

    return {
        "table_hit":     table_hit,
        "col_hit":       col_hit,
        "join_hit":      join_hit,
        "found_tables":  found_tables,
        "col_hits":      col_hits,
        "missing_t":     expect_t - found_tables,
        "missing_c":     expect_c - all_cols,
        "join_tables":   join_tables,
        "missing_jt":    expect_jt - join_tables,
        "example_ids":   example_ids,
        "table_col_map": table_col_map,
        "threshold":     threshold,
    }


def run_case(tc: dict, verbose: bool) -> dict:
    queries         = tc["queries"]
    variant_results = []

    for i, query in enumerate(queries):
        is_formal = (i == 0)
        label     = "formal  " if is_formal else "informal"
        r         = test_query(query, tc)
        all_pass  = r["table_hit"] and r["col_hit"] and r["join_hit"]
        icon      = "✅" if all_pass else "❌"

        print(f"\n  {icon} [{label}] \"{query}\"")

        if verbose or not all_pass:
            t_icon = "✅" if r["table_hit"] else "❌"
            c_icon = "✅" if r["col_hit"]   else "❌"
            j_icon = "✅" if r["join_hit"]  else "⚠️ "

            print(f"       Tables  {t_icon}  found={sorted(r['found_tables'])}"
                  + (f"  ❌missing={sorted(r['missing_t'])}" if r["missing_t"] else ""))

            for table, cols in sorted(r["table_col_map"].items()):
                mark = "→" if table in set(tc["expect_tables"]) else " "
                print(f"         {mark} {table:<28} {cols}")

            print(f"       Columns {c_icon}  "
                  f"need≥{r['threshold']}/{len(tc['expect_columns'])}  "
                  f"found={sorted(r['col_hits'])}"
                  + (f"  ❌missing={sorted(r['missing_c'])}" if r["missing_c"] else ""))

            print(f"       Joins   {j_icon}  found={sorted(r['join_tables'])}"
                  f"  need={sorted(tc.get('expect_join_tables', []))}"
                  + (f"  ❌missing={sorted(r['missing_jt'])}" if r["missing_jt"] else ""))

            print(f"       SQL ex  {r['example_ids']}")

        variant_results.append(all_pass)

    pass_count = sum(variant_results)
    total      = len(variant_results)
    formal_p   = variant_results[0]
    informal_p = all(variant_results[1:]) if len(variant_results) > 1 else True

    print(f"\n  ─ Summary: formal={'✅' if formal_p else '❌'}  "
          f"informal={'✅' if informal_p else '❌'}  "
          f"({pass_count}/{total} variants pass)")

    return {
        "id":       tc["id"],
        "desc":     tc["description"],
        "tier":     tc["tier"],
        "formal":   formal_p,
        "informal": informal_p,
        "all":      all(variant_results),
        "variants": variant_results,
    }


def run_tests(tier_filter: str, id_filter, verbose: bool):
    cases = load_cases(tier_filter, id_filter)

    print("=" * 85)
    print(f"Schema RAG Test  |  tier={tier_filter}  |  {len(cases)} cases  "
          f"|  file={CASES_FILE.name}")
    print(f"Semantic   : {SEMANTIC_INDEX}")
    print(f"Procedural : {PROCEDURAL_INDEX}")
    print("=" * 85)

    by_tier: dict[str, list[dict]] = {"simple": [], "medium": [], "complex": []}

    for tc in cases:
        n_informal = len(tc["queries"]) - 1
        print(f"\n{'─'*85}")
        print(f"[{tc['id']}] [{tc['tier'].upper()}] {tc['description']}"
              f"  (1 formal + {n_informal} informal variants)")
        print(f"{'─'*85}")
        result = run_case(tc, verbose)
        by_tier[tc["tier"]].append(result)

    # Summary table
    print(f"\n{'='*85}")
    print(f"{'TIER':<10} {'CASES':<7} {'FORMAL':<18} {'INFORMAL':<18} {'ALL VARIANTS'}")
    print(f"{'─'*10} {'─'*6} {'─'*17} {'─'*17} {'─'*12}")

    g_cases = g_formal = g_informal = g_vp = g_vt = 0
    for tier in ["simple", "medium", "complex"]:
        rs = by_tier[tier]
        if not rs:
            continue
        n      = len(rs)
        fp     = sum(1 for r in rs if r["formal"])
        ip     = sum(1 for r in rs if r["informal"])
        vp     = sum(sum(r["variants"]) for r in rs)
        vt     = sum(len(r["variants"])  for r in rs)
        print(f"  {tier:<8}  {n:<6}  "
              f"{fp}/{n} ({fp/n*100:.0f}%)          "
              f"{ip}/{n} ({ip/n*100:.0f}%)          "
              f"{vp}/{vt}")
        g_cases += n; g_formal += fp; g_informal += ip
        g_vp += vp;   g_vt += vt

    if g_cases:
        print(f"{'─'*85}")
        print(f"  {'TOTAL':<8}  {g_cases:<6}  "
              f"{g_formal}/{g_cases} ({g_formal/g_cases*100:.1f}%)          "
              f"{g_informal}/{g_cases} ({g_informal/g_cases*100:.1f}%)          "
              f"{g_vp}/{g_vt}")
    print("=" * 85)

    all_results = [r for rs in by_tier.values() for r in rs]
    failures    = [r for r in all_results if not r["all"]]
    if failures:
        print(f"\n⚠️  {len(failures)} case(s) with failing variants:")
        for r in failures:
            failed = [("formal" if i == 0 else f"informal-{i}")
                      for i, v in enumerate(r["variants"]) if not v]
            print(f"  [{r['tier']}] {r['id']} — {r['desc']}")
            print(f"    failing: {failed}")
    else:
        print("\n🎉  All variants passing — ready to build the agent!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="all",
                        choices=["all", "simple", "medium", "complex"])
    parser.add_argument("--id",      default=None, help="Single case ID e.g. tc013")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full detail for all variants")
    args = parser.parse_args()
    run_tests(args.tier, args.id, args.verbose)