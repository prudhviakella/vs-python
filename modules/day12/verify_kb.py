"""
scripts/verify_kb.py

Verify S3 Vectors indexes contain the correct data after ingestion.

Runs 6 diagnostic queries against ecom-semantic and ecom-procedural
and confirms:
  - text is present in metadata (has_text=True)
  - correct chunks are retrieved for known queries
  - procedural index has relationship and query_example chunks
  - sample values are present for categorical columns

Usage (from project root):
    python scripts/verify_kb.py
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING)  # suppress boto noise

import boto3
from openai import OpenAI

REGION           = os.getenv("AWS_REGION",          "us-east-1")
S3_BUCKET        = os.getenv("S3_VECTOR_BUCKET",    "nlq-ecom-schema-vectors")
SEMANTIC_INDEX   = os.getenv("S3_SEMANTIC_INDEX",    "ecom-semantic")
PROCEDURAL_INDEX = os.getenv("S3_PROCEDURAL_INDEX",  "ecom-procedural")
EMBED_MODEL      = "text-embedding-3-small"

s3v = boto3.client("s3vectors", region_name=REGION)
oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed(text: str) -> list[float]:
    return oai.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding


def query(index: str, vector: list[float], top_k: int) -> list[dict]:
    resp = s3v.query_vectors(
        vectorBucketName = S3_BUCKET,
        indexName        = index,
        queryVector      = {"float32": vector},
        topK             = top_k,
        returnMetadata   = True,
        returnDistance   = True,
    )
    results = []
    for v in resp.get("vectors", []):
        meta = v.get("metadata", {})
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: pass
        results.append({
            "key":      v.get("key", ""),
            "metadata": meta,
            "score":    round(v.get("distance", 0), 4),
        })
    return results


def check(label: str, condition: bool, detail: str = ""):
    icon = "✅" if condition else "❌"
    msg  = f"  {icon}  {label}"
    if detail: msg += f"\n       {detail}"
    print(msg)
    return condition


all_pass = True

print()
print("=" * 60)
print("  vs-NLQ Knowledge Base Verification")
print(f"  Bucket  : {S3_BUCKET}")
print(f"  Semantic: {SEMANTIC_INDEX}")
print(f"  Proc    : {PROCEDURAL_INDEX}")
print("=" * 60)

# ── Test 1: Revenue query retrieves order_items + products + orders ────────────
print("\n[ Test 1 ] Revenue query → order_items, products, orders")
v1      = embed("top 5 products by revenue")
r1      = query(SEMANTIC_INDEX, v1, 15)
tables  = {r["metadata"].get("table", "") for r in r1}
r1_pass = True

for must in ["order_items", "products", "orders"]:
    ok = must in tables
    all_pass = all_pass and ok
    r1_pass  = r1_pass and ok
    check(f"  {must} table in top-15 results", ok)

has_text_r1 = all(r["metadata"].get("text", "") != "" for r in r1)
all_pass = all_pass and has_text_r1
check(f"  text present in all {len(r1)} retrieved metadata", has_text_r1)


# ── Test 2: Date query retrieves orders.order_date ─────────────────────────────
print("\n[ Test 2 ] Date query → orders.order_date present")
v2   = embed("delivered orders this month date filter")
r2   = query(SEMANTIC_INDEX, v2, 15)
cols = {(r["metadata"].get("table",""), r["metadata"].get("column","")) for r in r2}
ok   = ("orders", "order_date") in cols
all_pass = all_pass and ok
check("orders.order_date in top-15 results", ok)
if not ok:
    retrieved = [(r["metadata"].get("table","?"), r["metadata"].get("column", r["metadata"].get("pk","overview"))) for r in r2]
    print(f"       Retrieved instead: {retrieved}")


# ── Test 3: order_status has correct sample_values ────────────────────────────
print("\n[ Test 3 ] orders.order_status has correct sample_values")
v3   = embed("order status filter cancelled delivered")
r3   = query(SEMANTIC_INDEX, v3, 10)
status_chunk = next(
    (r for r in r3
     if r["metadata"].get("table") == "orders"
     and r["metadata"].get("column") == "order_status"),
    None
)
if status_chunk:
    vals    = status_chunk["metadata"].get("sample_values", [])
    correct = sorted(vals) == sorted(["Cancelled","Delivered","Processing","Returned","Shipped"])
    all_pass = all_pass and correct
    check("orders.order_status sample_values correct",
          correct, f"Got: {vals}")
    has_text = bool(status_chunk["metadata"].get("text",""))
    all_pass = all_pass and has_text
    check("orders.order_status has text in metadata", has_text)
else:
    all_pass = False
    check("orders.order_status chunk found in top-10", False)


# ── Test 4: Procedural index has relationships ─────────────────────────────────
print("\n[ Test 4 ] Procedural index — relationships present")
v4   = embed("join order_items products revenue")
r4   = query(PROCEDURAL_INDEX, v4, 10)
if not r4:
    all_pass = False
    check("procedural index has vectors", False,
          "ecom-procedural returned 0 results — re-ingest procedural_ecom.json")
else:
    check(f"procedural index has vectors ({len(r4)} returned)", True)
    types = {r["metadata"].get("chunk_type","") for r in r4}
    has_rel = "relationship" in types
    all_pass = all_pass and has_rel
    check("relationship chunks present", has_rel, f"chunk_types: {types}")

    # Check specific join
    join_chunk = next(
        (r for r in r4
         if r["metadata"].get("source_table") == "order_items"
         and r["metadata"].get("target_table") == "products"),
        None
    )
    ok = join_chunk is not None
    all_pass = all_pass and ok
    check("order_items → products relationship retrieved", ok)


# ── Test 5: Procedural index has query examples ────────────────────────────────
print("\n[ Test 5 ] Procedural index — query examples present")
v5   = embed("top 5 products by revenue example")
r5   = query(PROCEDURAL_INDEX, v5, 10)
if r5:
    qex = next((r for r in r5 if r["metadata"].get("chunk_type") == "query_example"), None)
    ok  = qex is not None
    all_pass = all_pass and ok
    check("query_example chunks present", ok)
    if qex:
        text = qex["metadata"].get("text", "")
        uses_delivered = "'Delivered'" in text
        all_pass = all_pass and uses_delivered
        check("query example uses 'Delivered' not 'completed'", uses_delivered,
              f"text snippet: {text[text.find('WHERE'):text.find('WHERE')+60]}" if 'WHERE' in text else "")


# ── Test 6: Shipments carrier has correct values ──────────────────────────────
print("\n[ Test 6 ] shipments.carrier has correct sample_values")
v6   = embed("carrier FedEx UPS shipping")
r6   = query(SEMANTIC_INDEX, v6, 10)
carrier_chunk = next(
    (r for r in r6
     if r["metadata"].get("table") == "shipments"
     and r["metadata"].get("column") == "carrier"),
    None
)
if carrier_chunk:
    vals    = carrier_chunk["metadata"].get("sample_values", [])
    correct = sorted(vals) == sorted(["DHL","FedEx","OnTrac","UPS","USPS"])
    all_pass = all_pass and correct
    check("shipments.carrier sample_values correct", correct, f"Got: {vals}")
else:
    all_pass = False
    check("shipments.carrier chunk found", False)


# ── Summary ────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
if all_pass:
    print("  ALL TESTS PASSED ✅  Knowledge base is ready")
else:
    print("  SOME TESTS FAILED ❌  Fix issues above then re-ingest")
print("=" * 60)
print()
sys.exit(0 if all_pass else 1)
