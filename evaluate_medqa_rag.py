import os
import sys
import json
import time
import argparse
import re
from datetime import datetime
import pandas as pd
import numpy as np
import faiss
import requests
from sentence_transformers import SentenceTransformer

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_faiss.index")
METADATA_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_metadata.parquet")
DEFAULT_DATA_FILE = os.path.join(PROCESSED_DIR, "medqa_questions.parquet")
DEFAULT_RESULTS_FILE = os.path.join(RESULTS_DIR, "rag_full_results.jsonl")
DEFAULT_SUMMARY_FILE = os.path.join(RESULTS_DIR, "rag_summary.json")

# Models
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_retrieval_system():
    print("Loading embedding model and FAISS vector index...")
    t0 = time.time()
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    index = faiss.read_index(INDEX_FILE)
    df_meta = pd.read_parquet(METADATA_FILE)
    print(f"Retrieval system loaded in {time.time() - t0:.2f}s ({index.ntotal:,} vectors in index).\n")
    return embedder, index, df_meta


def retrieve(query, embedder, index, df_meta, top_k=5):
    """Retrieves top_k relevant textbook chunks for a query."""
    vec = embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, indices = index.search(vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(df_meta):
            continue
        row = df_meta.iloc[idx]
        results.append({
            "book": row.get("source_textbook", ""),
            "chunk_id": row.get("chunk_id", ""),
            "text": row.get("chunk_text", ""),
            "score": float(score)
        })
    return results


def answer_question(question_text, options, embedder, index, df_meta, top_k=5):
    """
    Phase 4 answer_question function:
    1. Formats question with options
    2. Retrieves top_k textbook context chunks
    3. Builds prompt and calls Llama 3 via Ollama
    4. Measures latency and returns full result dictionary
    """
    options_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
    full_question = f"{question_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"

    t_start = time.time()
    chunks = retrieve(full_question, embedder, index, df_meta, top_k=top_k)
    t_retrieval = time.time() - t_start

    context_str = "\n\n".join([f"Source: {c['book']}\nText: {c['text']}" for c in chunks])
    prompt = f"""You are a medical expert assistant. Use the following retrieved medical context to answer the question accurately. If the context doesn't contain enough information, say so rather than guessing.

Context:
{context_str}

Question: {full_question}

Answer:"""

    t_gen_start = time.time()
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        generated_answer = response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        generated_answer = "ERROR_CONNECTION: Could not connect to Ollama service at localhost:11434"
    except Exception as e:
        generated_answer = f"ERROR: {str(e)}"
    
    t_total = time.time() - t_start

    return {
        "full_question": full_question,
        "generated_answer": generated_answer,
        "retrieved_sources": [c["book"] for c in chunks],
        "retrieval_scores": [c["score"] for c in chunks],
        "latency_seconds": round(t_total, 3),
        "retrieval_latency_seconds": round(t_retrieval, 3)
    }


def extract_predicted_letter(generated_text, valid_options):
    """
    Strict extraction rule for the predicted answer letter.
    Looks for explicit answer declarations first, then parenthesized or standalone letters.
    Never guesses; returns 'UNPARSED' if no valid letter is determined.
    """
    if not generated_text or not isinstance(generated_text, str):
        return "UNPARSED"

    if generated_text.startswith("ERROR"):
        return "UNPARSED"

    valid_set = set(k.upper() for k in valid_options.keys()) if valid_options else {"A", "B", "C", "D", "E"}
    options_regex = "".join(sorted(valid_set))

    # Priority 1: Explicit answer statements
    patterns_p1 = [
        rf"(?:the\s+)?(?:correct\s+)?answer\s*(?:is|:)\s*:?\s*\(?([{options_regex}])\)?(?=[\s:.)\],]|$)",
        rf"(?:^|\n)\s*Answer\s*:\s*\(?([{options_regex}])\)?(?=[\s:.)\],]|$)",
        rf"I\s+would\s+answer\s*:\s*\(?([{options_regex}])\)?(?=[\s:.)\],]|$)",
        rf"(?:the\s+)?best\s+(?:treatment|answer|choice|option|next\s+step)\s+is\s*:?\s*\(?([{options_regex}])\)?(?=[\s:.)\],]|$)",
    ]
    for pat in patterns_p1:
        match = re.search(pat, generated_text, re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
            if letter in valid_set:
                return letter

    # Priority 2: Standalone option/choice declaration at start of line or bullet
    patterns_p2 = [
        rf"(?:^|\n)\s*(?:[-*•]\s*)?([{options_regex}])\s*:\s+",
        rf"(?:^|\n)\s*Option\s+([{options_regex}])\s*[:\b]",
        rf"(?:^|\s)\(([{options_regex}])\)(?=[\s:.,]|$)",
        rf"(?:^|\s)Option\s+([{options_regex}])\b",
    ]
    for pat in patterns_p2:
        match = re.search(pat, generated_text, re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
            if letter in valid_set:
                return letter

    # Priority 3: Standalone single letter on its own line
    match_standalone = re.search(rf"(?:^|\n)\s*([{options_regex}])\s*$", generated_text)
    if match_standalone:
        letter = match_standalone.group(1).upper()
        if letter in valid_set:
            return letter

    return "UNPARSED"


def load_existing_results(results_file):
    """Loads existing results from jsonl to support resume capability."""
    completed = {}
    if os.path.exists(results_file):
        with open(results_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    q_id = data.get("question_id")
                    if q_id:
                        completed[q_id] = data
                except json.JSONDecodeError:
                    print(f"Warning: Corrupted line {line_no} in {results_file}, skipping.")
    return completed


def compute_metrics(results_list):
    """Computes evaluation statistics from a list of result dictionaries."""
    total = len(results_list)
    if total == 0:
        return {
            "total_questions": 0,
            "num_correct": 0,
            "accuracy_percent": 0.0,
            "num_unparsed": 0,
            "unparsed_percent": 0.0,
            "accuracy_on_parsed": 0.0,
            "average_latency_seconds": 0.0
        }

    num_correct = sum(1 for r in results_list if r.get("predicted_letter") == r.get("correct_answer_letter"))
    num_unparsed = sum(1 for r in results_list if r.get("predicted_letter") == "UNPARSED")
    latencies = [r.get("latency_seconds", 0.0) for r in results_list if r.get("latency_seconds") is not None]
    avg_latency = float(np.mean(latencies)) if latencies else 0.0

    acc = (num_correct / total) * 100.0
    unparsed_pct = (num_unparsed / total) * 100.0
    parsed_total = total - num_unparsed
    acc_on_parsed = (num_correct / parsed_total * 100.0) if parsed_total > 0 else 0.0

    return {
        "total_questions": total,
        "num_correct": num_correct,
        "accuracy_percent": round(acc, 2),
        "num_unparsed": num_unparsed,
        "unparsed_percent": round(unparsed_pct, 2),
        "accuracy_on_parsed": round(acc_on_parsed, 2),
        "average_latency_seconds": round(avg_latency, 2)
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline on MedQA test split")
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE, help="Path to medqa_questions.parquet")
    parser.add_argument("--results-file", default=DEFAULT_RESULTS_FILE, help="Output JSONL results file")
    parser.add_argument("--summary-file", default=DEFAULT_SUMMARY_FILE, help="Output JSON summary file")
    parser.add_argument("--sample", type=int, default=None, help="Number of questions to sample (None for all)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling (default: 42)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve per question")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.results_file), exist_ok=True)
    os.makedirs(os.path.dirname(args.summary_file), exist_ok=True)

    print("=" * 70)
    print("      MEDQA TEST SPLIT FULL RAG EVALUATION (LLAMA 3 + FAISS)       ")
    print("=" * 70)

    # 1. Load MedQA Test Split
    print(f"\n[Step 1] Loading MedQA test split from {args.data_file}...")
    if not os.path.exists(args.data_file):
        print(f"ERROR: Dataset file not found at {args.data_file}")
        sys.exit(1)

    df_questions = pd.read_parquet(args.data_file)
    df_test = df_questions[df_questions["split"] == "test"].copy()
    total_test_questions = len(df_test)
    print(f"Total questions in MedQA test split: {total_test_questions:,}")

    # Apply sampling if specified
    if args.sample is not None and args.sample < total_test_questions:
        print(f"Sampling {args.sample} questions with random seed {args.seed}...")
        df_eval = df_test.sample(n=args.sample, random_state=args.seed).copy()
    else:
        df_eval = df_test

    eval_count = len(df_eval)
    print(f"Questions selected for evaluation in this run: {eval_count:,}")

    # 2. Check for resumability
    existing_results = load_existing_results(args.results_file)
    print(f"Found {len(existing_results):,} already completed evaluations in {args.results_file}.")

    # Load Retrieval System
    embedder, index, df_meta = load_retrieval_system()

    # Open results file in append mode
    records_written = list(existing_results.values())
    skipped_count = 0
    newly_processed = 0

    print("=" * 70)
    print("Starting evaluation loop...")
    print("=" * 70)

    loop_start_time = time.time()
    with open(args.results_file, "a", encoding="utf-8") as out_f:
        for idx, (_, row) in enumerate(df_eval.iterrows(), 1):
            q_id = row["id"]
            if q_id in existing_results:
                skipped_count += 1
                continue

            q_text = row["question"]
            options = row["options"]
            # Options may be dict or JSON string
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except Exception:
                    options = {}

            correct_letter = row.get("answer_idx", "")
            correct_text = row.get("correct_answer", "")

            # If answer_idx is missing, deduce from correct_answer matching option values
            if not correct_letter and correct_text and options:
                for k, v in options.items():
                    if v.strip() == correct_text.strip():
                        correct_letter = k
                        break

            # Execute RAG pipeline
            res = answer_question(
                question_text=q_text,
                options=options,
                embedder=embedder,
                index=index,
                df_meta=df_meta,
                top_k=args.top_k
            )

            predicted_letter = extract_predicted_letter(res["generated_answer"], options)
            is_correct = (predicted_letter == correct_letter)

            record = {
                "question_id": q_id,
                "question_text": q_text,
                "options": options,
                "correct_answer_letter": correct_letter,
                "correct_answer_text": correct_text,
                "generated_answer": res["generated_answer"],
                "predicted_letter": predicted_letter,
                "is_correct": is_correct,
                "retrieved_sources": res["retrieved_sources"],
                "retrieval_scores": res["retrieval_scores"],
                "latency_seconds": res["latency_seconds"],
                "timestamp": datetime.now().isoformat()
            }

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            records_written.append(record)
            newly_processed += 1

            # Compute running stats and ETA
            running_correct = sum(1 for r in records_written if r.get("is_correct"))
            running_acc = (running_correct / len(records_written)) * 100.0
            elapsed = time.time() - loop_start_time
            avg_per_q = elapsed / newly_processed if newly_processed > 0 else 0
            remaining_q = eval_count - len(records_written)
            eta_secs = int(remaining_q * avg_per_q)
            eta_min, eta_sec = divmod(eta_secs, 60)
            eta_hr, eta_min = divmod(eta_min, 60)
            eta_str = f"{eta_hr}h {eta_min:02d}m" if eta_hr > 0 else f"{eta_min}m {eta_sec:02d}s"

            print(
                f"[{len(records_written)}/{eval_count}] "
                f"({len(records_written)/eval_count*100:.1f}%) {q_id} | "
                f"Pred: {predicted_letter} | Correct: {correct_letter} | "
                f"Match: {is_correct} | Time: {res['latency_seconds']:.2f}s | "
                f"Acc: {running_acc:.1f}% ({running_correct}/{len(records_written)}) | "
                f"ETA: {eta_str}"
            )

    print("\n" + "=" * 70)
    print("                     EVALUATION SUMMARY REPORT                      ")
    print("=" * 70)

    # Filter records to only those in df_eval for final metrics
    target_ids = set(df_eval["id"].tolist())
    final_records = [r for r in records_written if r["question_id"] in target_ids]

    metrics = compute_metrics(final_records)

    print(f"Total Questions Evaluated : {metrics['total_questions']:,}")
    print(f"Number Correct            : {metrics['num_correct']:,}")
    print(f"Accuracy                  : {metrics['accuracy_percent']:.2f}%")
    print(f"Number Unparsed           : {metrics['num_unparsed']:,} ({metrics['unparsed_percent']:.2f}%)")
    print(f"Accuracy on Parsed        : {metrics['accuracy_on_parsed']:.2f}%")
    print(f"Average Latency           : {metrics['average_latency_seconds']:.2f}s / question")
    print("=" * 70)

    # Build summary dict
    summary_data = {
        "dataset": "MedQA (USMLE)",
        "split": "test",
        "total_test_split_questions": total_test_questions,
        "evaluated_questions": metrics["total_questions"],
        "num_correct": metrics["num_correct"],
        "accuracy_percent": metrics["accuracy_percent"],
        "num_unparsed": metrics["num_unparsed"],
        "unparsed_percent": metrics["unparsed_percent"],
        "accuracy_on_parsed": metrics["accuracy_on_parsed"],
        "average_latency_seconds": metrics["average_latency_seconds"],
        "ollama_model": OLLAMA_MODEL,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "sampling_used": (args.sample is not None),
        "sample_size": args.sample,
        "random_seed": args.seed if args.sample is not None else None,
        "results_file": args.results_file,
        "timestamp": datetime.now().isoformat()
    }

    with open(args.summary_file, "w", encoding="utf-8") as sum_f:
        json.dump(summary_data, sum_f, indent=2, ensure_ascii=False)

    print(f"Summary successfully saved to: {args.summary_file}")
    print(f"Full results saved to: {args.results_file}")


if __name__ == "__main__":
    main()
