"""
test_chunk_lookup.py

Traceability check: every chunk_id referenced by a generated insight
must exist in that company's saved chunks (so evidence lookup can
never point at a missing chunk).

This depends on generated artifacts (outputs/insights/*.json and
data/cleaned/*_chunks.json), which are gitignored. The test therefore
SKIPS cleanly when those files are absent, instead of erroring, so a
fresh checkout still passes `pytest tests/`.
"""

import json

import pytest

from src.config import INSIGHTS_DIR, CLEANED_DATA_DIR

SECTIONS = ["background", "challenge", "strategy", "execution", "results", "learning"]


def _artifacts_exist(company: str) -> bool:
    insights = INSIGHTS_DIR / f"{company}_insights.json"
    chunks = CLEANED_DATA_DIR / f"{company}_chunks.json"
    return insights.exists() and chunks.exists()


@pytest.mark.skipif(
    not _artifacts_exist("zerodha"),
    reason="generated insights/chunks not present (run the pipeline first)",
)
def test_every_insight_chunk_id_is_traceable():
    company = "zerodha"

    with open(INSIGHTS_DIR / f"{company}_insights.json", encoding="utf-8") as f:
        insights = json.load(f)

    with open(CLEANED_DATA_DIR / f"{company}_chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)

    chunk_ids = {c["chunk_id"] for c in chunks}

    missing = []
    for section in SECTIONS:
        for item in insights.get(section, []):
            if item["chunk_id"] not in chunk_ids:
                missing.append(item["chunk_id"])

    assert not missing, f"Insights reference missing chunk_ids: {missing}"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
