"""
analyze_rag.py — Parts A, B, C analysis for the RAG pipeline.

Part A: Retrieval quality (Hit@k, Precision@k for k in {1,3,5})
         Keyword-matching proxy using correct answer text key terms.
Part B: Groundedness / source attribution (lexical-overlap proxy)
Part C: Error analysis (bucketing + 10 sampled examples)

Does NOT modify any existing result files.
Does NOT re-run LLM inference.
Re-runs FAISS retrieval (deterministic) to obtain chunk texts.
"""

import json
import re
import random
import textwrap
import string
from pathlib import Path

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
RESULTS_DIR = BASE / "results"
VECTOR_DIR = BASE / "vector_store"

RAG_RESULTS = RESULTS_DIR / "rag_full_results.jsonl"
BASELINE_RESULTS = RESULTS_DIR / "baseline_results.jsonl"
COMPARISON_JSON = RESULTS_DIR / "comparison.json"

RETRIEVAL_OUT = RESULTS_DIR / "retrieval_metrics.json"
GROUNDEDNESS_OUT = RESULTS_DIR / "groundedness.json"
ERROR_ANALYSIS_OUT = RESULTS_DIR / "error_analysis.json"
ERROR_EXAMPLES_OUT = RESULTS_DIR / "error_examples.md"

FAISS_INDEX = VECTOR_DIR / "textbook_faiss.index"
METADATA_PARQUET = VECTOR_DIR / "textbook_metadata.parquet"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
SEED = 42

# ─────────────────────────────────────────────────────────────
# Stop-words (common English + common medical connectors)
# ─────────────────────────────────────────────────────────────
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
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def key_terms(text: str) -> list[str]:
    """Extract non-stopword tokens from text after normalization."""
    tokens = normalize(text).split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ─────────────────────────────────────────────────────────────
# 1. Load existing results
# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading existing results …")

rag_records = []
with open(RAG_RESULTS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            rag_records.append(json.loads(line))

print(f"  RAG results loaded: {len(rag_records)} records")

with open(COMPARISON_JSON, encoding="utf-8") as f:
    comparison = json.load(f)

# ─────────────────────────────────────────────────────────────
# 2. Load FAISS + metadata + embedding model (for re-retrieval)
# ─────────────────────────────────────────────────────────────
print("Loading FAISS index and metadata …")
index = faiss.read_index(str(FAISS_INDEX))
meta_df = pd.read_parquet(str(METADATA_PARQUET))
# Build a list aligned with FAISS row order by chunk_id sort order in parquet
# The parquet rows ARE in FAISS insertion order (same script built both)
chunk_texts = meta_df["chunk_text"].tolist()          # list[str], len=36723
chunk_sources = meta_df["source_textbook"].tolist()   # list[str]
print(f"  FAISS index: {index.ntotal} vectors | metadata rows: {len(meta_df)}")

print("Loading embedding model …")
embedder = SentenceTransformer(EMBED_MODEL_NAME)
print("  Ready.")


def retrieve(question: str, k: int = TOP_K):
    """Return (indices, scores, texts, sources) for top-k chunks."""
    emb = embedder.encode([question], normalize_embeddings=True).astype("float32")
    scores, idxs = index.search(emb, k)
    scores = scores[0].tolist()
    idxs = idxs[0].tolist()
    texts = [chunk_texts[i] for i in idxs]
    sources = [chunk_sources[i] for i in idxs]
    return idxs, scores, texts, sources


# ─────────────────────────────────────────────────────────────
# Part A — Retrieval Quality (Hit@k, Precision@k)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART A — Retrieval Quality (keyword-match proxy)")
print("NOTE: 'Relevant' is defined as a retrieved chunk containing")
print("      key terms from the correct answer text (lowercase,")
print("      punctuation removed, stopwords excluded). This is a")
print("      keyword-matching PROXY — not human relevance judgment.")
print("=" * 60)

K_VALUES = [1, 3, 5]

part_a_rows = []

for rec in rag_records:
    qid = rec["question_id"]
    question = rec["question_text"]
    ans_text = rec.get("correct_answer_text", "")
    terms = key_terms(ans_text)

    _, _, texts, _ = retrieve(question, k=TOP_K)  # always retrieve top-5

    norm_texts = [normalize(t) for t in texts]

    row = {"question_id": qid, "correct_answer_text": ans_text, "key_terms": terms}
    for k in K_VALUES:
        top_k_texts = norm_texts[:k]
        hits = [
            any(term in t for term in terms)
            for t in top_k_texts
        ] if terms else []
        hit_k = int(any(hits)) if hits else 0
        prec_k = (sum(hits) / k) if hits else 0.0
        row[f"hit@{k}"] = hit_k
        row[f"prec@{k}"] = round(prec_k, 4)
    part_a_rows.append(row)

# Averages
averages = {}
for k in K_VALUES:
    avg_hit = sum(r[f"hit@{k}"] for r in part_a_rows) / len(part_a_rows)
    avg_prec = sum(r[f"prec@{k}"] for r in part_a_rows) / len(part_a_rows)
    averages[f"hit@{k}"] = round(avg_hit, 4)
    averages[f"precision@{k}"] = round(avg_prec, 4)

retrieval_output = {
    "description": (
        "Keyword-matching proxy. 'Relevant' = chunk contains key terms "
        "from correct answer text (lowercased, punctuation removed, "
        "stopwords excluded). NOT human relevance judgment."
    ),
    "num_questions": len(part_a_rows),
    "averages": averages,
    "per_question": part_a_rows,
}

with open(RETRIEVAL_OUT, "w", encoding="utf-8") as f:
    json.dump(retrieval_output, f, indent=2, ensure_ascii=False)

print(f"\n  Questions evaluated: {len(part_a_rows)}")
print(f"\n  {'Metric':<20} {'Value':>8}")
print(f"  {'-'*30}")
for k in K_VALUES:
    print(f"  {'Hit@'+str(k):<20} {averages['hit@'+str(k)]:>8.4f}")
    print(f"  {'Precision@'+str(k):<20} {averages['precision@'+str(k)]:>8.4f}")
print(f"\n  Saved → {RETRIEVAL_OUT}")


# ─────────────────────────────────────────────────────────────
# Part B — Groundedness / Source Attribution (lexical-overlap proxy)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART B — Groundedness (lexical-overlap proxy)")
print("NOTE: A sentence is 'grounded' if >= 50% of its non-stopword")
print("      content words appear in the concatenated top-5 retrieved")
print("      chunks. This is a lexical-overlap PROXY — not semantic")
print("      faithfulness or factual correctness.")
print("=" * 60)


def sentence_groundedness(sentence: str, context_norm: str) -> float:
    """Fraction of sentence content words found in context."""
    words = key_terms(sentence)
    if not words:
        return 1.0  # vacuously grounded (empty / all stopwords)
    found = sum(1 for w in words if w in context_norm)
    return found / len(words)


def split_sentences(text: str) -> list[str]:
    """Rough sentence splitter on . ! ?"""
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


part_b_rows = []
grounded_correct = []
grounded_incorrect = []

for rec in rag_records:
    qid = rec["question_id"]
    question = rec["question_text"]
    generated = rec.get("generated_answer", "")
    is_correct = rec.get("is_correct", False)
    predicted = rec.get("predicted_letter", "UNPARSED")

    _, _, texts, _ = retrieve(question, k=TOP_K)
    context_norm = " ".join(normalize(t) for t in texts)

    sentences = split_sentences(generated)
    if not sentences:
        per_answer_grounded = 0.0
        sent_scores = []
    else:
        sent_scores = [sentence_groundedness(s, context_norm) for s in sentences]
        grounded_flags = [sc >= 0.5 for sc in sent_scores]
        per_answer_grounded = sum(grounded_flags) / len(grounded_flags)

    row = {
        "question_id": qid,
        "is_correct": is_correct,
        "predicted_letter": predicted,
        "num_sentences": len(sentences),
        "grounded_fraction": round(per_answer_grounded, 4),
        "sentence_scores": [round(sc, 4) for sc in sent_scores],
    }
    part_b_rows.append(row)

    if predicted != "UNPARSED":
        if is_correct:
            grounded_correct.append(per_answer_grounded)
        else:
            grounded_incorrect.append(per_answer_grounded)

avg_grounded_all = sum(r["grounded_fraction"] for r in part_b_rows) / len(part_b_rows)
avg_grounded_correct = (sum(grounded_correct) / len(grounded_correct)) if grounded_correct else 0.0
avg_grounded_incorrect = (sum(grounded_incorrect) / len(grounded_incorrect)) if grounded_incorrect else 0.0

groundedness_output = {
    "description": (
        "Lexical-overlap proxy. A sentence is grounded if >= 50% of its "
        "non-stopword content words appear in the concatenated top-5 "
        "retrieved chunks. Per-answer groundedness = fraction of grounded "
        "sentences. NOT semantic faithfulness."
    ),
    "num_questions": len(part_b_rows),
    "avg_grounded_fraction_all": round(avg_grounded_all, 4),
    "avg_grounded_fraction_correct_answers": round(avg_grounded_correct, 4),
    "avg_grounded_fraction_incorrect_answers": round(avg_grounded_incorrect, 4),
    "num_parsed_correct": len(grounded_correct),
    "num_parsed_incorrect": len(grounded_incorrect),
    "per_question": part_b_rows,
}

with open(GROUNDEDNESS_OUT, "w", encoding="utf-8") as f:
    json.dump(groundedness_output, f, indent=2, ensure_ascii=False)

print(f"\n  Questions evaluated: {len(part_b_rows)}")
print(f"\n  {'Metric':<45} {'Value':>8}")
print(f"  {'-'*55}")
print(f"  {'Avg grounded fraction (all 300)':<45} {avg_grounded_all:>8.4f}")
print(f"  {'Avg grounded fraction (correct answers, n=' + str(len(grounded_correct)) + ')':<45} {avg_grounded_correct:>8.4f}")
print(f"  {'Avg grounded fraction (incorrect answers, n=' + str(len(grounded_incorrect)) + ')':<45} {avg_grounded_incorrect:>8.4f}")
print(f"\n  Saved → {GROUNDEDNESS_OUT}")


# ─────────────────────────────────────────────────────────────
# Part C — Error Analysis
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART C — Error Analysis")
print("=" * 60)

# Build a fast lookup: question_id → part_a terms + retrieved texts
retrieval_cache = {}  # question_id → list[str] (5 norm texts)
for rec, a_row in zip(rag_records, part_a_rows):
    retrieval_cache[rec["question_id"]] = {
        "terms": a_row["key_terms"],
        "hit5": a_row["hit@5"],
    }

# Bucket errors
buckets = {
    "Parse failure": [],
    "Retrieval miss": [],
    "Model ignored context": [],
    "Other": [],
}

for rec in rag_records:
    if rec.get("is_correct"):
        continue  # skip correct answers

    qid = rec["question_id"]
    predicted = rec.get("predicted_letter", "UNPARSED")
    cache = retrieval_cache[qid]
    terms = cache["terms"]
    hit5 = cache["hit5"]

    if predicted == "UNPARSED":
        buckets["Parse failure"].append(rec)
    elif hit5 == 0:
        # No relevant passage retrieved → retrieval miss
        buckets["Retrieval miss"].append(rec)
    elif hit5 == 1:
        # Relevant passage was retrieved but model still got it wrong
        buckets["Model ignored context"].append(rec)
    else:
        buckets["Other"].append(rec)

bucket_counts = {k: len(v) for k, v in buckets.items()}
total_errors = sum(bucket_counts.values())

print(f"\n  Total errors (incorrect or UNPARSED): {total_errors}")
print(f"\n  {'Bucket':<30} {'Count':>7} {'%':>8}")
print(f"  {'-'*47}")
for bucket, count in bucket_counts.items():
    pct = 100 * count / total_errors if total_errors else 0
    print(f"  {bucket:<30} {count:>7} {pct:>7.1f}%")

# Baseline comparison from comparison.json
print(f"\n  --- Baseline comparison (from comparison.json) ---")
rag_sys = comparison["rag_system"]
base_sys = comparison["baseline_system"]
diff = comparison["difference_percentage_points"]
ct = comparison["contingency_table_2x2"]
print(f"  RAG accuracy:      {rag_sys['accuracy_percent']:.2f}%  (unparsed: {rag_sys['unparsed_percent']:.2f}%)")
print(f"  Baseline accuracy: {base_sys['accuracy_percent']:.2f}%  (unparsed: {base_sys['unparsed_percent']:.2f}%)")
print(f"  Difference (RAG - baseline): {diff:+.2f} pp")
print(f"  Both correct:        {ct['both_correct']}")
print(f"  Only RAG correct:    {ct['only_rag_correct']}")
print(f"  Only Baseline corr:  {ct['only_baseline_correct']}")
print(f"  Both wrong:          {ct['both_wrong']}")

# Sample 10 errors for examples
rng = random.Random(SEED)
all_errors = []
for bucket_name, recs in buckets.items():
    for rec in recs:
        all_errors.append((bucket_name, rec))

sampled = rng.sample(all_errors, min(10, len(all_errors)))

# Retrieve chunk snippets for sampled errors
def get_top2_snippets(question_text: str) -> list[str]:
    _, _, texts, sources = retrieve(question_text, k=2)
    snippets = []
    for t, s in zip(texts, sources):
        snippet = t[:300].replace("\n", " ")
        snippets.append(f"[{s}] {snippet}…")
    return snippets


md_lines = [
    "# Error Examples (10 sampled, seed=42)\n",
    f"Total errors: {total_errors} / 300 questions\n",
    "Bucket definitions:\n",
    "- **Parse failure**: model output could not be parsed to a letter\n",
    "- **Retrieval miss**: no top-5 chunk contained key terms from correct answer\n",
    "- **Model ignored context**: relevant chunk retrieved but wrong answer given\n",
    "- **Other**: answer was parseable, relevant chunk retrieved but still wrong; "
    "or correct answer had no extractable key terms\n",
    "\n---\n",
]

for i, (bucket_name, rec) in enumerate(sampled, 1):
    qid = rec["question_id"]
    question = rec["question_text"]
    options_str = " | ".join(
        f"({k}) {v}" for k, v in rec.get("options", {}).items()
    )
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

with open(ERROR_EXAMPLES_OUT, "w", encoding="utf-8") as f:
    f.writelines(md_lines)

# Save error_analysis.json
error_analysis_output = {
    "total_questions": len(rag_records),
    "total_errors": total_errors,
    "total_correct": len(rag_records) - total_errors,
    "bucket_counts": bucket_counts,
    "bucket_percentages_of_errors": {
        k: round(100 * v / total_errors, 2) if total_errors else 0.0
        for k, v in bucket_counts.items()
    },
    "baseline_comparison": {
        "rag_accuracy_percent": rag_sys["accuracy_percent"],
        "rag_unparsed_percent": rag_sys["unparsed_percent"],
        "baseline_accuracy_percent": base_sys["accuracy_percent"],
        "baseline_unparsed_percent": base_sys["unparsed_percent"],
        "difference_pp": diff,
        "contingency_2x2": ct,
    },
    "sample_seed": SEED,
    "num_sampled_error_examples": len(sampled),
    "error_examples_file": str(ERROR_EXAMPLES_OUT),
}

with open(ERROR_ANALYSIS_OUT, "w", encoding="utf-8") as f:
    json.dump(error_analysis_output, f, indent=2, ensure_ascii=False)

print(f"\n  Saved → {ERROR_ANALYSIS_OUT}")
print(f"  Saved → {ERROR_EXAMPLES_OUT}")

# ─────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ANALYSIS COMPLETE — Output files:")
print(f"  {RETRIEVAL_OUT}")
print(f"  {GROUNDEDNESS_OUT}")
print(f"  {ERROR_ANALYSIS_OUT}")
print(f"  {ERROR_EXAMPLES_OUT}")
print("=" * 60)
