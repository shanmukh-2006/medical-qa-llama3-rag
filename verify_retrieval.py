"""
Phase 2 Verification Script
-----------------------------
1. Confirms index/embedding files exist and prints sizes.
2. Confirms embedding count == 36,723.
3. Tests retrieval with 3 medical questions (top-5 each).
4. Runs determinism check (same query twice → identical results).
"""

import os
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
INDEX_FILE       = os.path.join(VECTOR_STORE_DIR, "textbook_faiss.index")
CHECKPOINT_FILE  = os.path.join(VECTOR_STORE_DIR, "textbook_embeddings_checkpoint.npy")
METADATA_FILE    = os.path.join(VECTOR_STORE_DIR, "textbook_metadata.parquet")
MODEL_NAME       = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_COUNT   = 36_723

SAMPLE_QUESTIONS = [
    "What causes chest pain radiating to the left arm?",
    "Which vitamin deficiency causes scurvy?",
    "What is the first-line treatment for type 2 diabetes?",
]

SEP  = "=" * 70
SEP2 = "-" * 70

def fmt_size(path):
    size = os.path.getsize(path)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"

# ── STEP 1: File existence & sizes ────────────────────────────────────────────
print(SEP)
print("  STEP 1 — FILE EXISTENCE & SIZES")
print(SEP)

files = {
    "FAISS index":          INDEX_FILE,
    "Embeddings checkpoint": CHECKPOINT_FILE,
    "Chunk metadata":       METADATA_FILE,
}

all_ok = True
for label, path in files.items():
    exists = os.path.exists(path)
    if exists:
        print(f"  [OK]  {label:25s}  {fmt_size(path):>10s}   {path}")
    else:
        print(f"  [MISSING]  {label:25s}  {path}")
        all_ok = False

if not all_ok:
    print("\nERROR: One or more required files are missing. Aborting.")
    raise SystemExit(1)

# ── STEP 2: Embedding count verification ──────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 2 — EMBEDDING COUNT VERIFICATION")
print(SEP)

embeddings  = np.load(CHECKPOINT_FILE)
embed_count = len(embeddings)
embed_dim   = embeddings.shape[1]
count_ok    = embed_count == EXPECTED_COUNT

print(f"  Embeddings shape   : {embeddings.shape}  (count x dim)")
print(f"  Expected count     : {EXPECTED_COUNT:,}")
print(f"  Actual count       : {embed_count:,}")
print(f"  Dimension          : {embed_dim}")
print(f"  Count match        : {'PASS' if count_ok else 'FAIL'}")

index = faiss.read_index(INDEX_FILE)
faiss_count = index.ntotal
print(f"  FAISS index vectors: {faiss_count:,}  ({'PASS' if faiss_count == EXPECTED_COUNT else 'FAIL'})")

df_meta = pd.read_parquet(METADATA_FILE)
print(f"  Metadata rows      : {len(df_meta):,}  ({'PASS' if len(df_meta) == EXPECTED_COUNT else 'FAIL'})")

# ── STEP 3 & 4: Load model and run retrieval tests ────────────────────────────
print(f"\n{SEP}")
print("  STEP 3 — LOADING MODEL FOR RETRIEVAL")
print(SEP)
print(f"  Model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print("  Model loaded successfully.\n")

def retrieve(query, top_k=5):
    vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, indices = index.search(vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(df_meta):
            continue
        row = df_meta.iloc[idx]
        results.append({
            "rank":    len(results) + 1,
            "score":   float(score),
            "book":    row.get("source_textbook", ""),
            "chunk_id": row.get("chunk_id", ""),
            "text":    row.get("chunk_text", ""),
        })
    return results

print(SEP)
print("  STEP 4 — RETRIEVAL TEST (TOP-5 PER QUESTION)")
print(SEP)

all_results = {}
for q in SAMPLE_QUESTIONS:
    print(f"\n  QUERY: \"{q}\"")
    print(SEP2)
    results = retrieve(q)
    all_results[q] = results
    for r in results:
        snippet = r["text"][:350].replace("\n", " ")
        if len(r["text"]) > 350:
            snippet += "..."
        print(f"  Rank {r['rank']} | Score: {r['score']:.4f} | {r['book']} | {r['chunk_id']}")
        print(f"  Snippet: {snippet}")
        print()

# ── STEP 5: Determinism check ─────────────────────────────────────────────────
print(SEP)
print("  STEP 5 — DETERMINISM CHECK")
print(SEP)

for q in SAMPLE_QUESTIONS:
    run1 = retrieve(q)
    run2 = retrieve(q)
    ids1 = [(r["chunk_id"], round(r["score"], 6)) for r in run1]
    ids2 = [(r["chunk_id"], round(r["score"], 6)) for r in run2]
    match = ids1 == ids2
    print(f"  \"{q[:55]}...\"")
    print(f"    Run1 top-1: {run1[0]['chunk_id']}  score={run1[0]['score']:.6f}")
    print(f"    Run2 top-1: {run2[0]['chunk_id']}  score={run2[0]['score']:.6f}")
    print(f"    All 5 identical: {'PASS' if match else 'FAIL'}\n")

print(SEP)
print("  VERIFICATION COMPLETE")
print(SEP)
