"""
test_references.py

Unit tests for src/references.py (evidence + confidence mapping).

The chunk lookup is monkeypatched so these tests are hermetic:
they need no data files and no Groq API key.
"""

import src.references as references
from src.references import (
    determine_confidence,
    build_evidence_for_section,
    attach_evidence_to_case_study,
    SECTION_KEY_MAP,
)


EVIDENCE_KEYS = {"chunk_id", "source_id", "source_name", "source_type", "snippet"}


def _insight(n):
    return {
        "chunk_id": f"src_01_chunk_00{n}",
        "source_id": "src_01",
        "source_type": "report",
        "source_name": "about.html",
        "insight": f"Insight number {n}.",
        "keywords": ["zerodha"],
    }


def test_determine_confidence_mapping():
    assert determine_confidence(0, 0) == "Weak Evidence"
    assert determine_confidence(1, 1) == "Low"
    assert determine_confidence(2, 2) == "Medium"
    assert determine_confidence(3, 3) == "Medium"
    assert determine_confidence(3, 4) == "High"
    assert determine_confidence(3, 10) == "High"


def test_build_evidence_uses_chunk_text_when_available(monkeypatch):
    monkeypatch.setattr(
        references, "get_chunk_text",
        lambda company, chunk_id: "REAL " * 100,
    )
    evidence = build_evidence_for_section("zerodha", [_insight(1)], max_snippets=3)
    assert len(evidence) == 1
    assert EVIDENCE_KEYS == set(evidence[0].keys())
    assert evidence[0]["snippet"].endswith("...")
    assert len(evidence[0]["snippet"]) <= 303


def test_build_evidence_falls_back_to_insight_when_chunk_missing(monkeypatch):
    monkeypatch.setattr(
        references, "get_chunk_text",
        lambda company, chunk_id: None,
    )
    evidence = build_evidence_for_section("zerodha", [_insight(2)], max_snippets=3)
    assert evidence[0]["snippet"] == "Insight number 2."


def test_build_evidence_respects_max_snippets(monkeypatch):
    monkeypatch.setattr(
        references, "get_chunk_text",
        lambda company, chunk_id: "text",
    )
    many = [_insight(i) for i in range(1, 6)]
    evidence = build_evidence_for_section("zerodha", many, max_snippets=3)
    assert len(evidence) == 3


def test_attach_evidence_builds_final_schema(monkeypatch):
    monkeypatch.setattr(
        references, "get_chunk_text",
        lambda company, chunk_id: "source snippet text",
    )

    case_study = {
        "company_name": "zerodha",
        "case_study": {
            "Background": "Background content.",
            "Challenge": "No sufficient evidence available.",
            "Learning": "Learning content.",
        },
    }
    grouped_insights = {
        "company_name": "zerodha",
        "background": [_insight(1), _insight(2)],
        "challenge": [],
        "learning": [_insight(3), _insight(4), _insight(5), _insight(6)],
    }

    final = attach_evidence_to_case_study("zerodha", case_study, grouped_insights)

    assert final["company_name"] == "zerodha"
    sections = final["case_study"]

    for name in ["Background", "Challenge", "Learning"]:
        assert set(sections[name].keys()) == {"content", "evidence", "confidence"}

    assert sections["Background"]["confidence"] == "Medium"
    assert sections["Challenge"]["confidence"] == "Weak Evidence"
    assert sections["Challenge"]["evidence"] == []
    assert sections["Learning"]["confidence"] == "High"
    assert len(sections["Learning"]["evidence"]) == 3


def test_section_key_map_handles_learning_variants():
    assert SECTION_KEY_MAP["Learning"] == "learning"
    assert SECTION_KEY_MAP["Learning Outcomes"] == "learning"


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
