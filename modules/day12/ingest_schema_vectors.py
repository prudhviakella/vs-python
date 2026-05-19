import os, json, time, logging
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env", override=True)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

REGION           = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME      = os.getenv("S3_VECTOR_BUCKET", "nlq-ecom-schema-vectors")
SEMANTIC_INDEX   = os.getenv("S3_SEMANTIC_INDEX", "ecom-semantic")
PROCEDURAL_INDEX = os.getenv("S3_PROCEDURAL_INDEX", "ecom-procedural")
KB_DIR           = Path(os.getenv("KNOWLEDGE_BASE_DIR", "./knowledge_base"))
CACHE_FILE       = Path(os.getenv("EMBEDDINGS_CACHE",
                         str(Path(__file__).parent / "embeddings_cache.json")))
EMBED_MODEL      = "text-embedding-3-small"
EMBED_DIM        = 1536
BATCH_SIZE       = 500
SEMANTIC_TYPES   = {"table_overview", "column_detail"}
PROCEDURAL_TYPES = {"relationship", "query_example"}


def clean_cache():
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        log.info("Deleted cache: %s", CACHE_FILE)
    else:
        log.info("No cache — starting fresh")


def delete_index(s3v, name):
    try:
        s3v.delete_index(vectorBucketName=BUCKET_NAME, indexName=name)
        log.info("Deleted index: %s", name)
        time.sleep(2)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code not in ("ResourceNotFoundException", "NotFoundException", "NoSuchKey"):
            log.warning("Could not delete %s: %s", name, code)
        else:
            log.info("Index not found (skip): %s", name)


def delete_bucket(s3v):
    try:
        s3v.delete_vector_bucket(vectorBucketName=BUCKET_NAME)
        log.info("Deleted bucket: %s", BUCKET_NAME)
        time.sleep(2)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code not in ("ResourceNotFoundException", "NoSuchBucket", "NotFoundException"):
            log.warning("Could not delete bucket: %s", code)


def create_bucket(s3v):
    try:
        s3v.create_vector_bucket(vectorBucketName=BUCKET_NAME)
        log.info("Created bucket: %s", BUCKET_NAME)
        time.sleep(1)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code not in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou", "ConflictException"):
            raise


def create_index(s3v, name):
    try:
        s3v.create_index(
            vectorBucketName=BUCKET_NAME, indexName=name,
            dataType="float32", dimension=EMBED_DIM, distanceMetric="cosine",
        )
        log.info("Created index: %s", name)
        time.sleep(2)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code not in ("IndexAlreadyExists", "ConflictException", "ResourceInUseException"):
            log.error("Failed to create %s: %s", name, code)
            raise


def clean_and_setup(s3v):
    delete_index(s3v, SEMANTIC_INDEX)
    delete_index(s3v, PROCEDURAL_INDEX)
    delete_bucket(s3v)
    create_bucket(s3v)
    create_index(s3v, SEMANTIC_INDEX)
    create_index(s3v, PROCEDURAL_INDEX)


def load_and_split():
    """
    Load all KB files and split into semantic and procedural chunks.

    FIX 1: Now reads BOTH semantic_*.json AND procedural_*.json files.
    The original script only read semantic_*.json, leaving procedural_ecom.json
    completely unprocessed.

    semantic_*.json   — have a top-level "table" key
    procedural_*.json — no "table" key; use source_table from chunk metadata
    """
    seen = {}

    # ── Semantic files (have top-level "table" key) ────────────────────────────
    sem_files = sorted(KB_DIR.glob("semantic_*.json"))
    if not sem_files:
        raise FileNotFoundError(f"No semantic_*.json files in {KB_DIR}")

    for path in sem_files:
        data  = json.load(open(path))
        table = data["table"]
        for chunk in data.get("chunks", []):
            cid = chunk["chunk_id"]
            if cid in seen:
                log.warning("Duplicate %r — overwriting with %s", cid, path.name)
            seen[cid] = {
                "chunk_id":   cid,
                "table":      table,
                "chunk_type": chunk.get("chunk_type", "general"),
                "text":       chunk["text"],
                "metadata":   chunk.get("metadata", {}),
            }
        log.info("  %-45s  %d chunks", path.name, len(data.get("chunks", [])))

    # ── Procedural files (no top-level "table" key) ────────────────────────────
    proc_files = sorted(KB_DIR.glob("procedural_*.json"))
    for path in proc_files:
        data = json.load(open(path))
        for chunk in data.get("chunks", []):
            cid  = chunk["chunk_id"]
            meta = chunk.get("metadata", {})
            # Use source_table for relationships, empty string for query examples
            table = meta.get("source_table", meta.get("table", ""))
            if cid in seen:
                log.warning("Duplicate %r — overwriting with %s", cid, path.name)
            seen[cid] = {
                "chunk_id":   cid,
                "table":      table,
                "chunk_type": chunk.get("chunk_type", "general"),
                "text":       chunk["text"],
                "metadata":   meta,
            }
        log.info("  %-45s  %d chunks", path.name, len(data.get("chunks", [])))

    all_chunks = list(seen.values())
    semantic   = [c for c in all_chunks if c["chunk_type"] in SEMANTIC_TYPES]
    procedural = [c for c in all_chunks if c["chunk_type"] in PROCEDURAL_TYPES]
    log.info("Total %d → semantic=%d  procedural=%d",
             len(all_chunks), len(semantic), len(procedural))
    return semantic, procedural


def embed_all(chunks, oai):
    cache = {}
    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        cid = chunk["chunk_id"]
        log.info("  [%d/%d] %s", i, total, cid)
        resp = oai.embeddings.create(
            model=EMBED_MODEL, input=chunk["text"][:8000], dimensions=EMBED_DIM)
        cache[cid] = resp.data[0].embedding
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
        time.sleep(0.05)
    return cache


def build_vectors(chunks, cache):
    """
    Build S3 Vectors put_vectors payload.

    FIX 2: Now stores all fields needed by schema_retriever.py:
      text           — rich description text (for schema context injection)
      sample_values  — valid categorical values as JSON string
      source_table / target_table / source_column / target_column
                     — relationship metadata for JOIN context
      question       — query example question for similarity matching
      pk / fks       — table overview metadata

    Note: is_pk and is_fk are stored as strings "True"/"False" per original
    script convention. schema_retriever.py handles this correctly.
    """
    vectors = []
    for chunk in chunks:
        cid = chunk["chunk_id"]
        raw = chunk.get("metadata", {})

        meta = {
            "table":      chunk.get("table", ""),
            "chunk_type": chunk["chunk_type"],
            "chunk_id":   cid,
        }

        # ── Core column/table fields ───────────────────────────────────────────
        if "column" in raw:  meta["column"] = str(raw["column"])
        if "entity" in raw:  meta["entity"] = str(raw["entity"])
        if "is_pk"  in raw:  meta["is_pk"]  = str(raw["is_pk"])
        if "is_fk"  in raw:  meta["is_fk"]  = str(raw["is_fk"])
        if "pk"     in raw:  meta["pk"]     = str(raw["pk"])
        if "type"   in raw:  meta["type"]   = str(raw["type"])

        # ── Rich text (needed by schema_retriever to build schema context) ─────
        text_val = raw.get("text", "")
        if text_val:
            # S3 Vectors metadata values are strings; trim to avoid size limits
            meta["text"] = str(text_val)[:2000]

        # ── Sample values for categorical columns ─────────────────────────────
        sample_vals = raw.get("sample_values", [])
        if sample_vals:
            meta["sample_values"] = json.dumps(sample_vals)

        # ── Relationship fields (for JOIN context in procedural chunks) ────────
        if "source_table"  in raw: meta["source_table"]  = str(raw["source_table"])
        if "source_column" in raw: meta["source_column"] = str(raw["source_column"])
        if "target_table"  in raw: meta["target_table"]  = str(raw["target_table"])
        if "target_column" in raw: meta["target_column"] = str(raw["target_column"])

        # ── Query example fields ───────────────────────────────────────────────
        if "question" in raw: meta["question"] = str(raw["question"])

        vectors.append({"key": cid, "data": {"float32": cache[cid]}, "metadata": meta})
    return vectors


def upload(s3v, index_name, vectors):
    total = len(vectors)
    for i in range(0, total, BATCH_SIZE):
        batch = vectors[i: i + BATCH_SIZE]
        s3v.put_vectors(vectorBucketName=BUCKET_NAME, indexName=index_name, vectors=batch)
        log.info("  [%s] batch [%d-%d / %d]", index_name, i+1, i+len(batch), total)
        time.sleep(0.1)


def main():
    log.info("KB_DIR           : %s", KB_DIR.resolve())
    log.info("Bucket           : %s", BUCKET_NAME)
    log.info("Semantic index   : %s  (table_overview + column_detail)", SEMANTIC_INDEX)
    log.info("Procedural index : %s  (relationship + query_example)", PROCEDURAL_INDEX)
    log.info("Region           : %s", REGION)
    log.info("Embed model      : %s  (%d dims)", EMBED_MODEL, EMBED_DIM)

    s3v = boto3.client("s3vectors", region_name=REGION)
    oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    log.info("=== Step 0: Clean slate ===")
    clean_cache()
    clean_and_setup(s3v)

    log.info("=== Step 1: Load + split ===")
    semantic_chunks, procedural_chunks = load_and_split()

    log.info("=== Step 2: Embed %d chunks ===",
             len(semantic_chunks) + len(procedural_chunks))
    cache = embed_all(semantic_chunks + procedural_chunks, oai)

    log.info("=== Step 3: Upload semantic (%d vectors) ===", len(semantic_chunks))
    upload(s3v, SEMANTIC_INDEX, build_vectors(semantic_chunks, cache))

    log.info("=== Step 4: Upload procedural (%d vectors) ===", len(procedural_chunks))
    upload(s3v, PROCEDURAL_INDEX, build_vectors(procedural_chunks, cache))

    log.info("=== Done ===")
    log.info("Semantic   → %s  (%d vectors)", SEMANTIC_INDEX, len(semantic_chunks))
    log.info("Procedural → %s  (%d vectors)", PROCEDURAL_INDEX, len(procedural_chunks))
    for ct, n in sorted(Counter(c["chunk_type"] for c in semantic_chunks).items()):
        log.info("  semantic   %-20s %d", ct, n)
    for ct, n in sorted(Counter(c["chunk_type"] for c in procedural_chunks).items()):
        log.info("  procedural %-20s %d", ct, n)


if __name__ == "__main__":
    main()