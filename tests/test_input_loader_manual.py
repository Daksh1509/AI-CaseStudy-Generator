from src.input_loader import load_company_documents
from src.chunker import chunk_documents

for company in ["infosys", "nykaa", "zerodha"]:
    docs = load_company_documents(company)
    chunks = chunk_documents(docs)
    print(f"{company}: {len(docs)} documents -> {len(chunks)} chunks")