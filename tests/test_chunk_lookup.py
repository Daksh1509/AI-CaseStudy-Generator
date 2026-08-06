import json
from src.config import INSIGHTS_DIR, CLEANED_DATA_DIR

with open(INSIGHTS_DIR / "zerodha_insights.json") as f:
    insights = json.load(f)

with open(CLEANED_DATA_DIR / "zerodha_chunks.json") as f:
    chunks = json.load(f)

chunk_ids = {c["chunk_id"] for c in chunks}

missing = 0
for section in ["background", "challenge", "strategy", "execution", "results", "learning"]:
    for item in insights.get(section, []):
        if item["chunk_id"] not in chunk_ids:
            print(f"MISSING: {item['chunk_id']}")
            missing += 1

print(f"Traceability check complete. Missing: {missing}")