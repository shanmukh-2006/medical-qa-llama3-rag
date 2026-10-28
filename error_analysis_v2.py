"""
error_analysis_v2.py — Part C error analysis on rag_v2_test.jsonl.
Same bucket rules, same 10-sample seed as analyze_rag.py.
Reads existing files ONLY — does not modify any existing files.
Writes results/error_analysis_v2.json and results/error_examples_v2.md.
"""

import json
import re
import random
import string
from pathlib import Path

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
RESULTS_DIR = BASE / "results"
VECTOR_DIR = BASE / "vector_store"

RAG_V2_RESULTS = RESULTS_DIR / "rag_v2_test.jsonl"
COMPARISON_JSON = RESULTS_DIR / "comparison.json"

ERROR_ANALYSIS_V2_OUT = RESULTS_DIR / "error_analysis_v2.json"
ERROR_EXAMPLES_V2_OUT = RESULTS_DIR / "error_examples_v2.md"

FAISS_INDEX = VECTOR_DIR / "textbook_faiss.index"
METADATA_PARQUET = VECTOR_DIR / "textbook_metadata.parquet"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
SEED = 42

STOPWORDS = {
    "a","an","the","and","or","of","in","is","are","was","were","to","for",
    "with","at","by","from","this","that","these","those","it","its","be",
    "been","has","have","had","as","on","not","but","if","do","does","did",
    "so","can","which","who","what","how","when","where","than","then",
    "their","they","them","also","both","each","all","any","more","most",
    "other","into","after","before","up","out","no","about","some","would",
    "will","may","might","should","could","there","been","through","during",
    "over","under","while","within","between","against","without","such",
    "used","use","using","due","per","type","types","two","one","three",
    "four","five","six","seven","eight","nine","ten","s","t","d","re",
    "ve","ll","m","o",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def key_terms(text: str) -> list:
    tokens = normalize(text).split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ── Load v2 results ──────────────────────────────────────────
print("Loading rag_v2_test.jsonl …")
rag_v2_records = []
with open(RAG_V2_RESULTS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            rag_v2_records.append(json.loads(line))
print(f"  Loaded {len(rag_v2_records)} records")

# Inspect first record to find the correct answer field names
first = rag_v2_records[0]
print(f"  Fields: {list(first.keys())}")
print(f"  Sample correct_answer_letter: {first.get('correct_answer_letter','MISSING')}")
print(f"  Sample correct_answer_text:   {first.get('correct_answer_text','MISSING')}")
print(f"  Sample predicted_letter:      {first.get('predicted_letter','MISSING')}")
print(f"  Sample is_correct:            {first.get('is_correct','MISSING')}")

with open(COMPARISON_JSON, encoding="utf-8") as f:
    comparison = json.load(f)

# ── Load FAISS + embedder ────────────────────────────────────
print("Loading FAISS + metadata …")
index = faiss.read_index(str(FAISS_INDEX))
meta_df = pd.read_parquet(str(METADATA_PARQUET))
chunk_texts = meta_df["chunk_text"].tolist()
chunk_sources = meta_df["source_textbook"].tolist()
print(f"  {index.ntotal} vectors | {len(meta_df)} metadata rows")

print("Loading embedding model …")
embedder = SentenceTransformer(EMBED_MODEL_NAME)
print("  Ready.")


def retrieve(question: str, k: int = TOP_K):
    emb = embedder.encode([question], normalize_embeddings=True).astype("float32")
    scores, idxs = index.search(emb, k)
    texts = [chunk_texts[i] for i in idxs[0]]
    sources = [chunk_sources[i] for i in idxs[0]]
    return idxs[0].tolist(), scores[0].tolist(), texts, sources


# ── Hit@5 per question (for bucketing) ──────────────────────
print("\nComputing Hit@5 for all v2 records (re-running retrieval) …")
hit5_map = {}
for i, rec in enumerate(rag_v2_records):
    if i % 50 == 0:
        print(f"  {i}/{len(rag_v2_records)}")
    qid = rec["question_id"]
    question = rec["question_text"]
    ans_text = rec.get("correct_answer_text", "")
    terms = key_terms(ans_text)
    if not terms:
        hit5_map[qid] = 0
        continue
    _, _, texts, _ = retrieve(question, k=TOP_K)
    norm_texts = [normalize(t) for t in texts]
    hit = int(any(any(term in nt for term in terms) for nt in norm_texts))
    hit5_map[qid] = hit

# ── Bucket errors ────────────────────────────────────────────
print("\nBucketing errors …")
buckets = {
    "Parse failure": [],
    "Retrieval miss": [],
    "Model ignored context": [],
    "Other": [],
}

for rec in rag_v2_records:
    if rec.get("is_correct"):
        continue
    qid = rec["question_id"]
    predicted = rec.get("predicted_letter", "UNPARSED")
    hit5 = hit5_map[qid]

    if predicted == "UNPARSED":
        buckets["Parse failure"].append(rec)
    elif hit5 == 0:
        buckets["Retrieval miss"].append(rec)
    elif hit5 == 1:
        buckets["Model ignored context"].append(rec)
    else:
        buckets["Other"].append(rec)

bucket_counts = {k: len(v) for k, v in buckets.items()}
total_errors = sum(bucket_counts.values())

# ── Print results ────────────────────────────────────────────
print()
print("=" * 60)
print("PART C (v2) — Error Analysis on rag_v2_test.jsonl")
print("=" * 60)
print(f"\n  Total errors: {total_errors} / {len(rag_v2_records)}")
correct_count = len(rag_v2_records) - total_errors
print(f"  Correct:      {correct_count} / {len(rag_v2_records)}  ({100*correct_count/len(rag_v2_records):.2f}%)")
print()
print(f"  {'Bucket':<30} {'Count':>7} {'%':>8}")
print(f"  {'-'*47}")
for bucket, count in bucket_counts.items():
    pct = 100 * count / total_errors if total_errors else 0
    print(f"  {bucket:<30} {count:>7} {pct:>7.1f}%")

rag_sys = comparison["rag_system"]
base_sys = comparison["baseline_system"]
diff = comparison["difference_percentage_points"]
ct = comparison["contingency_table_2x2"]
print()
print("  --- Baseline comparison (from comparison.json, RAG v1 vs baseline) ---")
print(f"  RAG v1 accuracy:   {rag_sys['accuracy_percent']:.2f}%  (unparsed: {rag_sys['unparsed_percent']:.2f}%)")
print(f"  Baseline accuracy: {base_sys['accuracy_percent']:.2f}%  (unparsed: {base_sys['unparsed_percent']:.2f}%)")
print(f"  Difference (RAG v1 - baseline): {diff:+.2f} pp")

# ── Sample 10 errors ─────────────────────────────────────────
rng = random.Random(SEED)
all_errors = [(bname, rec) for bname, recs in buckets.items() for rec in recs]
sampled = rng.sample(all_errors, min(10, len(all_errors)))


def get_top2_snippets(question_text):
    _, _, texts, sources = retrieve(question_text, k=2)
    snippets = []
    for t, s in zip(texts, sources):
        snippet = t[:300].replace("\n", " ")
        snippets.append(f"[{s}] {snippet}…")
    return snippets


print("\nGenerating error_examples_v2.md …")
md_lines = [
    "# Error Examples — RAG v2 (10 sampled, seed=42)\n",
    f"Total errors: {total_errors} / {len(rag_v2_records)} questions\n",
    "\nBucket definitions:\n",
    "- **Parse failure**: model output could not be parsed to a letter\n",
    "- **Retrieval miss**: no top-5 chunk contained key terms from correct answer\n",
    "- **Model ignored context**: relevant chunk retrieved but wrong answer given\n",
    "- **Other**: correct answer had no extractable key terms; answer parseable\n",
    "\n---\n",
]

for i, (bucket_name, rec) in enumerate(sampled, 1):
    qid = rec["question_id"]
    question = rec["question_text"]
    options_str = " | ".join(f"({k}) {v}" for k, v in rec.get("options", {}).items())
    correct_letter = rec.get("correct_answer_letter", "?")
    correct_text = rec.get("correct_answer_text", "")
    predicted = rec.get("predicted_letter", "UNPARSED")
    gen_answer = rec.get("generated_answer", "")[:300]
    snippets = get_top2_snippets(question)

    md_lines += [
        f"\n## Error {i} — {bucket_name}\n\n",
        f"**Question ID**: `{qid}`\n\n",
        f"**Question**: {question}\n\n",
        f"**Options**: {options_str}\n\n",
        f"**Correct**: ({correct_letter}) {correct_text}\n\n",
        f"**Predicted**: {predicted}\n\n",
        "**Generated answer (first 300 chars)**:\n",
        f"> {gen_answer}…\n\n",
        "**Top-2 retrieved snippets**:\n",
    ]
    for j, snip in enumerate(snippets, 1):
        md_lines.append(f"{j}. {snip}\n")
    md_lines.append("\n---\n")

with open(ERROR_EXAMPLES_V2_OUT, "w", encoding="utf-8") as f:
    f.writelines(md_lines)

# ── Save JSON ────────────────────────────────────────────────
error_analysis_v2_output = {
    "configuration": "rag_v2",
    "results_file": str(RAG_V2_RESULTS),
    "total_questions": len(rag_v2_records),
    "total_correct": correct_count,
    "accuracy_percent": round(100 * correct_count / len(rag_v2_records), 2),
    "total_errors": total_errors,
    "bucket_counts": bucket_counts,
    "bucket_percentages_of_errors": {
        k: round(100 * v / total_errors, 2) if total_errors else 0.0
        for k, v in bucket_counts.items()
    },
    "baseline_comparison_v1": {
        "rag_v1_accuracy_percent": rag_sys["accuracy_percent"],
        "rag_v1_unparsed_percent": rag_sys["unparsed_percent"],
        "baseline_accuracy_percent": base_sys["accuracy_percent"],
        "baseline_unparsed_percent": base_sys["unparsed_percent"],
        "rag_v1_vs_baseline_diff_pp": diff,
        "contingency_2x2": ct,
    },
    "sample_seed": SEED,
    "num_sampled_error_examples": len(sampled),
    "error_examples_file": str(ERROR_EXAMPLES_V2_OUT),
}

with open(ERROR_ANALYSIS_V2_OUT, "w", encoding="utf-8") as f:
    json.dump(error_analysis_v2_output, f, indent=2, ensure_ascii=False)

print(f"\n  Saved → {ERROR_ANALYSIS_V2_OUT}")
print(f"  Saved → {ERROR_EXAMPLES_V2_OUT}")
print("\nDone.")
