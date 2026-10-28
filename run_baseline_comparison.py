import os
import sys
import json
import time
import re
from datetime import datetime
import numpy as np
import requests

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RAG_RESULTS_FILE = os.path.join(RESULTS_DIR, "rag_full_results.jsonl")
BASELINE_RESULTS_FILE = os.path.join(RESULTS_DIR, "baseline_results.jsonl")
COMPARISON_FILE = os.path.join(RESULTS_DIR, "comparison.json")

# Ollama Config (Identical to RAG run)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"


def extract_predicted_letter(generated_text, valid_options):
    """
    Exact same strict extraction rule as in evaluate_medqa_rag.py.
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


def run_baseline_evaluation():
    print("=" * 70)
    print("      MEDQA NO-RETRIEVAL BASELINE (CONTROL EVALUATION)       ")
    print("=" * 70)

    # 1. Load exact same question set and ordering as RAG run
    if not os.path.exists(RAG_RESULTS_FILE):
        print(f"ERROR: RAG results file not found at {RAG_RESULTS_FILE}")
        sys.exit(1)

    rag_records = load_jsonl(RAG_RESULTS_FILE)
    total_questions = len(rag_records)
    print(f"Loaded {total_questions} questions from {RAG_RESULTS_FILE} in exact order.\n")

    # 2. Check for existing baseline results (resumable)
    existing_baseline = {r["question_id"]: r for r in load_jsonl(BASELINE_RESULTS_FILE)}
    print(f"Found {len(existing_baseline)} existing results in {BASELINE_RESULTS_FILE}.")

    loop_start_time = time.time()
    newly_processed = 0

    with open(BASELINE_RESULTS_FILE, "a", encoding="utf-8") as out_f:
        for idx, rag_q in enumerate(rag_records, 1):
            q_id = rag_q["question_id"]
            if q_id in existing_baseline:
                continue

            q_text = rag_q["question_text"]
            options = rag_q["options"]
            correct_letter = rag_q["correct_answer_letter"]
            correct_text = rag_q.get("correct_answer_text", "")

            options_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
            full_question = f"{q_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"

            prompt = f"""You are a medical expert assistant. Answer the following medical question accurately by choosing the correct option.

Question: {full_question}

Answer:"""

            t_start = time.time()
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

            t_latency = round(time.time() - t_start, 3)

            predicted_letter = extract_predicted_letter(generated_answer, options)
            is_correct = (predicted_letter == correct_letter)

            baseline_record = {
                "question_id": q_id,
                "question_text": q_text,
                "options": options,
                "correct_answer_letter": correct_letter,
                "correct_answer_text": correct_text,
                "generated_answer": generated_answer,
                "predicted_letter": predicted_letter,
                "is_correct": is_correct,
                "latency_seconds": t_latency,
                "timestamp": datetime.now().isoformat()
            }

            out_f.write(json.dumps(baseline_record, ensure_ascii=False) + "\n")
            out_f.flush()

            existing_baseline[q_id] = baseline_record
            newly_processed += 1

            # Running stats
            current_completed = len(existing_baseline)
            running_correct = sum(1 for r in existing_baseline.values() if r.get("is_correct"))
            running_acc = (running_correct / current_completed) * 100.0

            elapsed = time.time() - loop_start_time
            avg_per_q = elapsed / newly_processed if newly_processed > 0 else 0
            remaining_q = total_questions - current_completed
            eta_secs = int(remaining_q * avg_per_q)
            eta_min, eta_sec = divmod(eta_secs, 60)
            eta_hr, eta_min = divmod(eta_min, 60)
            eta_str = f"{eta_hr}h {eta_min:02d}m" if eta_hr > 0 else f"{eta_min}m {eta_sec:02d}s"

            print(
                f"[{current_completed}/{total_questions}] "
                f"({current_completed/total_questions*100:.1f}%) {q_id} | "
                f"Pred: {predicted_letter} | Correct: {correct_letter} | "
                f"Match: {is_correct} | Time: {t_latency:.2f}s | "
                f"Acc: {running_acc:.1f}% ({running_correct}/{current_completed}) | "
                f"ETA: {eta_str}"
            )

    print("\n" + "=" * 70)
    print("Baseline generation complete. Computing comparison metrics...")
    print("=" * 70)

    # 3. Compute side-by-side comparison
    baseline_records_map = {r["question_id"]: r for r in load_jsonl(BASELINE_RESULTS_FILE)}

    both_correct = 0
    only_rag_correct = 0
    only_baseline_correct = 0
    both_wrong = 0

    rag_correct = 0
    baseline_correct = 0
    rag_unparsed = 0
    baseline_unparsed = 0
    rag_latencies = []
    baseline_latencies = []

    for rag_q in rag_records:
        q_id = rag_q["question_id"]
        base_q = baseline_records_map.get(q_id, {})

        rag_match = bool(rag_q.get("is_correct"))
        base_match = bool(base_q.get("is_correct"))

        if rag_match:
            rag_correct += 1
        if base_match:
            baseline_correct += 1

        if rag_q.get("predicted_letter") == "UNPARSED":
            rag_unparsed += 1
        if base_q.get("predicted_letter") == "UNPARSED":
            baseline_unparsed += 1

        if "latency_seconds" in rag_q:
            rag_latencies.append(rag_q["latency_seconds"])
        if "latency_seconds" in base_q:
            baseline_latencies.append(base_q["latency_seconds"])

        # 2x2 Contingency
        if rag_match and base_match:
            both_correct += 1
        elif rag_match and not base_match:
            only_rag_correct += 1
        elif not rag_match and base_match:
            only_baseline_correct += 1
        else:
            both_wrong += 1

    total = len(rag_records)
    rag_acc = (rag_correct / total) * 100.0 if total > 0 else 0.0
    base_acc = (baseline_correct / total) * 100.0 if total > 0 else 0.0
    diff_pp = rag_acc - base_acc

    avg_rag_lat = float(np.mean(rag_latencies)) if rag_latencies else 0.0
    avg_base_lat = float(np.mean(baseline_latencies)) if baseline_latencies else 0.0

    comparison_dict = {
        "dataset": "MedQA (USMLE)",
        "model": OLLAMA_MODEL,
        "total_questions": total,
        "rag_system": {
            "num_correct": rag_correct,
            "accuracy_percent": round(rag_acc, 2),
            "num_unparsed": rag_unparsed,
            "unparsed_percent": round((rag_unparsed / total) * 100.0, 2),
            "average_latency_seconds": round(avg_rag_lat, 2)
        },
        "baseline_system": {
            "num_correct": baseline_correct,
            "accuracy_percent": round(base_acc, 2),
            "num_unparsed": baseline_unparsed,
            "unparsed_percent": round((baseline_unparsed / total) * 100.0, 2),
            "average_latency_seconds": round(avg_base_lat, 2)
        },
        "difference_percentage_points": round(diff_pp, 2),
        "contingency_table_2x2": {
            "both_correct": both_correct,
            "only_rag_correct": only_rag_correct,
            "only_baseline_correct": only_baseline_correct,
            "both_wrong": both_wrong
        },
        "contingency_percentages": {
            "both_correct_pct": round((both_correct / total) * 100.0, 2),
            "only_rag_correct_pct": round((only_rag_correct / total) * 100.0, 2),
            "only_baseline_correct_pct": round((only_baseline_correct / total) * 100.0, 2),
            "both_wrong_pct": round((both_wrong / total) * 100.0, 2)
        },
        "timestamp": datetime.now().isoformat()
    }

    with open(COMPARISON_FILE, "w", encoding="utf-8") as f:
        json.dump(comparison_dict, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("                   RAG vs BASELINE COMPARISON REPORT                ")
    print("=" * 70)
    print(f"Total Evaluated Questions      : {total}")
    print(f"RAG Accuracy (with retrieval)  : {rag_acc:.2f}% ({rag_correct}/{total})")
    print(f"Baseline Accuracy (no context) : {base_acc:.2f}% ({baseline_correct}/{total})")
    print(f"Difference (RAG - Baseline)    : {diff_pp:+.2f} percentage points")
    print(f"RAG Unparsed                   : {rag_unparsed} ({(rag_unparsed/total)*100:.1f}%)")
    print(f"Baseline Unparsed              : {baseline_unparsed} ({(baseline_unparsed/total)*100:.1f}%)")
    print(f"Avg Latency - RAG              : {avg_rag_lat:.2f}s")
    print(f"Avg Latency - Baseline         : {avg_base_lat:.2f}s")
    print("-" * 70)
    print("2x2 CONTINGENCY TABLE:")
    print(f"  Both Correct          : {both_correct:3d} ({both_correct/total*100:.1f}%)")
    print(f"  Only RAG Correct      : {only_rag_correct:3d} ({only_rag_correct/total*100:.1f}%)")
    print(f"  Only Baseline Correct : {only_baseline_correct:3d} ({only_baseline_correct/total*100:.1f}%)")
    print(f"  Both Wrong / Unparsed : {both_wrong:3d} ({both_wrong/total*100:.1f}%)")
    print("=" * 70)
    print(f"Saved comparison JSON to: {COMPARISON_FILE}")


if __name__ == "__main__":
    run_baseline_evaluation()
