"""
test_chunker.py

Tests for src/chunker.py.

Split into:
  - pure unit tests (no data files, always run)
  - integration tests over real company data (skipped if raw data
    is not present, so CI without the dataset still passes)
"""

import pytest

from src.chunker import (
    split_text_into_chunks,
    chunk_document,
    chunk_documents,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from src.input_loader import load_company_documents, list_company_files


REQUIRED_KEYS = {
    "company_name",
    "source_id",
    "source_type",
    "source_name",
    "chunk_id",
    "text",
}


def _sample_document(text: str) -> dict:
    return {
        "company_name": "testco",
        "source_id": "src_01",
        "source_type": "report",
        "source_name": "sample.pdf",
        "file_path": "",
        "chunk_id": None,
        "metadata": {},
        "text": text,
    }


# ----------------------------------------------------------
# Unit tests: split_text_into_chunks
# ----------------------------------------------------------

def test_split_empty_returns_empty_list():
    assert split_text_into_chunks("") == []


def test_split_short_text_single_chunk():
    chunks = split_text_into_chunks("short text")
    assert chunks == ["short text"]


def test_split_respects_chunk_size():
    text = "a" * 2500
    chunks = split_text_into_chunks(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= CHUNK_SIZE


def test_split_has_overlap_between_chunks():
    # Distinct characters so we can detect overlap at the boundary.
    text = "".join(chr(33 + (i % 90)) for i in range(2000))
    chunks = split_text_into_chunks(text)
    assert len(chunks) >= 2
    # The stride is CHUNK_SIZE - CHUNK_OVERLAP, so the tail of chunk 0
    # should reappear at the start of chunk 1.
    tail = chunks[0][-CHUNK_OVERLAP:]
    assert tail and tail in chunks[1]


# ----------------------------------------------------------
# Unit tests: chunk_document (contract + robustness)
# ----------------------------------------------------------

def test_chunk_document_produces_contract_fields():
    doc = _sample_document("x" * 2000)
    records = chunk_document(doc)
    assert len(records) > 0
    for record in records:
        assert REQUIRED_KEYS.issubset(record.keys())
        assert record["text"].strip() != ""


def test_chunk_document_chunk_id_format():
    doc = _sample_document("y" * 2000)
    records = chunk_document(doc)
    # chunk_id format is "{source_id}_chunk_{NNN}".
    assert records[0]["chunk_id"] == "src_01_chunk_001"
    assert records[1]["chunk_id"] == "src_01_chunk_002"


def test_chunk_document_preserves_metadata():
    doc = _sample_document("z" * 1500)
    records = chunk_document(doc)
    for record in records:
        assert record["company_name"] == "testco"
        assert record["source_id"] == "src_01"
        assert record["source_type"] == "report"
        assert record["source_name"] == "sample.pdf"


def test_chunk_document_empty_text_returns_no_chunks():
    # Weak-extraction case: must not raise, must return [].
    assert chunk_document(_sample_document("")) == []
    assert chunk_document(_sample_document("    ")) == []


def test_chunk_document_missing_text_key_returns_no_chunks():
    doc = _sample_document("ignored")
    del doc["text"]
    # Must not raise KeyError.
    assert chunk_document(doc) == []


# ----------------------------------------------------------
# Integration tests over real company data (auto-skip if absent)
# ----------------------------------------------------------

def _has_raw_data(company: str) -> bool:
    try:
        return len(list_company_files(company)) > 0
    except Exception:
        return False


@pytest.mark.skipif(not _has_raw_data("zerodha"), reason="raw data not present")
def test_real_zerodha_chunks_have_required_fields():
    docs = load_company_documents("zerodha")
    chunks = chunk_documents(docs)
    assert len(chunks) > 0
    for chunk in chunks:
        assert REQUIRED_KEYS.issubset(chunk.keys())
        assert chunk["text"].strip() != ""


@pytest.mark.skipif(not _has_raw_data("infosys"), reason="raw data not present")
def test_real_infosys_no_empty_chunks():
    docs = load_company_documents("infosys")
    chunks = chunk_documents(docs)
    for chunk in chunks:
        assert chunk["text"].strip() != ""


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
