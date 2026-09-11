"""
test_summarizer.py

Unit tests for src/summarizer.py.

All tests run offline (use_llm=False) or against pure functions,
so no Groq API key is required.
"""

from src.summarizer import (
    extract_keywords,
    summarize_chunk,
    summarize_chunks,
)


SUMMARY_KEYS = {
    "company_name",
    "source_id",
    "source_type",
    "source_name",
    "chunk_id",
    "summary",
    "keywords",
}


def _sample_chunk(text="Zerodha is a bootstrapped Indian brokerage firm."):
    return {
        "company_name": "zerodha",
        "source_id": "src_01",
        "source_type": "report",
        "source_name": "about.html",
        "chunk_id": "src_01_chunk_001",
        "text": text,
    }


def test_extract_keywords_returns_list_within_limit():
    text = "growth growth growth revenue revenue profit users india market"
    keywords = extract_keywords(text, max_keywords=3)
    assert isinstance(keywords, list)
    assert len(keywords) <= 3
    assert keywords[0] == "growth"


def test_extract_keywords_excludes_stopwords_and_short_words():
    text = "the and of to in is a an it we our growth"
    keywords = extract_keywords(text)
    for stop in ["the", "and", "of", "to", "we", "our", "a", "an", "it"]:
        assert stop not in keywords
    assert all(len(word) >= 3 for word in keywords)


def test_summarize_chunk_offline_preserves_contract():
    chunk = _sample_chunk()
    result = summarize_chunk(chunk, use_llm=False)
    assert SUMMARY_KEYS == set(result.keys())
    assert result["company_name"] == chunk["company_name"]
    assert result["chunk_id"] == chunk["chunk_id"]
    assert result["source_name"] == chunk["source_name"]
    assert isinstance(result["summary"], str) and result["summary"]
    assert isinstance(result["keywords"], list)


def test_summarize_chunk_offline_uses_text_fallback():
    long_text = "word " * 100
    chunk = _sample_chunk(text=long_text)
    result = summarize_chunk(chunk, use_llm=False)
    assert result["summary"].endswith("...")
    assert len(result["summary"]) <= 210


def test_summarize_chunks_offline_matches_input_count():
    chunks = [
        _sample_chunk(text="First chunk about Zerodha's founding."),
        _sample_chunk(text="Second chunk about its profit surge."),
    ]
    chunks[1]["chunk_id"] = "src_01_chunk_002"

    summaries = summarize_chunks(chunks, use_llm=False)
    assert len(summaries) == len(chunks)
    ids = [s["chunk_id"] for s in summaries]
    assert ids == ["src_01_chunk_001", "src_01_chunk_002"]


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
