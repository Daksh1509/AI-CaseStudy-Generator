"""
generator.py

Generates a structured business case study from grouped
business insights extracted in Day 6.

Input:
outputs/insights/<company>_insights.json

Output:
outputs/case_studies/<company>_case_study.json
"""

import os
import json
import logging

from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

_client = None


# ==========================================================
# Groq Client
# ==========================================================

def get_client():
    """
    Lazily initialize the Groq client.
    """

    global _client

    if _client is None:

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY not found."
            )

        _client = Groq(api_key=api_key)

    return _client


# ==========================================================
# Prompt Builder
# ==========================================================

def build_generation_prompt(
    section_name: str,
    section_insights: list
) -> str:
    """
    Build the prompt for generating one business case
    section.
    """

    insight_text = "\n".join(

        f"- {item['insight']}"

        for item in section_insights

    )

    return f"""
You are an expert business case writer.

Write ONLY the "{section_name}" section of a business case study.

Guidelines:

• Use only the supplied insights.

• Never invent facts.

• Never assume missing information.

• Professional business-school writing style.

• Avoid repetition.

• Do not mention that these are insights.

• Write as continuous prose.

• Around 150–250 words.

Insights:

{insight_text}

Return ONLY the paragraph.
"""


# ==========================================================
# LLM Call
# ==========================================================

def call_llm(prompt: str) -> str:
    """
    Generate text using Groq.
    """

    client = get_client()

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],

        temperature=0.3,

        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


# ==========================================================
# Generate One Section
# ==========================================================

def generate_section(
    section_name: str,
    section_insights: list,
    use_llm: bool = True
) -> str:
    """
    Generate one case-study section.
    """

    if not section_insights:

        logger.warning(
            "No insights found for %s.",
            section_name,
        )

        return "No sufficient evidence available."

    prompt = build_generation_prompt(

        section_name,

        section_insights,

    )

    if use_llm:

        try:

            return call_llm(prompt)

        except Exception as error:

            logger.warning(

                "Generation failed for %s : %s",

                section_name,

                error,

            )

    return "\n".join(

        item["insight"]

        for item in section_insights

    )
# ==========================================================
# Generate Complete Case Study
# ==========================================================

def generate_case_study(
    grouped_insights: Dict,
    use_llm: bool = True,
) -> Dict:
    """
    Generate a complete business case study from grouped insights.
    """

    logger.info(
        "Generating case study for %s...",
        grouped_insights["company_name"],
    )

    sections = [

        ("Background", "background"),

        ("Challenge", "challenge"),

        ("Strategy", "strategy"),

        ("Execution", "execution"),

        ("Results", "results"),

        ("Learning", "learning"),
    ]

    case_study = {}

    for display_name, key in sections:

        logger.info(
            "Generating section: %s",
            display_name,
        )

        case_study[display_name] = generate_section(

            display_name,

            grouped_insights.get(key, []),

            use_llm=use_llm,

        )

    return {

        "company_name": grouped_insights["company_name"],

        "case_study": case_study,
    }


# ==========================================================
# Load Insights
# ==========================================================

def load_insights_from_disk(
    company_name: str,
) -> Dict:
    """
    Load grouped insights produced by insight_extractor.py
    """

    from src.config import BASE_DIR

    insights_path = (

        BASE_DIR
        / "outputs"
        / "insights"
        / f"{company_name.lower()}_insights.json"

    )

    if not insights_path.exists():

        raise FileNotFoundError(

            f"Insights file not found: {insights_path}"

        )

    with open(

        insights_path,

        "r",

        encoding="utf-8",

    ) as file:

        insights = json.load(file)

    logger.info(

        "Loaded grouped insights for %s",

        company_name,

    )

    return insights


# ==========================================================
# Save Case Study
# ==========================================================

def save_case_study_to_disk(
    company_name: str,
    case_study: Dict,
) -> Path:
    """
    Save generated case study to outputs/case_studies/.
    """

    from src.config import CASE_STUDIES_DIR

    CASE_STUDIES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CASE_STUDIES_DIR
        / f"{company_name.lower()}_case_study.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            case_study,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info(
        "Case study saved to %s",
        output_path,
    )

    return output_path
    
# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    company = "zerodha"

    print("=" * 80)
    print(f"Loading insights for {company}...")
    print("=" * 80)

    insights = load_insights_from_disk(company)

    print("\nLoaded grouped insights.\n")

    case_study = generate_case_study(
        insights,
        use_llm=True,
    )

    print("=" * 80)
    print("Generated Case Study")
    print("=" * 80)

    for section, content in case_study["case_study"].items():

        print(f"\n[{section.upper()}]\n")

        preview = content.strip()

        if len(preview) > 300:
            preview = preview[:300] + "..."

        print(preview)

    output_path = save_case_study_to_disk(
        company,
        case_study,
    )

    print("\n")
    print("=" * 80)
    print("Generation Complete")
    print("=" * 80)
    print(f"Company : {company}")
    print(f"Output  : {output_path}")
    print("=" * 80)