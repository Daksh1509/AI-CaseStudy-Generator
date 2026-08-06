"""
chunk_lookup.py

Provides lookup of original chunk text by chunk_id,
used to attach real evidence snippets to generated
case study sections.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from src.config import CLEANED_DATA_DIR  # adjust name if different in your config.py

logger = logging.getLogger(__name__)

_chunk_cache: Dict[str, Dict] = {}


def load_chunks_for_company(company_name: str) -> Dict[str, Dict]:
    """
    Load all chunks for a company and index them by chunk_id.
    Cached so repeated lookups are fast.
    """
    cache_key = company_name.lower()

    if cache_key in _chunk_cache:
        return _chunk_cache[cache_key]

    chunks_path = CLEANED_DATA_DIR / f"{company_name.lower()}_chunks.json"

    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks_list = json.load(f)

    indexed = {chunk["chunk_id"]: chunk for chunk in chunks_list}
    _chunk_cache[cache_key] = indexed
    return indexed


def get_chunk_text(company_name: str, chunk_id: str) -> Optional[str]:
    """
    Return the original text of a chunk, or None if not found.
    """
    chunks = load_chunks_for_company(company_name)
    chunk = chunks.get(chunk_id)
    if chunk is None:
        logger.warning("chunk_id %s not found for %s", chunk_id, company_name)
        return None
    return chunk["text"]


if __name__ == "__main__":
    company = "zerodha"
    chunks = load_chunks_for_company(company)
    print(f"Loaded {len(chunks)} chunks for {company}")

    sample_id = next(iter(chunks))
    print(f"\nSample chunk_id: {sample_id}")
    print(get_chunk_text(company, sample_id)[:200])