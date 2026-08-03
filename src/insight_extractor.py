"""
insight_extractor.py

Reads chunk summaries and extracts structured business insights
for downstream case-study generation.

Each summary is classified into exactly one of the following
business case sections:

- Background
- Challenge
- Strategy
- Execution
- Results
- Learning

The output preserves source metadata so evidence mapping
can be performed later.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List

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

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Please check your .env file."
            )

        _client = Groq(api_key=api_key)

    return _client


# ==========================================================
# Prompt Builder
# ==========================================================

def build_extraction_prompt(summary_record: Dict) -> str:
    """
    Prompt for classifying one summary into exactly one
    business-case section.
    """

    return f"""
You are an expert business case-study analyst.

Your task is to read the company summary below.

Classify it into EXACTLY ONE of these sections:

- Background
- Challenge
- Strategy
- Execution
- Results
- Learning

Rules:

1. Choose only ONE section.

2. Rewrite the summary into one concise business insight.

3. Do NOT invent facts.

4. Use only information present.

5. Return ONLY valid JSON.

Expected format:

{{
    "section":"Strategy",
    "insight":"The company adopted a flat brokerage pricing model."
}}

Company:
{summary_record["company_name"]}

Summary:
{summary_record["summary"]}
"""


# ==========================================================
# LLM Call
# ==========================================================

def call_llm(prompt: str) -> str:
    """
    Call Groq Llama model.
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

        temperature=0.2,

        max_tokens=250,
    )

    return response.choices[0].message.content.strip()


# ==========================================================
# JSON Parsing
# ==========================================================

def parse_json_response(response_text: str) -> Dict:
    """
    Parse LLM JSON safely.
    """

    try:

        start = response_text.find("{")
        end = response_text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found.")

        json_text = response_text[start:end + 1]

        return json.loads(json_text)

    except Exception as error:

        logger.warning(
            "Failed to parse JSON response: %s",
            error
        )

        return {
            "section": "Learning",
            "insight": response_text.strip()
        }


# ==========================================================
# Extract One Insight
# ==========================================================

def extract_single_insight(summary_record: Dict,
                           use_llm: bool = True) -> Dict:
    """
    Convert one summary into one structured insight.
    """

    prompt = build_extraction_prompt(summary_record)

    if use_llm:

        try:

            response = call_llm(prompt)

            parsed = parse_json_response(response)

        except Exception as error:

            logger.warning(
                "LLM failed for %s : %s",
                summary_record["chunk_id"],
                error
            )

            parsed = {
                "section": "Learning",
                "insight": summary_record["summary"]
            }

    else:

        parsed = {
            "section": "Learning",
            "insight": summary_record["summary"]
        }

    return {

        "company_name":
            summary_record["company_name"],

        "source_id":
            summary_record["source_id"],

        "source_type":
            summary_record["source_type"],

        "source_name":
            summary_record["source_name"],

        "chunk_id":
            summary_record["chunk_id"],

        "section":
            parsed["section"].strip().lower(),

        "insight":
            parsed["insight"].strip(),

        "keywords":
            summary_record["keywords"]
    }


# ==========================================================
# Extract Insights From All Summaries
# ==========================================================

def extract_all_insights(
    summaries: List[Dict],
    use_llm: bool = True
) -> List[Dict]:
    """
    Extract structured insights from all summaries.
    """

    insights = []

    total = len(summaries)

    logger.info("Processing %d summaries...", total)

    for index, summary in enumerate(summaries, start=1):

        try:

            logger.info(
                "Extracting insight %d/%d",
                index,
                total,
            )

            insight = extract_single_insight(
                summary,
                use_llm=use_llm,
            )

            insights.append(insight)

        except Exception as error:

            logger.warning(
                "Failed to process %s : %s",
                summary.get("chunk_id"),
                error,
            )

    logger.info("Finished extracting insights.")

    return insights


# ==========================================================
# Group Insights By Business Section
# ==========================================================

def group_insights(insights: List[Dict]) -> Dict:
    """
    Group insights into the six business case sections.
    """

    if not insights:
        return {}

    grouped = {

        "company_name": insights[0]["company_name"],

        "background": [],

        "challenge": [],

        "strategy": [],

        "execution": [],

        "results": [],

        "learning": [],
    }

    valid_sections = {

        "background",

        "challenge",

        "strategy",

        "execution",

        "results",

        "learning",
    }

    for insight in insights:

        section = insight["section"].lower()

        if section not in valid_sections:

            logger.warning(
                "Unknown section '%s'. Moving to learning.",
                section,
            )

            section = "learning"

        grouped[section].append(

            {

                "chunk_id": insight["chunk_id"],

                "source_id": insight["source_id"],

                "source_type": insight["source_type"],

                "source_name": insight["source_name"],

                "insight": insight["insight"],

                "keywords": insight["keywords"],
            }

        )

    return grouped


# ==========================================================
# Save Insights
# ==========================================================

def save_insights_to_disk(
    company_name: str,
    grouped_insights: Dict,
) -> Path:
    """
    Save grouped insights to outputs/insights/.
    """

    from src.config import BASE_DIR

    output_dir = BASE_DIR / "outputs" / "insights"

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / f"{company_name.lower()}_insights.json"

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            grouped_insights,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info("Insights saved to %s", output_path)

    return output_path


# ==========================================================
# Load Saved Summaries
# ==========================================================

def load_summaries_from_disk(
    company_name: str,
) -> List[Dict]:
    """
    Load summaries generated by summarizer.py.
    """

    from src.config import BASE_DIR

    summary_file = (

        BASE_DIR
        / "outputs"
        / "summaries"
        / f"{company_name.lower()}_summaries.json"

    )

    if not summary_file.exists():

        raise FileNotFoundError(

            f"Summary file not found: {summary_file}"

        )

    with open(

        summary_file,

        "r",

        encoding="utf-8",

    ) as file:

        summaries = json.load(file)

    logger.info(

        "Loaded %d summaries.",

        len(summaries),

    )

    return summaries

# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    company = "zerodha"

    print("=" * 80)
    print(f"Loading summaries for {company}...")
    print("=" * 80)

    summaries = load_summaries_from_disk(company)

    print(f"\nLoaded {len(summaries)} summaries.\n")

    insights = extract_all_insights(
        summaries,
        use_llm=True,
    )

    print(f"\nExtracted {len(insights)} insights.\n")

    grouped = group_insights(insights)

    print("=" * 80)
    print("Business Insight Distribution")
    print("=" * 80)

    sections = [
        "background",
        "challenge",
        "strategy",
        "execution",
        "results",
        "learning",
    ]

    for section in sections:

        count = len(grouped.get(section, []))

        print(f"{section.capitalize():12}: {count}")

    print("\n")

    print("=" * 80)
    print("Sample Insights")
    print("=" * 80)

    for section in sections:

        values = grouped.get(section, [])

        if not values:
            continue

        print(f"\n[{section.upper()}]\n")

        for item in values[:2]:

            print(f"- {item['insight']}")

    output_path = save_insights_to_disk(
        company,
        grouped,
    )

    print("\n")
    print("=" * 80)
    print(f"Insights saved to:\n{output_path}")
    print("=" * 80)