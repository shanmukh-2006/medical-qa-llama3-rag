# Medical Question Answering using Llama 3 & RAG

A local Retrieval-Augmented Generation (RAG) system for answering USMLE-style medical examination questions from the **MedQA** dataset. The system indexes medical textbooks using dense embeddings and FAISS vector search, retrieving relevant passages to augment generation with **Llama 3** running locally via Ollama.

---

## 1. Project Overview

- **Dataset**: MedQA (USMLE 4-option multiple-choice questions) — evaluated on a 300-question sample with fixed seed (`seed=42`).
- **Knowledge Base**: 18 medical textbooks chunked into 36,723 passages (300–500 words, ~50-word overlap).
- **Embeddings & Vector Index**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim), indexed via FAISS `IndexFlatIP` (cosine similarity with L2 normalization).
- **LLM Generator**: `llama3:latest` (Llama 3 8B Q4_0) served locally via Ollama (`http://localhost:11434`).
- **Evaluated Configurations**:
  - **Baseline**: Llama 3 zero-shot without retrieval (48.67% accuracy).
  - **RAG v1**: Top-5 retrieval with standard refusal-style prompt (42.67% accuracy, 20.33% unparsed abstentions).
  - **RAG v2 (Presented Main Model)**: Top-5 retrieval with forced-choice prompt (**52.00% accuracy**, 0.00% abstentions, +3.33 pp gain over baseline).

---

## 2. Repository Structure

```
Medical Question Answering/
├── data/                                 # Raw MedQA dataset and medical textbooks (gitignored)
│   └── data_clean/questions/US/          # MedQA train/dev/test jsonl splits
├── processed_data/                       # Parsed parquet files
│   ├── medqa_questions.parquet           # Parsed MedQA questions (12,723 questions)
│   └── textbook_chunks.parquet           # Chunked textbook passages (36,723 passages)
├── vector_store/                         # FAISS index and metadata (gitignored)
│   ├── textbook_faiss.index              # FAISS IndexFlatIP (36,723 vectors x 384-dim)
│   └── textbook_metadata.parquet         # Passage text and source metadata
├── results/                              # Evaluation outputs and metrics
│   ├── results_table.csv                 # Core comparison table (Baseline, RAG v1, RAG v2)
│   ├── FINAL_RESULTS.md                  # Comprehensive results report
│   ├── rag_summary.json                  # RAG v1 metrics summary
│   ├── rag_v2_summary.json               # RAG v2 metrics summary
│   ├── comparison.json                   # Side-by-side RAG v1 vs. baseline contingency table
│   ├── retrieval_metrics.json            # Hit@k and Precision@k (k=1, 3, 5)
│   ├── groundedness.json                 # Groundedness lexical-overlap proxy
│   ├── error_analysis.json               # RAG v1 error breakdown
│   ├── error_analysis_v2.json            # RAG v2 error breakdown
│   └── figures/                          # Publication-ready plots (PNG 300 DPI & PDF)
│       ├── accuracy_bar_chart.png
│       └── error_buckets_stacked_bar.png
├── prepare_dataset.py                    # Phase 1: parse MedQA & chunk textbooks
├── build_retrieval_system.py             # Phase 2: compute embeddings & build FAISS index
├── run_rag_pipeline.py                   # Phase 3/4: RAG question-answering CLI
├── evaluate_medqa_rag.py                 # Evaluates RAG v1 on 300 MedQA test questions
├── run_baseline_comparison.py            # Evaluates Baseline (no retrieval)
├── run_rag_v2.py                         # Tunes on validation and evaluates RAG v2
├── analyze_rag.py                        # Computes retrieval, groundedness, & RAG v1 error analysis
├── error_analysis_v2.py                  # Computes RAG v2 error analysis
├── generate_charts.py                    # Generates matplotlib bar and stacked bar figures
├── requirements.txt                      # Python dependencies
└── README.md                             # Project documentation
```

---

## 3. Prerequisites & Installation

### 3.1 Python Environment
Requires Python 3.10+ (tested on Windows & Linux):
```bash
python -m pip install -r requirements.txt
```

### 3.2 Ollama & Llama 3
Install and start [Ollama](https://ollama.com/), then pull the Llama 3 model:
```bash
ollama pull llama3:latest
```
Ensure the Ollama local daemon is running at `http://localhost:11434`.

---

## 4. Obtaining the Data

1. **MedQA (USMLE) Dataset**:
   - Download the official English MedQA dataset from the [MedQA GitHub Repository](https://github.com/jind11/MedQA).
   - Place the jsonl files into `data/data_clean/questions/US/` (`train.jsonl`, `dev.jsonl`, `test.jsonl`).

2. **Medical Textbooks**:
   - The knowledge base uses the 18 standard medical textbooks designated by MedQA (covering Internal Medicine, Surgery, Pediatrics, Pharmacology, Pathology, etc.).
   - Place textbook `.txt` files into `data/textbooks/`.

---

## 5. Execution Pipeline (Order of Running Scripts)

Follow this order to reproduce the entire pipeline from scratch:

### Step 1 — Parse Dataset & Chunk Textbooks
```bash
python prepare_dataset.py
```
*Outputs:* `processed_data/medqa_questions.parquet` and `processed_data/textbook_chunks.parquet`.

### Step 2 — Build Vector Store & FAISS Index
```bash
python build_retrieval_system.py
```
*Outputs:* `vector_store/textbook_faiss.index` and `vector_store/textbook_metadata.parquet`.

### Step 3 — Interactive Query Demonstration
Test retrieval and generation with a sample question:
```bash
python ask.py "What is the first-line treatment for acute otitis media in pediatric patients?"
```

### Step 4 — Run Full Evaluations (300-Question Test Set)
1. **Evaluate RAG v1 (refusal prompt)**:
   ```bash
   python evaluate_medqa_rag.py
   ```
   *Outputs:* `results/rag_full_results.jsonl` and `results/rag_summary.json`.

2. **Evaluate Baseline (no retrieval)**:
   ```bash
   python run_baseline_comparison.py
   ```
   *Outputs:* `results/baseline_results.jsonl` and `results/comparison.json`.

3. **Validate & Evaluate RAG v2 (forced-choice prompt)**:
   ```bash
   # Validation run on 100 dev questions
   python run_rag_v2.py --step val

   # Final test run on the 300 test questions
   python run_rag_v2.py --step test

   # Compile summary
   python run_rag_v2.py --step summary
   ```
   *Outputs:* `results/rag_v2_test.jsonl` and `results/rag_v2_summary.json`.

### Step 5 — Run Metrics & Error Analysis
1. **Analyze Retrieval Quality, Groundedness, & RAG v1 Errors**:
   ```bash
   python analyze_rag.py
   ```
   *Outputs:* `results/retrieval_metrics.json`, `results/groundedness.json`, `results/error_analysis.json`.

2. **Analyze RAG v2 Errors**:
   ```bash
   python error_analysis_v2.py
   ```
   *Outputs:* `results/error_analysis_v2.json`.

### Step 6 — Generate Visualizations
```bash
python generate_charts.py
```
*Outputs:* `results/figures/accuracy_bar_chart.png` (and `.pdf`), `results/figures/error_buckets_stacked_bar.png` (and `.pdf`).

---

## 6. Summary of Key Results

| Configuration | Accuracy | Abstention Count | Abstention Rate | Avg Latency |
|---|---|---|---|---|
| **RAG v2** *(main)* | **52.00%** | 0 | 0.00% | 5.76 s |
| Baseline (no retrieval) | 48.67% | 2 | 0.67% | 10.89 s |
| RAG v1 | 42.67% | 61 | 20.33% | 17.42 s |

- **RAG v2 vs. Baseline**: **+3.33 pp** gain in accuracy with 0 abstentions.
- **Retrieval Performance (keyword proxy)**: Hit@1 = 0.39, Hit@3 = 0.59, Hit@5 = 0.71.
- Detailed metrics, methodology, and limitations are documented in [`results/FINAL_RESULTS.md`](results/FINAL_RESULTS.md).
