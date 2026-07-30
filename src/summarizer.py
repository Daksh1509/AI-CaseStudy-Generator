"""
summarizer.py

Summarizes individual chunks of company text into short,
factual summaries with keywords, following the shared
module contract.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def build_summarization_prompt(chunk: Dict) -> str:
    """
    Build the prompt text for summarizing a single chunk.
    """
    return (
        f"Summarize the following text about {chunk['company_name']} "
        f"in 2-3 sentences. Preserve only factual information. "
        f"Do not invent or assume anything not stated in the text.\n\n"
        f"Text:\n{chunk['text']}\n\n"
        f"Summary:"
    )


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Very simple placeholder keyword extractor based on frequency.
    Replace later with a proper keyword/embedding-based method.
    """
    import re
    from collections import Counter

    stopwords = {
        "the", "and", "of", "to", "in", "is", "for", "with", "on", "are",
        "we", "our", "a", "an", "at", "as", "by", "this", "that", "it",
        "from", "was", "were", "be", "has", "have", "had"
    }

    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    filtered = [w for w in words if w not in stopwords]
    most_common = Counter(filtered).most_common(max_keywords)

    return [word for word, _ in most_common]


def summarize_chunk(chunk: Dict, model=None) -> Dict:
    """
    Summarize a single chunk following the module contract:

    Input: {company_name, chunk_id, text}
    Output: {chunk_id, summary, keywords}
    """
    prompt = build_summarization_prompt(chunk)

    if model is not None:
        summary_text = model.generate(prompt)
    else:
        # Placeholder until a real model/API is connected.
        summary_text = chunk["text"][:200].strip() + "..."

    keywords = extract_keywords(chunk["text"])

    return {
        "chunk_id": chunk["chunk_id"],
        "summary": summary_text,
        "keywords": keywords,
    }


def summarize_chunks(chunks: List[Dict], model=None) -> List[Dict]:
    """
    Summarize a list of chunks, returning a list of summary records.
    """
    summaries = []
    for chunk in chunks:
        try:
            summaries.append(summarize_chunk(chunk, model=model))
        except Exception as error:
            logger.warning("Failed to summarize chunk %s: %s", chunk.get("chunk_id"), error)
    return summaries


if __name__ == "__main__":
    from src.input_loader import load_company_documents
    from src.chunker import chunk_documents

    company = "zerodha"
    docs = load_company_documents(company)
    chunks = chunk_documents(docs)

    print(f"Loaded {len(docs)} documents, {len(chunks)} chunks for {company}\n")

    summaries = summarize_chunks(chunks)

    for summary in summaries[:3]:
        print("=" * 70)
        print(f"chunk_id: {summary['chunk_id']}")
        print(f"summary: {summary['summary']}")
        print(f"keywords: {summary['keywords']}")