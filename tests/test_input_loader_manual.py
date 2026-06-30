from src.input_loader import load_company_documents

for company in ["infosys", "nykaa", "zerodha"]:
    docs = load_company_documents(company)
    print(f"\nCompany: {company}")
    print(f"Documents loaded: {len(docs)}")

    for doc in docs:
        print(f"- {doc['source_id']} | {doc['source_name']} | {doc['source_type']} | chars: {len(doc['text'])}")