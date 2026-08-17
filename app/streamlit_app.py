"""
streamlit_app.py

Streamlit interface for displaying generated business
case studies with supporting evidence and confidence levels.
"""

import json
from pathlib import Path

import streamlit as st

from src.config import CASE_STUDIES_DIR


# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="AI Case Study Generator",
    page_icon="📚",
    layout="wide",
)


# ==========================================================
# Application Title
# ==========================================================

st.title("AI-Powered Business Case Study Generator")

st.write(
    "Generate and review structured business case studies "
    "with source-backed evidence."
)


# ==========================================================
# Case Study Configuration
# ==========================================================

SECTION_ORDER = [
    "Background",
    "Challenge",
    "Strategy",
    "Execution",
    "Results",
    "Learning Outcomes",
]


# ==========================================================
# Load Case Study
# ==========================================================

def load_case_study(company_name: str):
    """
    Load the final case study with evidence from disk.
    """

    file_path = (
        CASE_STUDIES_DIR
        / f"{company_name.lower()}_case_study_with_evidence.json"
    )

    if not file_path.exists():
        return None

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except json.JSONDecodeError as error:

        st.error(
            f"Could not read the case study JSON: {error}"
        )

        return None


# ==========================================================
# Display Evidence
# ==========================================================

def display_evidence(evidence):
    """
    Display supporting evidence snippets for a section.
    """

    st.markdown("**Evidence**")

    if not evidence:

        st.warning(
            "No supporting evidence was found for this section."
        )

        return

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        source_name = item.get(
            "source_name",
            "Unknown source",
        )

        with st.expander(
            f"Evidence {index}: {source_name}"
        ):

            st.write(
                item.get(
                    "snippet",
                    "No snippet available.",
                )
            )

            st.caption(
                f"Source ID: "
                f"{item.get('source_id', 'N/A')}"
            )

            st.caption(
                f"Source Type: "
                f"{item.get('source_type', 'N/A')}"
            )

            st.caption(
                f"Chunk ID: "
                f"{item.get('chunk_id', 'N/A')}"
            )


# ==========================================================
# Display Confidence
# ==========================================================

def display_confidence(confidence: str):
    """
    Display the evidence confidence level.
    """

    if confidence == "High":

        st.success(
            f"Evidence confidence: {confidence}"
        )

    elif confidence == "Medium":

        st.info(
            f"Evidence confidence: {confidence}"
        )

    elif confidence in {
        "Low",
        "Weak Evidence",
    }:

        st.warning(
            f"Evidence confidence: {confidence}"
        )

    else:

        st.caption(
            f"Evidence confidence: {confidence}"
        )


# ==========================================================
# Display Case Study
# ==========================================================

def display_case_study(final_case_study):
    """
    Display the complete case study section by section,
    including generated content, evidence and confidence.
    """

    company_name = final_case_study.get(
        "company_name",
        "Unknown Company",
    )

    st.header(
        f"Case Study: {company_name}"
    )

    case_study = final_case_study.get(
        "case_study",
        {},
    )

    if not case_study:

        st.warning(
            "No case study sections are available."
        )

        return

    for section_name in SECTION_ORDER:

        section_data = case_study.get(
            section_name
        )

        if not section_data:
            continue

        content = section_data.get(
            "content",
            "",
        )

        evidence = section_data.get(
            "evidence",
            [],
        )

        confidence = section_data.get(
            "confidence",
            "Unknown",
        )

        # --------------------------------------------------
        # Section Heading
        # --------------------------------------------------

        st.subheader(section_name)

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        display_confidence(confidence)

        # --------------------------------------------------
        # Generated Content
        # --------------------------------------------------

        if content:

            st.write(content)

        else:

            st.warning(
                "No generated content is available "
                "for this section."
            )

        # --------------------------------------------------
        # Supporting Evidence
        # --------------------------------------------------

        display_evidence(evidence)

        st.divider()


# ==========================================================
# Sidebar
# ==========================================================

st.sidebar.header("Case Study")

company_name = st.sidebar.selectbox(
    "Select company",
    [
        "Zerodha",
        "Infosys",
        "Nykaa",
    ],
)


# ==========================================================
# Load Button
# ==========================================================

load_button = st.sidebar.button(
    "Load Case Study",
    use_container_width=True,
)


# ==========================================================
# Main Application
# ==========================================================

if load_button:

    final_case_study = load_case_study(
        company_name
    )

    if final_case_study is None:

        expected_file = (
            CASE_STUDIES_DIR
            / f"{company_name.lower()}_case_study_with_evidence.json"
        )

        st.error(
            "Case study with evidence was not found."
        )

        st.info(
            f"Expected file:\n{expected_file}"
        )

    else:

        display_case_study(
            final_case_study
        )

else:

    st.info(
        "Select a company from the sidebar "
        "and click 'Load Case Study' to view "
        "the generated case study."
    )