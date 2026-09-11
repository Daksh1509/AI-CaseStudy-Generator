"""
test_generator.py

Unit tests for src/generator.py.

All tests run offline (use_llm=False), so no Groq API key is required.
"""

from src.generator import generate_section, generate_case_study


DISPLAY_SECTIONS = [
    "Background",
    "Challenge",
    "Strategy",
    "Execution",
    "Results",
    "Learning",
]


def _insight(section_key, text):
    return {
        "chunk_id": f"src_01_chunk_00{section_key[0]}",
        "source_id": "src_01",
        "source_type": "report",
        "source_name": "about.html",
        "insight": text,
        "keywords": ["zerodha"],
    }


def test_generate_section_empty_returns_no_evidence_message():
    result = generate_section("Background", [], use_llm=False)
    assert result == "No sufficient evidence available."


def test_generate_section_offline_uses_insights():
    insights = [_insight("background", "Zerodha was bootstrapped without VC funding.")]
    result = generate_section("Background", insights, use_llm=False)
    assert "bootstrapped" in result
    assert result != "No sufficient evidence available."


def test_generate_case_study_returns_all_six_sections():
    grouped = {
        "company_name": "zerodha",
        "background": [_insight("background", "Bootstrapped brokerage.")],
        "challenge": [],
        "strategy": [_insight("strategy", "Zero-brokerage on equity delivery.")],
        "execution": [],
        "results": [],
        "learning": [_insight("learning", "Focus on profitability over growth.")],
    }
    case = generate_case_study(grouped, use_llm=False)

    assert case["company_name"] == "zerodha"
    assert list(case["case_study"].keys()) == DISPLAY_SECTIONS

    assert case["case_study"]["Background"] != "No sufficient evidence available."
    assert case["case_study"]["Challenge"] == "No sufficient evidence available."
    assert case["case_study"]["Results"] == "No sufficient evidence available."


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
