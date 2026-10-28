import os
import json
import time
import torch
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# NOTE: run with PYTHONUTF8=1 env var on Windows to handle non-ASCII textbook chars
# e.g.  $env:PYTHONUTF8="1"; python -u build_retrieval_system.py

# Set PyTorch thread count for optimal CPU execution
torch.set_num_threads(max(1, os.cpu_count() // 2 if os.cpu_count() else 4))

# ── Model constants ────────────────────────────────────────────────────────────
MODEL_NAME  = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM   = 384          # MiniLM output dimension
BATCH_SIZE  = 16           # Reduced batch size for CPU
SAVE_EVERY  = 100          # Checkpoint frequency (in batches)


def load_model():
    """Load all-MiniLM-L6-v2 — used for both passages and queries."""
    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully.")
    return model


def _format_eta(seconds: float) -> str:
    """Format seconds into a human-readable HH:MM:SS string."""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def generate_embeddings_with_checkpoints(
    texts,
    model,
    checkpoint_path,
    batch_size=BATCH_SIZE,
    save_every=SAVE_EVERY,
):
    """
    Generates embeddings batch-by-batch with per-100-batch checkpointing.
    Prints estimated time remaining after every batch.
    Resumes from a saved checkpoint if one exists.
    """
    total_texts   = len(texts)
    total_batches = (total_texts + batch_size - 1) // batch_size

    embeddings_list = []
    start_batch     = 0

    # ── Resume from checkpoint ────────────────────────────────────────────────
    if os.path.exists(checkpoint_path):
        existing = np.load(checkpoint_path)
        if 0 < len(existing) <= total_texts:
            embeddings_list.append(existing)
            start_batch = (len(existing) + batch_size - 1) // batch_size
            print(
                f"  Resuming from checkpoint: {len(existing)}/{total_texts} "
                f"passages already embedded (batch {start_batch}/{total_batches})."
            )

    remaining_batches = total_batches - start_batch
    if remaining_batches <= 0:
        print("  All embeddings already cached in checkpoint — skipping encoding.")
        return np.vstack(embeddings_list).astype(np.float32)

    print(
        f"  Encoding {remaining_batches} remaining batches "
        f"(batch_size={batch_size}, checkpoint every {save_every} batches) ..."
    )

    start_idx   = start_batch * batch_size
    batch_times = []
    wall_start  = time.time()

    for batch_num, i in enumerate(range(start_idx, total_texts, batch_size), start=1):
        t0        = time.time()
        sub_texts = texts[i : i + batch_size]

        sub_embeds = model.encode(
            sub_texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        embeddings_list.append(sub_embeds)
        elapsed_batch = time.time() - t0
        batch_times.append(elapsed_batch)

        # ── ETA calculation (rolling 20-batch average) ────────────────────────
        avg_time          = sum(batch_times[-20:]) / len(batch_times[-20:])
        batches_done      = start_batch + batch_num
        batches_remaining = total_batches - batches_done
        eta_seconds       = avg_time * batches_remaining
        total_elapsed     = time.time() - wall_start
        passages_done     = min(i + batch_size, total_texts)

        print(
            f"  Batch {batches_done:>4}/{total_batches} | "
            f"Passages {passages_done:>6}/{total_texts} | "
            f"Batch {elapsed_batch:.1f}s | "
            f"Elapsed {_format_eta(total_elapsed)} | "
            f"ETA {_format_eta(eta_seconds)}",
            flush=True,
        )

        # ── Checkpoint every SAVE_EVERY batches ───────────────────────────────
        if batch_num % save_every == 0:
            current_all = np.vstack(embeddings_list).astype(np.float32)
            np.save(checkpoint_path, current_all)
            print(f"  [CHECKPOINT] Saved {len(current_all)} passages -> {checkpoint_path}")

    # Final save
    final_embeddings = np.vstack(embeddings_list).astype(np.float32)
    np.save(checkpoint_path, final_embeddings)
    print(f"\n  Embedding complete. Total time: {_format_eta(time.time() - wall_start)} | {len(final_embeddings)} passages.")
    return final_embeddings


def embed_query(query_text, model):
    """Embeds a single query string. Returns (1, EMBED_DIM) float32 array."""
    return model.encode(
        [query_text],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)


def build_faiss_index(embeddings):
    """Builds an inner-product (cosine) FAISS index on CPU."""
    dim = embeddings.shape[1]
    print(f"Building FAISS IndexFlatIP (dim={dim}) over {len(embeddings)} vectors ...")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS index built — {index.ntotal} vectors indexed.")
    return index


def search_textbooks(query, index, df_metadata, model, top_k=5):
    """
    Given a query string, embed it and return the top-k most similar
    textbook chunks with metadata and similarity scores.
    """
    query_vec = embed_query(query, model)
    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(df_metadata):
            continue
        row = df_metadata.iloc[idx].to_dict()
        results.append({
            "rank":             len(results) + 1,
            "similarity_score": float(score),
            "chunk_id":         row.get("chunk_id", ""),
            "source_textbook":  row.get("source_textbook", ""),
            "textbook_title":   row.get("textbook_title", ""),
            "word_count":       row.get("word_count", 0),
            "chunk_text":       row.get("chunk_text", ""),
        })
    return results


def main():
    base_dir       = os.path.dirname(os.path.abspath(__file__))
    chunks_path    = os.path.join(base_dir, "processed_data", "textbook_chunks.parquet")
    questions_path = os.path.join(base_dir, "processed_data", "medqa_questions.json")

    vector_store_dir = os.path.join(base_dir, "vector_store")
    os.makedirs(vector_store_dir, exist_ok=True)

    index_file      = os.path.join(vector_store_dir, "textbook_faiss.index")
    checkpoint_file = os.path.join(vector_store_dir, "textbook_embeddings_checkpoint.npy")
    metadata_file   = os.path.join(vector_store_dir, "textbook_metadata.parquet")

    print("=" * 65)
    print("  MEDICAL TEXTBOOK FAISS VECTOR INDEX & RETRIEVAL SYSTEM")
    print(f"  Model : {MODEL_NAME}")
    print(f"  Dim   : {EMBED_DIM}  |  Batch size : {BATCH_SIZE}")
    print("=" * 65)

    # 1. Load single model (used for both passages and queries)
    model = load_model()

    # 2. Load chunk data
    print(f"\nLoading chunked textbook data from:\n  {chunks_path}")
    df_chunks = pd.read_parquet(chunks_path)
    print(f"Loaded {len(df_chunks):,} textbook chunks.")

    # 3. Build or load index
    if os.path.exists(index_file) and os.path.exists(metadata_file):
        print(f"\nExisting vector store found in {vector_store_dir}")
        print(f"Loading FAISS index from: {index_file}")
        index       = faiss.read_index(index_file)
        df_metadata = pd.read_parquet(metadata_file)
        print(f"Loaded index with {index.ntotal:,} vectors.")
    else:
        print("\nNo existing index found — building from scratch.")
        chunk_texts = df_chunks["chunk_text"].tolist()

        print(f"\n[Step 1/3] Generating embeddings for {len(chunk_texts):,} passages ...")
        embeddings = generate_embeddings_with_checkpoints(
            chunk_texts,
            model,
            checkpoint_file,
            batch_size=BATCH_SIZE,
            save_every=SAVE_EVERY,
        )

        print("\n[Step 2/3] Building FAISS index ...")
        index = build_faiss_index(embeddings)

        print(f"\n[Step 3/3] Saving vector store to: {vector_store_dir}")
        faiss.write_index(index, index_file)
        df_chunks.iloc[:len(embeddings)].to_parquet(metadata_file, index=False)
        df_metadata = df_chunks.iloc[:len(embeddings)]
        print("Vector store saved successfully!")

    # 4. Test retrieval with 3 sample MedQA questions
    print("\n" + "=" * 65)
    print("          TESTING RETRIEVAL SYSTEM (TOP-5 SEARCH)")
    print("=" * 65)

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    sample_questions = questions[:3]

    for q_idx, sample in enumerate(sample_questions, 1):
        q_text      = sample["question"]
        correct_ans = sample.get("correct_answer", "")
        options     = sample.get("options", {})

        print(f"\n--- [Sample Question {q_idx}] ---")
        print(f"QUESTION: {q_text[:250]}..." if len(q_text) > 250 else f"QUESTION: {q_text}")
        print(f"CORRECT ANSWER: {correct_ans}")
        print(f"OPTIONS: {options}")

        results = search_textbooks(q_text, index, df_metadata, model, top_k=5)

        print("\nTOP-5 RETRIEVED TEXTBOOK PASSAGES:")
        for r in results:
            snippet = r["chunk_text"][:300] + "..." if len(r["chunk_text"]) > 300 else r["chunk_text"]
            print(f"\n  Rank {r['rank']} | Score: {r['similarity_score']:.4f} | "
                  f"Book: {r['source_textbook']} ({r['chunk_id']})")
            print(f"  Snippet: {snippet}")

    print("\n" + "=" * 65)
    print("Phase 2 — Retrieval system set up and verified successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
