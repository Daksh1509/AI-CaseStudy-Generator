"""
references.py

Maps generated case-study sections to evidence snippets
from the original source chunks, and assigns a confidence
level per section based on evidence strength.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from src.chunk_lookup import get_chunk_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SECTION_KEY_MAP = {
    "Background": "background",
    "Challenge": "challenge",
    "Strategy": "strategy",
    "Execution": "execution",
    "Results": "results",
    "Learning Outcomes": "learning",
    "Learning": "learning",
}


def build_evidence_for_section(
    company_name: str,
    section_insights: List[Dict],
    max_snippets: int = 3,
) -> List[Dict]:
    """
    Build a list of evidence snippet records for one section.
    """
    evidence = []

    for item in section_insights[:max_snippets]:
        chunk_text = get_chunk_text(company_name, item["chunk_id"])

        snippet = chunk_text[:300].strip() + "..." if chunk_text else item["insight"]

        evidence.append({
            "chunk_id": item["chunk_id"],
            "source_id": item["source_id"],
            "source_name": item["source_name"],
            "source_type": item["source_type"],
            "snippet": snippet,
        })

    return evidence


def determine_confidence(evidence_count: int, total_insights: int) -> str:
    """
    Assign a confidence label based on how much evidence
    backs a section.
    """
    if total_insights == 0:
        return "Weak Evidence"
    if total_insights >= 4:
        return "High"
    if total_insights >= 2:
        return "Medium"
    return "Low"


def attach_evidence_to_case_study(
    company_name: str,
    case_study: Dict,
    grouped_insights: Dict,
    max_snippets: int = 3,
) -> Dict:
    """
    Take a generated case_study (section_name -> content text)
    and grouped_insights (section_key -> list of insight dicts),
    and return the final schema with content, evidence, confidence.
    """
    final_case_study = {}

    for section_name, content in case_study["case_study"].items():
        section_key = SECTION_KEY_MAP.get(section_name, section_name.lower())
        section_insights = grouped_insights.get(section_key, [])

        evidence = build_evidence_for_section(
            company_name, section_insights, max_snippets=max_snippets
        )
        confidence = determine_confidence(len(evidence), len(section_insights))

        final_case_study[section_name] = {
            "content": content,
            "evidence": evidence,
            "confidence": confidence,
        }

    return {
        "company_name": company_name,
        "case_study": final_case_study,
    }


def save_final_case_study(company_name: str, final_case_study: Dict) -> Path:
    from src.config import CASE_STUDIES_DIR

    CASE_STUDIES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CASE_STUDIES_DIR / f"{company_name.lower()}_case_study_with_evidence.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_case_study, f, indent=4, ensure_ascii=False)

    logger.info("Final case study with evidence saved to %s", output_path)
    return output_path


if __name__ == "__main__":
    from src.generator import load_insights_from_disk, generate_case_study

    company = "zerodha"

    grouped_insights = load_insights_from_disk(company)
    case_study = generate_case_study(grouped_insights, use_llm=True)

    final = attach_evidence_to_case_study(company, case_study, grouped_insights)

    print("=" * 80)
    print(f"Final Case Study with Evidence — {company}")
    print("=" * 80)

    for section, data in final["case_study"].items():
        print(f"\n[{section.upper()}] (confidence: {data['confidence']})")
        print(data["content"][:200] + "...")
        print(f"\nEvidence ({len(data['evidence'])} snippets):")
        for ev in data["evidence"]:
            print(f"  - {ev['source_name']} ({ev['chunk_id']}): {ev['snippet'][:100]}...")

    save_final_case_study(company, final)