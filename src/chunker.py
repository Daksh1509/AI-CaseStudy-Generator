"""
chunker.py

Splits cleaned document text into smaller chunks for
downstream summarization and generation.
"""

from typing import List, Dict

CHUNK_SIZE = 800       # characters per chunk
CHUNK_OVERLAP = 100     # overlap to preserve context between chunks


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


if __name__ == "__main__":
    from src.input_loader import load_company_documents

    company = "infosys"
    docs = load_company_documents(company)
    chunks = chunk_documents(docs)

    print(f"Loaded {len(docs)} documents, produced {len(chunks)} chunks\n")

    for chunk in chunks[:3]:
        print("=" * 70)
        print(f"chunk_id: {chunk['chunk_id']}")
        print(f"source_id: {chunk['source_id']}")
        print(f"text preview: {chunk['text'][:200]}")