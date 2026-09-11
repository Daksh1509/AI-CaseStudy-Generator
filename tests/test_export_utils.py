"""
test_export_utils.py

Unit tests for src/export_utils.py (Markdown / plain-text export).
Pure functions over a sample final case study; no files, no API key.
"""

from src.export_utils import (
    build_markdown,
    build_plain_text,
    export_case_study,
)


def _final_case_study():
    return {
        "company_name": "zerodha",
        "case_study": {
            "Background": {
                "content": "Zerodha is a bootstrapped brokerage.",
                "evidence": [
                    {
                        "chunk_id": "src_01_chunk_001",
                        "source_id": "src_01",
                        "source_name": "about.html",
                        "source_type": "official_page",
                        "snippet": "Zerodha was founded in 2010...",
                    }
                ],
                "confidence": "Medium",
            },
            "Challenge": {
                "content": "No sufficient evidence available.",
                "evidence": [],
                "confidence": "Weak Evidence",
            },
            "Strategy": {"content": "Zero-brokerage model.", "evidence": [], "confidence": "Low"},
            "Execution": {"content": "Built Kite in-house.", "evidence": [], "confidence": "Low"},
            "Results": {"content": "Profitable and growing.", "evidence": [], "confidence": "Low"},
            "Learning": {"content": "Profit over growth.", "evidence": [], "confidence": "High"},
        },
    }


def test_markdown_contains_all_six_sections():
    md = build_markdown(_final_case_study())
    for section in ["Background", "Challenge", "Strategy", "Execution", "Results", "Learning"]:
        assert f"## {section}" in md
    assert "# Business Case Study: Zerodha" in md
    assert "Confidence:" in md
    assert "Zerodha was founded in 2010" in md


def test_plain_text_contains_all_six_sections():
    txt = build_plain_text(_final_case_study())
    for section in ["BACKGROUND", "CHALLENGE", "STRATEGY", "EXECUTION", "RESULTS", "LEARNING"]:
        assert section in txt


def test_export_case_study_filenames_and_format():
    md_name, md_content = export_case_study(_final_case_study(), fmt="md")
    txt_name, txt_content = export_case_study(_final_case_study(), fmt="txt")
    assert md_name == "zerodha_case_study.md"
    assert txt_name == "zerodha_case_study.txt"
    assert md_content.startswith("#")
    assert "=" in txt_content


def test_export_handles_empty_case_study():
    empty = {"company_name": "zerodha", "case_study": {}}
    md = build_markdown(empty)
    assert "No case study sections are available." in md


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
