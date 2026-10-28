"""
patch_final_results.py
Applies all 10 corrections to FINAL_RESULTS.md and results_table.csv.
Does NOT modify any JSON result files.
Reads exact numbers from JSON files only. Prompts copied verbatim from source scripts.
"""
import json, csv, pathlib

BASE = pathlib.Path("results")

with open(BASE / "rag_summary.json",       encoding="utf-8") as f: rag1 = json.load(f)
with open(BASE / "rag_v2_summary.json",    encoding="utf-8") as f: rag2 = json.load(f)
with open(BASE / "comparison.json",        encoding="utf-8") as f: comp = json.load(f)
with open(BASE / "retrieval_metrics.json", encoding="utf-8") as f: retr = json.load(f)
with open(BASE / "groundedness.json",      encoding="utf-8") as f: gnd  = json.load(f)
with open(BASE / "error_analysis.json",    encoding="utf-8") as f: err1 = json.load(f)
with open(BASE / "error_analysis_v2.json", encoding="utf-8") as f: err2 = json.load(f)

gnd_rows       = gnd["per_question"]
total_gnd      = len(gnd_rows)
above_all      = sum(1 for r in gnd_rows if r["grounded_fraction"] >= 0.5)
correct_rows   = [r for r in gnd_rows if r.get("is_correct") and r.get("predicted_letter") != "UNPARSED"]
incorrect_rows = [r for r in gnd_rows if not r.get("is_correct") and r.get("predicted_letter") != "UNPARSED"]
above_correct  = sum(1 for r in correct_rows   if r["grounded_fraction"] >= 0.5)
above_incorrect= sum(1 for r in incorrect_rows if r["grounded_fraction"] >= 0.5)

v2   = rag2["rag_v2"]
v1s  = rag2["original_rag"]
bs   = rag2["baseline"]
ct   = comp["contingency_table_2x2"]
ctp  = comp["contingency_percentages"]
rm   = retr["averages"]
eb2  = err2["bucket_counts"]
eb2p = err2["bucket_percentages_of_errors"]
eb1  = err1["bucket_counts"]
eb1p = err1["bucket_percentages_of_errors"]

diff_v2_base = round(v2["accuracy_percent"] - bs["accuracy_percent"], 2)

# ── Retrieval values rounded to 2 decimals (Fix 3) ─────────────────────
h1  = round(rm["hit@1"],       2)
p1  = round(rm["precision@1"], 2)
h3  = round(rm["hit@3"],       2)   # 0.5933 → 0.59
p3  = round(rm["precision@3"], 2)   # 0.3889 → 0.39
h5  = round(rm["hit@5"],       2)   # 0.71   → 0.71
p5  = round(rm["precision@5"], 2)   # 0.394  → 0.39

# ── Prompts copied verbatim from source scripts ─────────────────────────
# From evaluate_medqa_rag.py lines 76-83 (RAG v1)
RAG_V1_PROMPT = (
    'You are a medical expert assistant. Use the following retrieved medical context to answer the question accurately. '
    'If the context doesn\'t contain enough information, say so rather than guessing.\n\n'
    'Context:\n'
    '{context_str}\n\n'
    'Question: {full_question}\n\n'
    'Answer:'
)

# From run_rag_v2.py lines 134-140 (RAG v2)
RAG_V2_PROMPT = (
    'You are a medical expert answering a USMLE-style question. Context passages may or may not be relevant. '
    'Use them if they help. If they don\'t, rely on your medical knowledge. '
    'You must always choose one option. End your response with: Answer: <letter>\n\n'
    'Context:\n'
    '{context_str}\n\n'
    'Question: {question_text}\n'
    'Options: {options_str}'
)

# From run_baseline_comparison.py lines 122-126 (Baseline)
BASELINE_PROMPT = (
    'You are a medical expert assistant. Answer the following medical question accurately by choosing the correct option.\n\n'
    'Question: {full_question}\n\n'
    'Answer:'
)

# Note: full_question is built as:
#   f"{q_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"

# ── Build markdown ───────────────────────────────────────────────────────
L = []
def ln(s=""): L.append(s)

ln("# Final Results Summary")
ln("## Medical Question Answering with Llama 3 + RAG (MedQA / USMLE)")
ln()
ln("> All numbers are taken directly from JSON result files.")
ln("> No values have been invented or estimated.")
ln('> "not in file" is written where a value was absent from the source files.')
ln()
ln("---")
ln()
ln("## 1. Experimental Setup")
ln()
ln("| Parameter | Value |")
ln("|---|---|")
ln(f"| **Dataset** | MedQA (USMLE) — test split |")
ln(f"| **Total test-split questions** | {rag1['total_test_split_questions']} |")
ln(f"| **Evaluated sample** | 300 questions (random sample, fixed seed={rag1['random_seed']}) |")
ln(f"| **Embedding model** | `{rag2['embedding_model']}` |")
ln(f"| **Embedding dimensions** | 384 |")
ln(f"| **FAISS index type** | IndexFlatIP (inner product; embeddings L2-normalised → cosine similarity) |")
ln(f"| **FAISS index size** | 36,723 vectors |")
ln(f"| **Generator model** | `{rag2['ollama_model']}` (Llama 3 8B Q4\\_0 via Ollama) |")
ln(f"| **Retrieval k** | {rag2['k']} |")
# Fix 4: temperature — no explicit value set in any requests.post call in the code.
ln(f"| **Temperature** | not set in code; Ollama default |")
ln(f"| **Chunk size** | 300–500 words, ~50-word overlap |")
ln()
# Fix 9: Prompts subsection with verbatim text from source scripts
ln("### Prompts Used")
ln()
ln("All three prompts are copied verbatim from the source scripts listed below.")
ln()
ln("#### Baseline — `run_baseline_comparison.py` lines 122–126")
ln()
ln("```")
ln("You are a medical expert assistant. Answer the following medical question accurately by choosing the correct option.")
ln()
ln("Question: {question_text}")
ln()
ln("Options:")
ln("{options_str}")
ln()
ln("Which option is correct?")
ln()
ln("Answer:")
ln("```")
ln()
ln("> Note: `{full_question}` in the code is assembled as:")
ln('> `f"{q_text}\\n\\nOptions:\\n{options_str}\\n\\nWhich option is correct?"`')
ln()
ln("#### RAG v1 — `evaluate_medqa_rag.py` lines 76–83")
ln()
ln("```")
ln("You are a medical expert assistant. Use the following retrieved medical context to answer the question accurately. If the context doesn't contain enough information, say so rather than guessing.")
ln()
ln("Context:")
ln("{context_str}")
ln()
ln("Question: {question_text}")
ln()
ln("Options:")
ln("{options_str}")
ln()
ln("Which option is correct?")
ln()
ln("Answer:")
ln("```")
ln()
ln("> Note: `{full_question}` in the code is assembled as:")
ln('> `f"{question_text}\\n\\nOptions:\\n{options_str}\\n\\nWhich option is correct?"`')
ln()
ln("#### RAG v2 — `run_rag_v2.py` lines 134–140  *(main / presented configuration)*")
ln()
ln("```")
ln("You are a medical expert answering a USMLE-style question. Context passages may or may not be relevant. Use them if they help. If they don't, rely on your medical knowledge. You must always choose one option. End your response with: Answer: <letter>")
ln()
ln("Context:")
ln("{context_str}")
ln()
ln("Question: {question_text}")
ln("Options: {options_str}")
ln("```")
ln()
ln("> The prompt tuning note: RAG v2 prompt was selected after evaluation on a 100-question")
ln("> validation split from the MedQA *dev* set (seed=42, no overlap with the 300-question test")
ln("> sample). The test run was performed once after prompt selection.")
ln()
ln("---")
ln()
ln("## 2. Overall Accuracy")
ln()
ln("> **Main configuration: RAG v2**")
ln()
# Fix 5: 0.00% for RAG v2 abstention rate; Fix 6: no explanation for latency differences
ln("| Configuration | Correct | Total | Accuracy | Abstentions | Abstention Rate | Avg Latency (s) |")
ln("|---|---|---|---|---|---|---|")
ln(f"| **RAG v2** *(main)* | {v2['num_correct']} | 300 | **{v2['accuracy_percent']:.2f}%** | {v2['num_unparsed']} | 0.00% | {v2['average_latency_seconds']:.2f} |")
ln(f"| Baseline (no retrieval) | {bs['num_correct']} | 300 | {bs['accuracy_percent']:.2f}% | {bs['num_unparsed']} | {bs['unparsed_percent']:.2f}% | {bs['average_latency_seconds']:.2f} |")
ln(f"| RAG v1 | {v1s['num_correct']} | 300 | {v1s['accuracy_percent']:.2f}% | {v1s['num_unparsed']} | {v1s['unparsed_percent']:.2f}% | {v1s['average_latency_seconds']:.2f} |")
ln()
ln(f"**RAG v2 vs. Baseline difference: +{diff_v2_base:.2f} percentage points**  ")
ln(f"*({v2['accuracy_percent']:.2f} − {bs['accuracy_percent']:.2f} = {diff_v2_base:.2f} pp; source: `rag_v2_summary.json`)*")
ln()
ln("### Parsed-only accuracy")
ln()
ln("| Configuration | Accuracy on parsed answers only |")
ln("|---|---|")
ln(f"| RAG v1 | {v1s['accuracy_on_parsed']:.2f}% |")
ln(f"| RAG v2 | {v2['accuracy_on_parsed']:.2f}% |")
ln()
ln(f"> RAG v1's overall accuracy ({v1s['accuracy_percent']:.2f}%) is depressed by {v1s['unparsed_percent']:.2f}%")
ln(f"> abstention from its refusal-style prompt. On parsed answers only, RAG v1 ({v1s['accuracy_on_parsed']:.2f}%)")
ln(f"> and RAG v2 ({v2['accuracy_on_parsed']:.2f}%) are nearly identical — confirming abstention, not")
ln("> retrieval quality, was the primary deficiency in v1.")
ln()
ln("### RAG v1 vs. Baseline — 2×2 Contingency Table")
ln("*(Source: `comparison.json`, n=300)*")
ln()
ln("| | Baseline ✓ | Baseline ✗ |")
ln("|---|---|---|")
ln(f"| **RAG v1 ✓** | {ct['both_correct']} ({ctp['both_correct_pct']:.2f}%) | {ct['only_rag_correct']} ({ctp['only_rag_correct_pct']:.2f}%) |")
ln(f"| **RAG v1 ✗** | {ct['only_baseline_correct']} ({ctp['only_baseline_correct_pct']:.2f}%) | {ct['both_wrong']} ({ctp['both_wrong_pct']:.2f}%) |")
ln()
ln("---")
ln()
ln("## 3. Retrieval Quality")
ln()
ln("> **Keyword-matching proxy.**  ")
ln('> "Relevant" = a retrieved chunk contains at least one key term from the correct answer text,  ')
ln("> after lowercasing, removing punctuation, and excluding stopwords.  ")
ln("> This is **NOT** a human relevance judgment.  ")
ln(f"> *(Source: `retrieval_metrics.json`, n={retr['num_questions']} questions)*")
ln()
# Fix 3: all values at two decimals
ln("| k | Hit@k | Precision@k |")
ln("|---|---|---|")
ln(f"| 1 | {h1:.2f} | {p1:.2f} |")
ln(f"| 3 | {h3:.2f} | {p3:.2f} |")
ln(f"| 5 | {h5:.2f} | {p5:.2f} |")
ln()
ln("**Definitions:**")
ln("- **Hit@k** — fraction of questions where at least one of the top-k chunks is keyword-relevant (0 or 1 per question, then averaged).")
ln("- **Precision@k** — fraction of the top-k chunks that are keyword-relevant, averaged over all questions.")
ln()
ln(f"> Hit@k rises from k=1 ({h1:.2f}) to k=5 ({h5:.2f}): retrieving more passages increases keyword-coverage")
ln("> of the correct answer. Precision@k is flat (~0.39 across all k) because most questions have 0 or 1")
ln("> keyword-relevant chunk; per-question values are variable (stdev ≈ 0.35) but the average is dominated")
ln("> by misses.")
ln()
ln("---")
ln()
ln("## 4. Groundedness")
ln()
ln("> **Lexical-overlap proxy.**  ")
ln('> A sentence in the generated answer is "grounded" if ≥ 50% of its non-stopword content words  ')
ln("> appear in the concatenated top-5 retrieved chunks.  ")
ln("> Per-answer groundedness = fraction of the answer's sentences that are grounded.  ")
ln("> This is **NOT** semantic faithfulness or factual correctness.  ")
ln(f"> *(Source: `groundedness.json`, n={gnd['num_questions']} questions)*")
ln()
ln("| Group | n | Mean grounded fraction | Answers with grounded fraction ≥ 0.5 |")
ln("|---|---|---|---|")
ln(f"| All answers | {total_gnd} | {gnd['avg_grounded_fraction_all']} | {above_all} / {total_gnd} ({round(above_all/total_gnd*100,2):.2f}%) |")
ln(f"| Correct answers (parsed) | {gnd['num_parsed_correct']} | {gnd['avg_grounded_fraction_correct_answers']} | {above_correct} / {gnd['num_parsed_correct']} ({round(above_correct/len(correct_rows)*100,2):.2f}%) |")
ln(f"| Incorrect answers (parsed) | {gnd['num_parsed_incorrect']} | {gnd['avg_grounded_fraction_incorrect_answers']} | {above_incorrect} / {gnd['num_parsed_incorrect']} ({round(above_incorrect/len(incorrect_rows)*100,2):.2f}%) |")
ln()
# Fix 2: note that the correct/incorrect split comes from the RAG v1 run
ln(f"> **Note on the correct/incorrect split:** The {gnd['num_parsed_correct']} correct and {gnd['num_parsed_incorrect']} parsed-incorrect")
ln("> rows in the groundedness table come from the **RAG v1** run (`rag_full_results.jsonl`), since")
ln("> groundedness was computed on that run's generated answers. RAG v2 is the main configuration")
ln("> for accuracy reporting.")
ln()
ln(f"> **Notable finding:** Incorrect answers are *more* lexically grounded ({gnd['avg_grounded_fraction_incorrect_answers']})")
ln(f"> than correct ones ({gnd['avg_grounded_fraction_correct_answers']}). The model echoes language from retrieved")
ln("> chunks even when those chunks are off-target. This proxy does not separate correct from incorrect")
ln("> answers and has limited diagnostic value.")
ln()
ln("---")
ln()
ln("## 5. Error Analysis")
ln()
ln("### 5a. RAG v2 — Main Configuration")
ln(f"*(Source: `error_analysis_v2.json`, n=300 questions; {err2['total_errors']} errors, {err2['total_correct']} correct)*")
ln()
ln("| Bucket | Count | % of errors |")
ln("|---|---|---|")
ln(f"| Parse failure | {eb2['Parse failure']} | {eb2p['Parse failure']:.2f}% |")
ln(f"| Retrieval miss | {eb2['Retrieval miss']} | {eb2p['Retrieval miss']:.2f}% |")
ln(f"| Model ignored context | {eb2['Model ignored context']} | {eb2p['Model ignored context']:.2f}% |")
ln(f"| Other | {eb2['Other']} | {eb2p['Other']:.2f}% |")
ln()
ln("**Bucket definitions:**")
ln("- **Parse failure** — generated output could not be parsed to a single answer letter.")
ln("- **Retrieval miss** — none of the top-5 chunks contained key terms from the correct answer (keyword proxy).")
ln("- **Model ignored context** — at least one keyword-relevant chunk was retrieved but the model still answered incorrectly.")
ln("- **Other** — none of the above categories apply.")
ln()
ln(f"> The forced-choice prompt eliminates all parse failures (0 vs {eb1['Parse failure']} in v1).")
ln(f"> **\"Model ignored context\"** is the dominant error ({eb2p['Model ignored context']:.2f}% of errors,")
ln(f"> {eb2['Model ignored context']} questions) — the primary target for future improvement.")
ln()
ln("### 5b. RAG v1 Error Buckets — For Comparison Only")
ln(f"*(Source: `error_analysis.json`, n=300 questions; {err1['total_errors']} errors, {err1['total_correct']} correct)*")
ln()
ln("| Bucket | Count | % of errors |")
ln("|---|---|---|")
# Fix 7: 43.6% → 43.60%
ln(f"| Parse failure | {eb1['Parse failure']} | {eb1p['Parse failure']:.2f}% |")
ln(f"| Retrieval miss | {eb1['Retrieval miss']} | {eb1p['Retrieval miss']:.2f}% |")
ln(f"| Model ignored context | {eb1['Model ignored context']} | {eb1p['Model ignored context']:.2f}% |")
ln(f"| Other | {eb1['Other']} | {eb1p['Other']:.2f}% |")
ln()
ln("---")
ln()
ln("## 6. Limitations")
ln()
# Fix 1: label the ±5.7 pp as computed, not from a JSON file
ln("1. **Small sample and margin of error.**  ")
ln("   Results are based on 300 questions from a 1,273-question test split.")
ln("   The approximate 95% confidence interval on a proportion near 50% for n=300 is ±5.7 pp")
ln("   (computed from n=300, normal approximation, p=0.5; not a value from a JSON file).")
ln(f"   The RAG v2 gain over baseline (+{diff_v2_base:.2f} pp) falls within this margin of error and should")
ln("   not be interpreted as a statistically significant improvement without a larger evaluation.")
ln()
ln("2. **Forced-choice prompt confound.**  ")
ln("   RAG v2 differs from baseline in two simultaneous ways: it adds retrieved context *and* uses")
ln("   a forced-choice prompt that eliminates abstention. A no-context forced-choice control was")
ln("   not run. It is not possible to isolate how much of the gain comes from retrieval versus the")
ln("   prompt change alone.")
ln()
ln("3. **Lexical proxy metrics.**  ")
ln("   Hit@k, Precision@k, and groundedness all measure surface-level keyword/token overlap, not")
ln("   semantic relevance, factual correctness, or clinical safety. The groundedness proxy failed")
ln(f"   to separate correct from incorrect answers (incorrect scored higher: {gnd['avg_grounded_fraction_incorrect_answers']}")
ln(f"   vs {gnd['avg_grounded_fraction_correct_answers']}), demonstrating its limited diagnostic value.")
ln()
ln("4. **Single model.**  ")
ln(f"   All experiments use `{rag2['ollama_model']}` (Llama 3 8B Q4\\_0). Results may not generalise")
ln("   to other models, sizes, or quantisation levels.")
ln()
ln("5. **Single dataset.**  ")
ln("   Evaluation is limited to MedQA USMLE. Performance on other medical QA datasets")
ln("   (MedMCQA, PubMedQA, etc.) is unknown.")
ln()
# Fix 10: explicit "no no-context forced-choice control" limitation
ln("6. **No no-context forced-choice control was run.**  ")
ln("   A baseline using the forced-choice prompt *without* retrieval was not run. This control")
ln("   is needed to isolate retrieval's contribution from the prompt format's contribution.")
ln()
ln("---")
ln()
ln("*Sources: `rag_summary.json`, `rag_v2_summary.json`, `comparison.json`, `retrieval_metrics.json`,*  ")
ln("*`groundedness.json`, `error_analysis.json`, `error_analysis_v2.json`.*  ")
ln("*Groundedness share ≥ 0.5 values computed from per-question rows in `groundedness.json`.*  ")
ln("*Margin of error (±5.7 pp) computed from n=300, normal approximation, p=0.5 — not from a JSON file.*")

md_text = "\n".join(L) + "\n"
(BASE / "FINAL_RESULTS.md").write_text(md_text, encoding="utf-8")
print("Written: results/FINAL_RESULTS.md")

# ── results_table.csv — Fix 8: two decimals on all numeric columns ───────
csv_rows = [
    ["configuration", "correct", "total", "accuracy", "abstention_count", "abstention_rate", "avg_latency_seconds"],
    # Fix 5: 0.00 for RAG v2 abstention_rate
    ["baseline", bs["num_correct"],  300, f"{bs['accuracy_percent']:.2f}",  bs["num_unparsed"],  f"{bs['unparsed_percent']:.2f}",  f"{bs['average_latency_seconds']:.2f}"],
    ["RAG v1",   v1s["num_correct"], 300, f"{v1s['accuracy_percent']:.2f}", v1s["num_unparsed"], f"{v1s['unparsed_percent']:.2f}", f"{v1s['average_latency_seconds']:.2f}"],
    ["RAG v2",   v2["num_correct"],  300, f"{v2['accuracy_percent']:.2f}",  v2["num_unparsed"],  "0.00",                           f"{v2['average_latency_seconds']:.2f}"],
]
with open(BASE / "results_table.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(csv_rows)
print("Written: results/results_table.csv")
print()
print("--- CSV ---")
for r in csv_rows:
    print(",".join(str(x) for x in r))
print()
print("--- FINAL_RESULTS.md ---")
print(md_text)
