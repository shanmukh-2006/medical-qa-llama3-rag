# Final Results Summary
## Medical Question Answering with Llama 3 + RAG (MedQA / USMLE)

> All numbers are taken directly from JSON result files.
> No values have been invented or estimated.
> "not in file" is written where a value was absent from the source files.

---

## 1. Experimental Setup

| Parameter | Value |
|---|---|
| **Dataset** | MedQA (USMLE) — test split |
| **Total test-split questions** | 1273 |
| **Evaluated sample** | 300 questions (random sample, fixed seed=42) |
| **Embedding model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Embedding dimensions** | 384 |
| **FAISS index type** | IndexFlatIP (inner product; embeddings L2-normalised → cosine similarity) |
| **FAISS index size** | 36,723 vectors |
| **Generator model** | `llama3:latest` (Llama 3 8B Q4\_0 via Ollama) |
| **Retrieval k** | 5 |
| **Temperature** | not set in code; Ollama default |
| **Chunk size** | 300–500 words, ~50-word overlap |

### Prompts Used

All three prompts are copied verbatim from the source scripts listed below.

#### Baseline — `run_baseline_comparison.py` lines 122–126

```
You are a medical expert assistant. Answer the following medical question accurately by choosing the correct option.

Question: {question_text}

Options:
{options_str}

Which option is correct?

Answer:
```

> Note: `{full_question}` in the code is assembled as:
> `f"{q_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"`

#### RAG v1 — `evaluate_medqa_rag.py` lines 76–83

```
You are a medical expert assistant. Use the following retrieved medical context to answer the question accurately. If the context doesn't contain enough information, say so rather than guessing.

Context:
{context_str}

Question: {question_text}

Options:
{options_str}

Which option is correct?

Answer:
```

> Note: `{full_question}` in the code is assembled as:
> `f"{question_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"`

#### RAG v2 — `run_rag_v2.py` lines 134–140  *(main / presented configuration)*

```
You are a medical expert answering a USMLE-style question. Context passages may or may not be relevant. Use them if they help. If they don't, rely on your medical knowledge. You must always choose one option. End your response with: Answer: <letter>

Context:
{context_str}

Question: {question_text}
Options: {options_str}
```

> The prompt tuning note: RAG v2 prompt was selected after evaluation on a 100-question
> validation split from the MedQA *dev* set (seed=42, no overlap with the 300-question test
> sample). The test run was performed once after prompt selection.

---

## 2. Overall Accuracy

> **Main configuration: RAG v2**

| Configuration | Correct | Total | Accuracy | Abstentions | Abstention Rate | Avg Latency (s) |
|---|---|---|---|---|---|---|
| **RAG v2** *(main)* | 156 | 300 | **52.00%** | 0 | 0.00% | 5.76 |
| Baseline (no retrieval) | 146 | 300 | 48.67% | 2 | 0.67% | 10.89 |
| RAG v1 | 128 | 300 | 42.67% | 61 | 20.33% | 17.42 |

**RAG v2 vs. Baseline difference: +3.33 percentage points**  
*(52.00 − 48.67 = 3.33 pp; source: `rag_v2_summary.json`)*

### Parsed-only accuracy

| Configuration | Accuracy on parsed answers only |
|---|---|
| RAG v1 | 53.56% |
| RAG v2 | 52.00% |

> RAG v1's overall accuracy (42.67%) is depressed by 20.33%
> abstention from its refusal-style prompt. On parsed answers only, RAG v1 (53.56%)
> and RAG v2 (52.00%) are nearly identical — confirming abstention, not
> retrieval quality, was the primary deficiency in v1.

### RAG v1 vs. Baseline — 2×2 Contingency Table
*(Source: `comparison.json`, n=300)*

| | Baseline ✓ | Baseline ✗ |
|---|---|---|
| **RAG v1 ✓** | 95 (31.67%) | 33 (11.00%) |
| **RAG v1 ✗** | 51 (17.00%) | 121 (40.33%) |

---

## 3. Retrieval Quality

> **Keyword-matching proxy.**  
> "Relevant" = a retrieved chunk contains at least one key term from the correct answer text,  
> after lowercasing, removing punctuation, and excluding stopwords.  
> This is **NOT** a human relevance judgment.  
> *(Source: `retrieval_metrics.json`, n=300 questions)*

| k | Hit@k | Precision@k |
|---|---|---|
| 1 | 0.39 | 0.39 |
| 3 | 0.59 | 0.39 |
| 5 | 0.71 | 0.39 |

**Definitions:**
- **Hit@k** — fraction of questions where at least one of the top-k chunks is keyword-relevant (0 or 1 per question, then averaged).
- **Precision@k** — fraction of the top-k chunks that are keyword-relevant, averaged over all questions.

> Hit@k rises from k=1 (0.39) to k=5 (0.71): retrieving more passages increases keyword-coverage
> of the correct answer. Precision@k is flat (~0.39 across all k) because most questions have 0 or 1
> keyword-relevant chunk; per-question values are variable (stdev ≈ 0.35) but the average is dominated
> by misses.

---

## 4. Groundedness

> **Lexical-overlap proxy.**  
> A sentence in the generated answer is "grounded" if ≥ 50% of its non-stopword content words  
> appear in the concatenated top-5 retrieved chunks.  
> Per-answer groundedness = fraction of the answer's sentences that are grounded.  
> This is **NOT** semantic faithfulness or factual correctness.  
> *(Source: `groundedness.json`, n=300 questions)*

| Group | n | Mean grounded fraction | Answers with grounded fraction ≥ 0.5 |
|---|---|---|---|
| All answers | 300 | 0.6436 | 221 / 300 (73.67%) |
| Correct answers (parsed) | 128 | 0.6705 | 97 / 128 (75.78%) |
| Incorrect answers (parsed) | 111 | 0.7155 | 93 / 111 (83.78%) |

> **Note on the correct/incorrect split:** The 128 correct and 111 parsed-incorrect
> rows in the groundedness table come from the **RAG v1** run (`rag_full_results.jsonl`), since
> groundedness was computed on that run's generated answers. RAG v2 is the main configuration
> for accuracy reporting.

> **Notable finding:** Incorrect answers are *more* lexically grounded (0.7155)
> than correct ones (0.6705). The model echoes language from retrieved
> chunks even when those chunks are off-target. This proxy does not separate correct from incorrect
> answers and has limited diagnostic value.

---

## 5. Error Analysis

### 5a. RAG v2 — Main Configuration
*(Source: `error_analysis_v2.json`, n=300 questions; 144 errors, 156 correct)*

| Bucket | Count | % of errors |
|---|---|---|
| Parse failure | 0 | 0.00% |
| Retrieval miss | 49 | 34.03% |
| Model ignored context | 95 | 65.97% |
| Other | 0 | 0.00% |

**Bucket definitions:**
- **Parse failure** — generated output could not be parsed to a single answer letter.
- **Retrieval miss** — none of the top-5 chunks contained key terms from the correct answer (keyword proxy).
- **Model ignored context** — at least one keyword-relevant chunk was retrieved but the model still answered incorrectly.
- **Other** — none of the above categories apply.

> The forced-choice prompt eliminates all parse failures (0 vs 61 in v1).
> **"Model ignored context"** is the dominant error (65.97% of errors,
> 95 questions) — the primary target for future improvement.

### 5b. RAG v1 Error Buckets — For Comparison Only
*(Source: `error_analysis.json`, n=300 questions; 172 errors, 128 correct)*

| Bucket | Count | % of errors |
|---|---|---|
| Parse failure | 61 | 35.47% |
| Retrieval miss | 36 | 20.93% |
| Model ignored context | 75 | 43.60% |
| Other | 0 | 0.00% |

---

## 6. Limitations

1. **Small sample and margin of error.**  
   Results are based on 300 questions from a 1,273-question test split.
   The approximate 95% confidence interval on a proportion near 50% for n=300 is ±5.7 pp
   (computed from n=300, normal approximation, p=0.5; not a value from a JSON file).
   The RAG v2 gain over baseline (+3.33 pp) falls within this margin of error and should
   not be interpreted as a statistically significant improvement without a larger evaluation.

2. **Forced-choice prompt confound.**  
   RAG v2 differs from baseline in two simultaneous ways: it adds retrieved context *and* uses
   a forced-choice prompt that eliminates abstention. A no-context forced-choice control was
   not run. It is not possible to isolate how much of the gain comes from retrieval versus the
   prompt change alone.

3. **Lexical proxy metrics.**  
   Hit@k, Precision@k, and groundedness all measure surface-level keyword/token overlap, not
   semantic relevance, factual correctness, or clinical safety. The groundedness proxy failed
   to separate correct from incorrect answers (incorrect scored higher: 0.7155
   vs 0.6705), demonstrating its limited diagnostic value.

4. **Single model.**  
   All experiments use `llama3:latest` (Llama 3 8B Q4\_0). Results may not generalise
   to other models, sizes, or quantisation levels.

5. **Single dataset.**  
   Evaluation is limited to MedQA USMLE. Performance on other medical QA datasets
   (MedMCQA, PubMedQA, etc.) is unknown.

6. **No no-context forced-choice control was run.**  
   A baseline using the forced-choice prompt *without* retrieval was not run. This control
   is needed to isolate retrieval's contribution from the prompt format's contribution.

---

*Sources: `rag_summary.json`, `rag_v2_summary.json`, `comparison.json`, `retrieval_metrics.json`,*  
*`groundedness.json`, `error_analysis.json`, `error_analysis_v2.json`.*  
*Groundedness share ≥ 0.5 values computed from per-question rows in `groundedness.json`.*  
*Margin of error (±5.7 pp) computed from n=300, normal approximation, p=0.5 — not from a JSON file.*
