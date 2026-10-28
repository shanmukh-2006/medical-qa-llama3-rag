import os
import json
import pandas as pd
import numpy as np
import faiss
import requests
import time
from sentence_transformers import SentenceTransformer

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")

INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_faiss.index")
METADATA_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_metadata.parquet")
MEDQA_FILE = os.path.join(PROCESSED_DIR, "medqa_questions.json")
RESULTS_CSV = os.path.join(BASE_DIR, "rag_results.csv")

# Ollama Config
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

print("Loading Retrieval System (Phase 2 assets)...")
# Load model, index, metadata
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
index = faiss.read_index(INDEX_FILE)
df_meta = pd.read_parquet(METADATA_FILE)
print("Retrieval system loaded successfully.\n")

def retrieve(query, top_k=5):
    """Retrieves top_k relevant textbook chunks for a given query."""
    vec = embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, indices = index.search(vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(df_meta): continue
        row = df_meta.iloc[idx]
        results.append({
            "book": row.get("source_textbook", ""),
            "chunk_id": row.get("chunk_id", ""),
            "text": row.get("chunk_text", ""),
            "score": float(score)
        })
    return results

def generate_answer(question, context_chunks):
    """Formats prompt and calls Ollama Llama 3 to generate an answer."""
    context_str = "\n\n".join([f"Source: {c['book']}\nText: {c['text']}" for c in context_chunks])
    
    prompt = f"""You are a medical expert assistant. Use the following retrieved medical context to answer the question accurately. If the context doesn't contain enough information, say so rather than guessing.

Context:
{context_str}

Question: {question}

Answer:"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "ERROR_CONNECTION"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    # --- PHASE 3: Llama 3 Integration Test (5 Samples) ---
    print("="*60)
    print("PHASE 3: Llama 3 Integration Manual Test")
    print("="*60)
    
    sample_questions = [
        "What causes chest pain radiating to the left arm?",
        "Which vitamin deficiency causes scurvy?",
        "What is the first-line treatment for type 2 diabetes?",
        "What is the most common cause of community-acquired pneumonia?",
        "How do you treat a suspected opioid overdose?"
    ]
    
    for q in sample_questions:
        print(f"\n[Question] {q}")
        chunks = retrieve(q)
        print(f"[Context] Retrieved {len(chunks)} passages. Top match: {chunks[0]['book']} (Score: {chunks[0]['score']:.4f})")
        
        ans = generate_answer(q, chunks)
        if ans == "ERROR_CONNECTION":
            print("\n❌ CRITICAL ERROR: Could not connect to Ollama.")
            print("Please ensure Ollama is running on localhost:11434 and you have pulled llama3.")
            print("Run: `ollama run llama3` in a separate terminal.")
            return
            
        print(f"[Llama 3 Answer]\n{ans}\n")
        print("-" * 40)

    # --- PHASE 4: Full Pipeline Integration ---
    print("\n" + "="*60)
    print("PHASE 4: Full Pipeline on MedQA subset (20 questions)")
    print("="*60)
    
    with open(MEDQA_FILE, 'r', encoding='utf-8') as f:
        medqa_data = json.load(f)
    
    # Process 20 sample questions
    test_questions = medqa_data[:20]
    results = []
    
    start_time = time.time()
    for i, item in enumerate(test_questions):
        q_text = item.get('question', '')
        options = item.get('options', {})
        correct = item.get('correct_answer', '')
        
        # Format the multiple choice question for the model
        options_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
        full_question = f"{q_text}\n\nOptions:\n{options_str}\n\nWhich option is correct?"
        
        print(f"Processing Q{i+1}/20...")
        chunks = retrieve(full_question)
        ans = generate_answer(full_question, chunks)
        
        results.append({
            "Question": q_text,
            "Options": json.dumps(options),
            "Correct_Answer": correct,
            "Retrieved_Sources": json.dumps([c['book'] for c in chunks]),
            "Generated_Answer": ans
        })
        
    df_results = pd.DataFrame(results)
    df_results.to_csv(RESULTS_CSV, index=False, encoding='utf-8')
    elapsed = time.time() - start_time
    
    print(f"\n✅ Phase 4 Complete!")
    print(f"Processed 20 questions in {elapsed:.1f} seconds.")
    print(f"Results saved to: {RESULTS_CSV}")

if __name__ == '__main__':
    main()
