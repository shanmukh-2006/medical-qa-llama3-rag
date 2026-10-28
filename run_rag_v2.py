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
SPLIT_DIR = os.path.join(RESULTS_DIR, "split")
VAL_DIR = os.path.join(RESULTS_DIR, "validation")

INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_faiss.index")
METADATA_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_metadata.parquet")
DATA_FILE = os.path.join(PROCESSED_DIR, "medqa_questions.parquet")
RAG_ORIGINAL_RESULTS_FILE = os.path.join(RESULTS_DIR, "rag_full_results.jsonl")
RAG_ORIGINAL_SUMMARY_FILE = os.path.join(RESULTS_DIR, "rag_summary.json")
BASELINE_COMPARISON_FILE = os.path.join(RESULTS_DIR, "comparison.json")

VAL_IDS_FILE = os.path.join(SPLIT_DIR, "validation_ids.json")
VAL_RESULTS_FILE = os.path.join(VAL_DIR, "rag_v2_val.jsonl")
TEST_RESULTS_FILE = os.path.join(RESULTS_DIR, "rag_v2_test.jsonl")
V2_SUMMARY_FILE = os.path.join(RESULTS_DIR, "rag_v2_summary.json")

# Model Config
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5


def load_retrieval_system():
    print("Loading embedding model and FAISS vector index...")
    t0 = time.time()
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    index = faiss.read_index(INDEX_FILE)
    df_meta = pd.read_parquet(METADATA_FILE)
    print(f"Retrieval system loaded in {time.time() - t0:.2f}s ({index.ntotal:,} vectors in index).\n")
    return embedder, index, df_meta


def retrieve(query, embedder, index, df_meta, top_k=5):
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


def extract_predicted_letter(generated_text, valid_options):
    """
    Exact same strict extraction rule as original RAG and baseline.
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


def answer_question_v2(question_text, options, embedder, index, df_meta, top_k=5):
    """
    RAG v2 prompt:
    Uses retrieved context if helpful, falls back to medical knowledge if not,
    always commits to one option, and ends with: Answer: <letter>.
    """
    options_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
    query_str = f"{question_text}\n\nOptions:\n{options_str}"

    t_start = time.time()
    chunks = retrieve(query_str, embedder, index, df_meta, top_k=top_k)
    t_retrieval = time.time() - t_start

    context_str = "\n\n".join([f"Source: {c['book']}\nText: {c['text']}" for c in chunks])

    prompt = f"""You are a medical expert answering a USMLE-style question. Context passages may or may not be relevant. Use them if they help. If they don't, rely on your medical knowledge. You must always choose one option. End your response with: Answer: <letter>

Context:
{context_str}

Question: {question_text}
Options: {options_str}"""

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
    except Exception as e:
        generated_answer = f"ERROR: {str(e)}"

    t_total = time.time() - t_start

    return {
        "prompt": prompt,
        "generated_answer": generated_answer,
        "retrieved_sources": [c["book"] for c in chunks],
        "retrieval_scores": [c["score"] for c in chunks],
        "latency_seconds": round(t_total, 3),
        "retrieval_latency_seconds": round(t_retrieval, 3)
    }


def load_jsonl(filepath):
    records = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
    return records


def run_evaluation(target_questions, output_file, mode_name):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    existing_results = {r["question_id"]: r for r in load_jsonl(output_file)}
    print(f"[{mode_name.upper()}] Total target questions: {len(target_questions)}")
    print(f"[{mode_name.upper()}] Found {len(existing_results)} already completed evaluations in {output_file}.")

    embedder, index, df_meta = load_retrieval_system()

    loop_start_time = time.time()
    newly_processed = 0

    with open(output_file, "a", encoding="utf-8") as out_f:
        for idx, q_item in enumerate(target_questions, 1):
            q_id = q_item["id"]
            if q_id in existing_results:
                continue

            q_text = q_item["question"]
            options = q_item["options"]
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except Exception:
                    options = {}

            correct_letter = q_item.get("answer_idx", "")
            correct_text = q_item.get("correct_answer", "")

            if not correct_letter and correct_text and options:
                for k, v in options.items():
                    if v.strip() == correct_text.strip():
                        correct_letter = k
                        break

            res = answer_question_v2(
                question_text=q_text,
                options=options,
                embedder=embedder,
                index=index,
                df_meta=df_meta,
                top_k=TOP_K
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

            existing_results[q_id] = record
            newly_processed += 1

            current_count = len(existing_results)
            running_correct = sum(1 for r in existing_results.values() if r.get("is_correct"))
            running_acc = (running_correct / current_count) * 100.0

            elapsed = time.time() - loop_start_time
            avg_per_q = elapsed / newly_processed if newly_processed > 0 else 0
            remaining_q = len(target_questions) - current_count
            eta_secs = int(remaining_q * avg_per_q)
            eta_min, eta_sec = divmod(eta_secs, 60)
            eta_hr, eta_min = divmod(eta_min, 60)
            eta_str = f"{eta_hr}h {eta_min:02d}m" if eta_hr > 0 else f"{eta_min}m {eta_sec:02d}s"

            print(
                f"[{current_count}/{len(target_questions)}] "
                f"({current_count/len(target_questions)*100:.1f}%) {q_id} | "
                f"Pred: {predicted_letter} | Correct: {correct_letter} | "
                f"Match: {is_correct} | Time: {res['latency_seconds']:.2f}s | "
                f"Acc: {running_acc:.1f}% ({running_correct}/{current_count}) | "
                f"ETA: {eta_str}"
            )

    all_results = list(existing_results.values())
    total = len(all_results)
    num_correct = sum(1 for r in all_results if r.get("is_correct"))
    num_unparsed = sum(1 for r in all_results if r.get("predicted_letter") == "UNPARSED")
    latencies = [r.get("latency_seconds", 0.0) for r in all_results if r.get("latency_seconds")]
    avg_latency = float(np.mean(latencies)) if latencies else 0.0

    acc = (num_correct / total) * 100.0 if total > 0 else 0.0
    parsed_count = total - num_unparsed
    acc_on_parsed = (num_correct / parsed_count) * 100.0 if parsed_count > 0 else 0.0

    print("\n" + "=" * 70)
    print(f"            {mode_name.upper()} RUN COMPLETED RESULTS            ")
    print("=" * 70)
    print(f"Total Questions Evaluated : {total}")
    print(f"Number Correct            : {num_correct}")
    print(f"Overall Accuracy          : {acc:.2f}%")
    print(f"UNPARSED / Abstentions    : {num_unparsed} ({(num_unparsed/total)*100:.2f}%)")
    print(f"Accuracy on Parsed        : {acc_on_parsed:.2f}%")
    print(f"Average Latency           : {avg_latency:.2f}s / question")
    print("=" * 70)

    return {
        "total_questions": total,
        "num_correct": num_correct,
        "accuracy_percent": round(acc, 2),
        "num_unparsed": num_unparsed,
        "unparsed_percent": round((num_unparsed / total) * 100.0, 2),
        "accuracy_on_parsed": round(acc_on_parsed, 2),
        "average_latency_seconds": round(avg_latency, 2)
    }


def main():
    parser = argparse.ArgumentParser(description="RAG v2 Evaluation Pipeline")
    parser.add_argument("--step", choices=["val", "test", "summary"], required=True,
                        help="val: Step 2 validation run; test: Step 3 test run; summary: Step 4 export")
    args = parser.parse_args()

    # Load Questions Dataset
    df_questions = pd.read_parquet(DATA_FILE)

    if args.step == "val":
        print("\n=== STEP 2: RAG v2 Validation Run (100 Dev Questions) ===")
        with open(VAL_IDS_FILE, "r", encoding="utf-8") as f:
            val_info = json.load(f)
        val_ids = val_info["validation_ids"]

        # Ensure order matches validation_ids.json
        q_map = {row["id"]: row.to_dict() for _, row in df_questions[df_questions["id"].isin(val_ids)].iterrows()}
        target_questions = [q_map[qid] for qid in val_ids if qid in q_map]

        run_evaluation(target_questions, VAL_RESULTS_FILE, mode_name="Validation (RAG v2)")

    elif args.step == "test":
        print("\n=== STEP 3: RAG v2 Test Run (Exact 300 Test Questions) ===")
        # Read exact order from rag_full_results.jsonl
        test_records = load_jsonl(RAG_ORIGINAL_RESULTS_FILE)
        test_ids = [r["question_id"] for r in test_records]

        q_map = {row["id"]: row.to_dict() for _, row in df_questions[df_questions["id"].isin(test_ids)].iterrows()}
        target_questions = [q_map[qid] for qid in test_ids if qid in q_map]

        run_evaluation(target_questions, TEST_RESULTS_FILE, mode_name="Test (RAG v2)")

    elif args.step == "summary":
        print("\n=== STEP 4: Compiling RAG v2 Summary vs Original RAG vs Baseline ===")
        # Load all 3 files
        with open(RAG_ORIGINAL_SUMMARY_FILE, "r", encoding="utf-8") as f:
            orig_rag = json.load(f)

        with open(BASELINE_COMPARISON_FILE, "r", encoding="utf-8") as f:
            comp_data = json.load(f)

        v2_test_records = load_jsonl(TEST_RESULTS_FILE)
        total_v2 = len(v2_test_records)
        correct_v2 = sum(1 for r in v2_test_records if r.get("is_correct"))
        unparsed_v2 = sum(1 for r in v2_test_records if r.get("predicted_letter") == "UNPARSED")
        latencies_v2 = [r.get("latency_seconds", 0.0) for r in v2_test_records if r.get("latency_seconds")]
        avg_lat_v2 = float(np.mean(latencies_v2)) if latencies_v2 else 0.0
        acc_v2 = (correct_v2 / total_v2) * 100.0 if total_v2 > 0 else 0.0
        parsed_v2 = total_v2 - unparsed_v2
        acc_on_parsed_v2 = (correct_v2 / parsed_v2) * 100.0 if parsed_v2 > 0 else 0.0

        summary = {
            "dataset": "MedQA (USMLE)",
            "test_questions_count": total_v2,
            "ollama_model": OLLAMA_MODEL,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "k": TOP_K,
            "temperature": "default (Ollama default: 0.8 / identical to original runs)",
            "rag_v2": {
                "num_correct": correct_v2,
                "accuracy_percent": round(acc_v2, 2),
                "num_unparsed": unparsed_v2,
                "unparsed_percent": round((unparsed_v2 / total_v2) * 100.0, 2),
                "accuracy_on_parsed": round(acc_on_parsed_v2, 2),
                "average_latency_seconds": round(avg_lat_v2, 2)
            },
            "original_rag": {
                "num_correct": orig_rag.get("num_correct"),
                "accuracy_percent": orig_rag.get("accuracy_percent"),
                "num_unparsed": orig_rag.get("num_unparsed"),
                "unparsed_percent": orig_rag.get("unparsed_percent"),
                "accuracy_on_parsed": orig_rag.get("accuracy_on_parsed"),
                "average_latency_seconds": orig_rag.get("average_latency_seconds")
            },
            "baseline": {
                "num_correct": comp_data["baseline_system"]["num_correct"],
                "accuracy_percent": comp_data["baseline_system"]["accuracy_percent"],
                "num_unparsed": comp_data["baseline_system"]["num_unparsed"],
                "unparsed_percent": comp_data["baseline_system"]["unparsed_percent"],
                "average_latency_seconds": comp_data["baseline_system"]["average_latency_seconds"]
            },
            "timestamp": datetime.now().isoformat()
        }

        with open(V2_SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"Summary successfully written to: {V2_SUMMARY_FILE}")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
