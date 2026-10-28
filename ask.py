import os
import faiss
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_faiss.index")
METADATA_FILE = os.path.join(VECTOR_STORE_DIR, "textbook_metadata.parquet")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

print("Loading Medical RAG System (this takes a few seconds)...")
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
index = faiss.read_index(INDEX_FILE)
df_meta = pd.read_parquet(METADATA_FILE)
print("Ready!\n" + "="*50)

def retrieve(query, top_k=5):
    vec = embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, indices = index.search(vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(df_meta):
            row = df_meta.iloc[idx]
            results.append({
                "book": row.get("source_textbook", ""),
                "text": row.get("chunk_text", "")
            })
    return results

def ask_llama(question, context_chunks):
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
    except Exception as e:
        return f"ERROR communicating with Ollama: {str(e)}"

# Interactive Loop
while True:
    user_q = input("\n🩺 Enter your medical question (or type 'quit' to exit):\n> ")
    if user_q.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        break
    if not user_q.strip():
        continue
        
    print("\n🔍 Retrieving textbook context...")
    chunks = retrieve(user_q)
    print(f"   (Found sources: {', '.join(list(set(c['book'] for c in chunks)))})")
    
    print("🧠 Llama 3 is thinking...")
    answer = ask_llama(user_q, chunks)
    
    print("\n" + "-"*50)
    print(f"🤖 ANSWER:\n{answer}")
    print("-"*50)
