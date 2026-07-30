"""
chunker.py

Splits cleaned document text into smaller chunks for
downstream summarization and generation.
"""

from typing import List, Dict
import json
from pathlib import Path
from src.config import BASE_DIR

CHUNK_SIZE = 800       # characters per chunk
CHUNK_OVERLAP = 100     # overlap to preserve context between chunks
CLEANED_DATA_DIR = BASE_DIR / "data" / "cleaned"


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks of a fixed character size."""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def chunk_document(document: Dict) -> List[Dict]:
    """
    Take one document dict (from input_loader.py) and return
    a list of chunk dicts following the shared data contract.
    """
    raw_chunks = split_text_into_chunks(document["text"])
    chunked_records = []

    for index, chunk_text in enumerate(raw_chunks, start=1):
        chunk_id = f"{document['source_id']}_chunk_{index:03d}"

        chunked_records.append({
            "company_name": document["company_name"],
            "source_id": document["source_id"],
            "source_type": document["source_type"],
            "source_name": document["source_name"],
            "chunk_id": chunk_id,
            "text": chunk_text,
        })

    return chunked_records


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """Chunk a list of documents (e.g. all documents for one company)."""
    all_chunks = []
    for document in documents:
        all_chunks.extend(chunk_document(document))
    return all_chunks

def save_chunks_to_disk(company_name: str, chunks: list) -> Path:
    """
    Save a company's chunks as a JSON file in data/cleaned/.
    """
    CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLEANED_DATA_DIR / f"{company_name.lower()}_chunks.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    return output_path

if __name__ == "__main__":
    from src.input_loader import load_company_documents

    for company in ["infosys", "nykaa", "zerodha"]:
        docs = load_company_documents(company)
        chunks = chunk_documents(docs)
        path = save_chunks_to_disk(company, chunks)
        print(f"{company}: {len(docs)} documents -> {len(chunks)} chunks saved to {path}")