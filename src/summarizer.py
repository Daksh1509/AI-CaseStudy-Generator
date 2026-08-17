"""
summarizer.py

Summarizes individual chunks of company text into short,
factual summaries with keywords, using the Groq API.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

_client = None


# ==========================================================
# Groq Client
# ==========================================================

def get_client():
    global _client

    if _client is None:

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Check your .env file."
            )

        _client = Groq(api_key=api_key)

    return _client


# ==========================================================
# Prompt Builder
# ==========================================================

def build_summarization_prompt(chunk: Dict) -> str:

    return (
        f"Summarize the following text about {chunk['company_name']} "
        f"in 2-3 sentences. Preserve only factual information. "
        f"Do not invent or assume anything not stated in the text. "
        f"Respond with ONLY the summary text — no preamble, no headers, "
        f"no phrases like 'Here is a summary'.\n\n"
        f"Text:\n{chunk['text']}\n\n"
        f"Summary:"
    )


# ==========================================================
# LLM Call
# ==========================================================

def call_llm(prompt: str) -> str:

    client = get_client()

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


# ==========================================================
# Keyword Extraction
# ==========================================================

def extract_keywords(
    text: str,
    max_keywords: int = 5,
) -> List[str]:

    import re
    from collections import Counter

    stopwords = {
        "the", "and", "of", "to", "in", "is", "for", "with", "on",
        "are", "we", "our", "a", "an", "at", "as", "by", "this",
        "that", "it", "from", "was", "were", "be", "has", "have",
        "had",
    }

    words = re.findall(
        r"[a-zA-Z]{3,}",
        text.lower(),
    )

    filtered = [
        word
        for word in words
        if word not in stopwords
    ]

    return [
        word
        for word, _ in Counter(filtered).most_common(max_keywords)
    ]


# ==========================================================
# Summarize One Chunk
# ==========================================================

def summarize_chunk(
    chunk: Dict,
    use_llm: bool = True,
) -> Dict:
    """
    Summarize one chunk while preserving metadata.
    """

    prompt = build_summarization_prompt(chunk)

    if use_llm:

        try:

            summary_text = call_llm(prompt)

        except Exception as error:

            logger.warning(
                "LLM call failed for %s, using fallback: %s",
                chunk["chunk_id"],
                error,
            )

            summary_text = (
                chunk["text"][:200].strip() + "..."
            )

    else:

        summary_text = (
            chunk["text"][:200].strip() + "..."
        )

    keywords = extract_keywords(chunk["text"])

    return {

        "company_name": chunk["company_name"],

        "source_id": chunk["source_id"],

        "source_type": chunk["source_type"],

        "source_name": chunk["source_name"],

        "chunk_id": chunk["chunk_id"],

        "summary": summary_text,

        "keywords": keywords,
    }


# ==========================================================
# Summarize All Chunks
# ==========================================================

def summarize_chunks(
    chunks: List[Dict],
    use_llm: bool = True,
) -> List[Dict]:

    summaries = []

    for chunk in chunks:

        try:

            summaries.append(
                summarize_chunk(
                    chunk,
                    use_llm=use_llm,
                )
            )

        except Exception as error:

            logger.warning(
                "Failed to summarize chunk %s: %s",
                chunk.get("chunk_id"),
                error,
            )

    return summaries


# ==========================================================
# Save Summaries
# ==========================================================

def save_summaries_to_disk(
    company_name: str,
    summaries: list,
) -> Path:

    from src.config import SUMMARIES_DIR

    SUMMARIES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        SUMMARIES_DIR
        / f"{company_name.lower()}_summaries.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summaries,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    from src.input_loader import load_company_documents
    from src.chunker import chunk_documents

    company = "zerodha"

    docs = load_company_documents(company)

    chunks = chunk_documents(docs)

    print(
        f"Loaded {len(docs)} documents, "
        f"{len(chunks)} chunks for {company}\n"
    )

    # Process ALL chunks
    summaries = summarize_chunks(
        chunks,
        use_llm=True,
    )

    for summary in summaries[:5]:

        print("=" * 70)

        print(f"chunk_id: {summary['chunk_id']}")

        print(f"summary: {summary['summary']}")

        print(f"keywords: {summary['keywords']}")

    saved_path = save_summaries_to_disk(
        company,
        summaries,
    )

    print(f"\nSaved summaries to: {saved_path}")