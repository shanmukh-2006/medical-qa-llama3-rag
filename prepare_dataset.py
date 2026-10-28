import os
import glob
import json
import re
import pandas as pd

def load_medqa_dataset(dataset_dir):
    """
    Loads MedQA dataset (train, dev, test) from JSONL files.
    Returns list of dicts with standardized structure.
    """
    questions = []
    splits = ["train", "dev", "test"]
    
    for split in splits:
        file_path = os.path.join(dataset_dir, f"{split}.jsonl")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                
                # Standardize question object structure
                parsed_item = {
                    "id": f"medqa_{split}_{idx}",
                    "split": split,
                    "question": data.get("question", ""),
                    "options": data.get("options", {}),
                    "correct_answer": data.get("answer", ""),
                    "answer_idx": data.get("answer_idx", ""),
                    "meta_info": data.get("meta_info", "")
                }
                questions.append(parsed_item)
                
    return questions


def chunk_text_sliding_window(text, target_chunk_size=400, overlap=50):
    """
    Chunks text into passages of 300-500 words (default ~400) with ~50 word overlap.
    """
    words = text.split()
    if not words:
        return []
        
    step_size = max(1, target_chunk_size - overlap)
    chunks = []
    
    for i in range(0, len(words), step_size):
        chunk_words = words[i : i + target_chunk_size]
        # Avoid creating tiny trailing chunks if possible
        if len(chunk_words) < 50 and len(chunks) > 0:
            chunks[-1]["chunk_text"] += " " + " ".join(chunk_words)
            chunks[-1]["word_count"] = len(chunks[-1]["chunk_text"].split())
            chunks[-1]["end_word_idx"] = i + len(chunk_words)
            break
            
        chunk_str = " ".join(chunk_words)
        chunks.append({
            "chunk_text": chunk_str,
            "word_count": len(chunk_words),
            "start_word_idx": i,
            "end_word_idx": i + len(chunk_words)
        })
        
        if i + target_chunk_size >= len(words):
            break
            
    return chunks


def load_and_chunk_textbooks(textbooks_dir, target_chunk_size=400, overlap=50):
    """
    Loads all .txt medical textbooks from directory and creates chunks with metadata.
    """
    all_chunks = []
    txt_files = sorted(glob.glob(os.path.join(textbooks_dir, "*.txt")))
    
    print(f"Found {len(txt_files)} textbook file(s) in {textbooks_dir}")
    
    for txt_file in txt_files:
        book_filename = os.path.basename(txt_file)
        book_name = os.path.splitext(book_filename)[0]
        
        # Read text with fallback encodings
        content = ""
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(txt_file, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
                
        # Clean extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Chunk text
        book_chunks = chunk_text_sliding_window(content, target_chunk_size=target_chunk_size, overlap=overlap)
        
        for c_idx, chunk in enumerate(book_chunks):
            chunk_metadata = {
                "chunk_id": f"{book_name}_chunk_{c_idx:05d}",
                "source_textbook": book_filename,
                "textbook_title": book_name,
                "chunk_text": chunk["chunk_text"],
                "word_count": chunk["word_count"],
                "start_word_idx": chunk["start_word_idx"],
                "end_word_idx": chunk["end_word_idx"]
            }
            all_chunks.append(chunk_metadata)
            
        print(f"  Processed '{book_filename}': {len(book_chunks)} chunks created.")
        
    return all_chunks


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    questions_dir = os.path.join(base_dir, "data", "data_clean", "questions", "US")
    textbooks_dir = os.path.join(base_dir, "data", "data_clean", "textbooks", "en")
    output_dir = os.path.join(base_dir, "processed_data")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("      MEDQA & MEDICAL TEXTBOOKS DATA PREPARATION PIPELINE   ")
    print("=" * 60)
    
    # 1. Load MedQA Dataset
    print("\n[Step 1/3] Loading MedQA dataset...")
    questions = load_medqa_dataset(questions_dir)
    print(f"Loaded {len(questions)} MedQA questions in total.")
    
    # 2. Process and Chunk Textbooks
    print("\n[Step 2/3] Processing and chunking medical textbooks...")
    textbook_chunks = load_and_chunk_textbooks(textbooks_dir, target_chunk_size=400, overlap=50)
    
    # 3. Save Processed Data
    print("\n[Step 3/3] Saving processed data to JSON and Parquet...")
    
    # Questions
    df_questions = pd.DataFrame(questions)
    questions_parquet_path = os.path.join(output_dir, "medqa_questions.parquet")
    questions_json_path = os.path.join(output_dir, "medqa_questions.json")
    
    df_questions.to_parquet(questions_parquet_path, index=False)
    with open(questions_json_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
        
    # Textbooks
    df_chunks = pd.DataFrame(textbook_chunks)
    chunks_parquet_path = os.path.join(output_dir, "textbook_chunks.parquet")
    chunks_json_path = os.path.join(output_dir, "textbook_chunks.json")
    
    df_chunks.to_parquet(chunks_parquet_path, index=False)
    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump(textbook_chunks, f, indent=2, ensure_ascii=False)
        
    print(f"Saved questions to:\n  - {questions_parquet_path}\n  - {questions_json_path}")
    print(f"Saved textbook chunks to:\n  - {chunks_parquet_path}\n  - {chunks_json_path}")
    
    # 4. Print Summary Stats
    print("\n" + "=" * 60)
    print("                     PIPELINE STATISTICS                    ")
    print("=" * 60)
    
    # Question stats by split
    split_counts = df_questions['split'].value_counts().to_dict() if not df_questions.empty else {}
    print(f"Total Questions Loaded   : {len(questions)}")
    for split_name, count in split_counts.items():
        print(f"  - {split_name.capitalize()} split       : {count}")
        
    # Chunk stats
    total_chunks = len(textbook_chunks)
    chunk_lengths = [c["word_count"] for c in textbook_chunks]
    avg_length = sum(chunk_lengths) / total_chunks if total_chunks > 0 else 0
    min_length = min(chunk_lengths) if total_chunks > 0 else 0
    max_length = max(chunk_lengths) if total_chunks > 0 else 0
    
    print(f"\nTotal Textbooks Processed: {len(df_chunks['source_textbook'].unique()) if not df_chunks.empty else 0}")
    print(f"Total Textbook Chunks    : {total_chunks}")
    print(f"Average Chunk Length     : {avg_length:.2f} words")
    print(f"Min Chunk Length         : {min_length} words")
    print(f"Max Chunk Length         : {max_length} words")
    print("=" * 60)

if __name__ == "__main__":
    main()
