from src.input_loader import load_company_documents
from src.chunker import chunk_documents


def test_chunks_have_required_fields():
    docs = load_company_documents("zerodha")
    chunks = chunk_documents(docs)

    assert len(chunks) > 0

    required_keys = {"company_name", "source_id", "source_type", "source_name", "chunk_id", "text"}
    for chunk in chunks:
        assert required_keys.issubset(chunk.keys())
        assert len(chunk["text"]) > 0


def test_no_empty_chunks():
    docs = load_company_documents("infosys")
    chunks = chunk_documents(docs)

    for chunk in chunks:
        assert chunk["text"].strip() != ""


if __name__ == "__main__":
    test_chunks_have_required_fields()
    test_no_empty_chunks()
    print("All chunker tests passed.")