import os
import json
import time
import torch
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# Set PyTorch thread count for CPU execution
torch.set_num_threads(max(1, os.cpu_count() // 2 if os.cpu_count() else 4))

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chunks_path = os.path.join(base_dir, "processed_data", "textbook_chunks.parquet")
    questions_path = os.path.join(base_dir, "processed_data", "medqa_questions.json")
    
    vector_store_dir = os.path.join(base_dir, "vector_store")
    os.makedirs(vector_store_dir, exist_ok=True)

    print("=" * 65)
    print("      FAISS VECTOR RETRIEVAL SYSTEM DEMO (MEDCPT ENCODERS)      ")
    print("=" * 65)
    
    print("\n[Step 1/4] Loading MedCPT Encoders...")
    art_model = SentenceTransformer("ncbi/MedCPT-Article-Encoder")
    q_model = SentenceTransformer("ncbi/MedCPT-Query-Encoder")
    
    print("\n[Step 2/4] Loading textbook chunk data...")
    df_chunks = pd.read_parquet(chunks_path)
    print(f"Total textbook chunks in dataset: {len(df_chunks)}")
    
    index_file = os.path.join(vector_store_dir, "textbook_faiss_demo.index")
    metadata_file = os.path.join(vector_store_dir, "textbook_metadata_demo.parquet")
    
    if os.path.exists(index_file) and os.path.exists(metadata_file):
        print(f"Loading existing demo vector store from {vector_store_dir}...")
        index = faiss.read_index(index_file)
        df_sample = pd.read_parquet(metadata_file)
    else:
        # Sample representative chunks across textbooks
        df_sample = df_chunks.groupby("source_textbook", as_index=False, group_keys=False).apply(
            lambda x: x.sample(min(len(x), 6), random_state=42)
        ).reset_index(drop=True)
        
        print(f"Sampled {len(df_sample)} representative chunks across 18 textbooks for retrieval testing...")
        
        print("\n[Step 3/4] Generating MedCPT passage embeddings for test set...")
        start_time = time.time()
        sample_texts = df_sample["chunk_text"].tolist()
        
        embeddings = art_model.encode(
            sample_texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype(np.float32)
        
        print(f"Embeddings generated in {time.time() - start_time:.2f} seconds. Shape: {embeddings.shape}")
        
        # Build FAISS Index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        # Save demo index & metadata
        faiss.write_index(index, index_file)
        df_sample.to_parquet(metadata_file, index=False)
        print(f"Saved FAISS index to {index_file}")
    
    # 4. Run Retrieval on 3 Sample MedQA Questions
    print("\n[Step 4/4] Testing Retrieval with 3 Sample MedQA Questions...")
    print("=" * 65)
    
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    sample_questions = questions[:3]
    
    for q_idx, sample in enumerate(sample_questions, 1):
        q_text = sample["question"]
        correct_ans = sample.get("correct_answer", "")
        options = sample.get("options", {})
        
        print(f"\n==================== [SAMPLE QUESTION {q_idx}] ====================")
        print(f"QUESTION:\n{q_text}")
        print(f"\nCORRECT ANSWER: {correct_ans}")
        print(f"OPTIONS: {options}")
        
        # Embed query using Query Encoder
        query_vec = q_model.encode([q_text], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
        scores, indices = index.search(query_vec, k=5)
        
        print("\nTOP-5 RETRIEVED TEXTBOOK PASSAGES (MedCPT Similarity):")
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            row = df_sample.iloc[idx]
            print(f"\n  [Rank {rank}] Similarity Score: {score:.4f}")
            print(f"  Source Textbook : {row.get('source_textbook', 'N/A')} ({row.get('chunk_id', 'N/A')})")
            snippet = row['chunk_text'][:280].replace('\n', ' ') + "..."
            print(f"  Passage Snippet : \"{snippet}\"")
            
    print("\n" + "=" * 65)
    print("Retrieval System setup and sample test completed successfully!")
    print("=" * 65)

if __name__ == "__main__":
    main()
