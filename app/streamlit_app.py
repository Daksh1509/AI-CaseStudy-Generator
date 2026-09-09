"""
streamlit_app.py

End-to-end Streamlit interface for the AI-Powered Business Case
Study Generator.

Input side  (Student A):
    - company selector / name input
    - file upload (PDF / HTML / TXT)
    - pasted-text input
    - "Generate Case Study" button
    - input validation messages

Pipeline wiring (Day 10 integration):
    input_loader/preprocess -> chunker -> summarizer
    -> insight_extractor -> generator -> references

Output side (Student B):
    - section-by-section generated content
    - per-section confidence badge
    - per-section evidence snippets
    - Markdown / text download (export_utils)

Nothing here renames or restructures any existing module contract.
It only calls the existing functions in order.
"""

import tempfile
from pathlib import Path

import streamlit as st

from src.config import CASE_STUDIES_DIR

# Input side
from src.input_loader import load_company_documents, load_single_file
from src.preprocess import preprocess_text

# Pipeline
from src.chunker import chunk_documents, save_chunks_to_disk
from src.summarizer import summarize_chunks, save_summaries_to_disk
from src.insight_extractor import (
    extract_all_insights,
    group_insights,
    save_insights_to_disk,
)
from src.generator import generate_case_study
from src.references import (
    attach_evidence_to_case_study,
    save_final_case_study,
)
import src.chunk_lookup as chunk_lookup

# Export
from src.export_utils import export_case_study


# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="AI Case Study Generator",
    page_icon="📚",
    layout="wide",
)


# ==========================================================
# Case Study Configuration
# ==========================================================

# NOTE: the sixth section key produced by the pipeline is "Learning"
# (generator.py -> references.py). It must match exactly here, or the
# section is silently dropped from the display.
SECTION_ORDER = [
    "Background",
    "Challenge",
    "Strategy",
    "Execution",
    "Results",
    "Learning",
]

BUILT_IN_COMPANIES = ["Zerodha", "Infosys", "Nykaa"]

SUPPORTED_UPLOAD_TYPES = ["pdf", "html", "htm", "txt"]


# ==========================================================
# Input builders
# ==========================================================

def build_documents_from_company(company_name: str):
    """
    Load all built-in raw documents for one of the demo companies
    from data/raw/{company}/.
    """
    return load_company_documents(company_name)


def build_documents_from_uploads(company_name: str, uploaded_files):
    """
    Save each uploaded file to a temporary path and load it through
    the same input_loader used for built-in files, so the document
    dicts follow the exact same contract.
    """
    documents = []
    temp_dir = Path(tempfile.mkdtemp(prefix="case_study_uploads_"))

    for index, uploaded in enumerate(uploaded_files, start=1):
        source_id = f"src_{index:02d}"
        temp_path = temp_dir / uploaded.name

        with open(temp_path, "wb") as file:
            file.write(uploaded.getbuffer())

        try:
            document = load_single_file(company_name, temp_path, source_id)
            documents.append(document)
        except Exception as error:
            st.warning(f"Skipped '{uploaded.name}': {error}")

    return documents


def build_document_from_text(company_name: str, pasted_text: str):
    """
    Wrap pasted text into a single document dict that matches the
    shared contract, so it flows through the rest of the pipeline
    unchanged.
    """
    cleaned = preprocess_text(pasted_text)

    document = {
        "company_name": company_name.lower(),
        "source_id": "src_01",
        "source_type": "pasted_text",
        "source_name": "pasted_text.txt",
        "file_path": "",
        "chunk_id": None,
        "metadata": {},
        "text": cleaned.strip(),
    }
    return [document]


# ==========================================================
# Pipeline orchestration
# ==========================================================

def run_full_pipeline(company_name, documents, use_llm=True, progress=None):
    """
    Run the complete pipeline for one company and return the final
    case study dict (schema from references.py).

    progress: optional callable(step_index, total_steps, message)
              used to drive a Streamlit progress bar.
    """
    total_steps = 6

    def step(index, message):
        if progress is not None:
            progress(index, total_steps, message)

    if not documents:
        raise ValueError(
            "No readable documents were found. "
            "Check the files or pasted text and try again."
        )

    # 1) Chunk + persist (chunks are required later for evidence lookup)
    step(1, "Chunking documents...")
    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError("Chunking produced no text chunks.")
    save_chunks_to_disk(company_name, chunks)

    # 2) Summarize + persist
    step(2, "Summarizing chunks...")
    summaries = summarize_chunks(chunks, use_llm=use_llm)
    save_summaries_to_disk(company_name, summaries)

    # 3) Insights + group + persist
    step(3, "Extracting insights...")
    insights = extract_all_insights(summaries, use_llm=use_llm)
    grouped_insights = group_insights(insights)
    save_insights_to_disk(company_name, grouped_insights)

    # 4) Generate section text
    step(4, "Generating case study sections...")
    case_study = generate_case_study(grouped_insights, use_llm=use_llm)

    # 5) Attach evidence + confidence
    step(5, "Attaching evidence and confidence...")
    # Clear any stale cached chunks so evidence reflects THIS run's chunks.
    chunk_lookup._chunk_cache.clear()
    final_case_study = attach_evidence_to_case_study(
        company_name, case_study, grouped_insights
    )

    # 6) Persist final
    step(6, "Saving final case study...")
    save_final_case_study(company_name, final_case_study)

    return final_case_study


# ==========================================================
# Output display (Student B — Day 9 display, preserved)
# ==========================================================

def display_confidence(confidence: str):
    """Display the evidence confidence level as a coloured badge."""
    if confidence == "High":
        st.success(f"Evidence confidence: {confidence}")
    elif confidence == "Medium":
        st.info(f"Evidence confidence: {confidence}")
    elif confidence in {"Low", "Weak Evidence"}:
        st.warning(f"Evidence confidence: {confidence}")
    else:
        st.caption(f"Evidence confidence: {confidence}")


def display_evidence(evidence):
    """Display supporting evidence snippets for a section."""
    st.markdown("**Evidence**")

    if not evidence:
        st.warning("No supporting evidence was found for this section.")
        return

    for index, item in enumerate(evidence, start=1):
        source_name = item.get("source_name", "Unknown source")

        with st.expander(f"Evidence {index}: {source_name}"):
            st.write(item.get("snippet", "No snippet available."))
            st.caption(f"Source ID: {item.get('source_id', 'N/A')}")
            st.caption(f"Source Type: {item.get('source_type', 'N/A')}")
            st.caption(f"Chunk ID: {item.get('chunk_id', 'N/A')}")


def display_case_study(final_case_study):
    """
    Display the complete case study section by section, including
    generated content, confidence, and evidence.
    """
    company_name = final_case_study.get("company_name", "Unknown Company")
    st.header(f"Case Study: {company_name.title()}")

    case_study = final_case_study.get("case_study", {})

    if not case_study:
        st.warning("No case study sections are available.")
        return

    for section_name in SECTION_ORDER:
        section_data = case_study.get(section_name)

        if not section_data:
            continue

        content = section_data.get("content", "")
        evidence = section_data.get("evidence", [])
        confidence = section_data.get("confidence", "Unknown")

        st.subheader(section_name)
        display_confidence(confidence)

        if content:
            st.write(content)
        else:
            st.warning("No generated content is available for this section.")

        display_evidence(evidence)
        st.divider()


def render_download_buttons(final_case_study):
    """Offer Markdown and plain-text downloads of the case study."""
    st.subheader("Export")

    md_name, md_content = export_case_study(final_case_study, fmt="md")
    txt_name, txt_content = export_case_study(final_case_study, fmt="txt")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="Download as Markdown (.md)",
            data=md_content,
            file_name=md_name,
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            label="Download as text (.txt)",
            data=txt_content,
            file_name=txt_name,
            mime="text/plain",
            use_container_width=True,
        )


# ==========================================================
# Application Title
# ==========================================================

st.title("AI-Powered Business Case Study Generator")
st.write(
    "Generate structured, source-backed business case studies. "
    "Every section is grounded in real evidence with a confidence rating."
)


# ==========================================================
# Sidebar — Input side (Student A)
# ==========================================================

st.sidebar.header("Input")

input_mode = st.sidebar.radio(
    "Choose input source",
    ["Built-in company", "Upload files", "Paste text"],
)

# Defaults so validation logic below always has values.
selected_company = None
uploaded_files = None
pasted_text = ""
company_name_input = ""

if input_mode == "Built-in company":
    selected_company = st.sidebar.selectbox(
        "Select company",
        BUILT_IN_COMPANIES,
    )

elif input_mode == "Upload files":
    company_name_input = st.sidebar.text_input(
        "Company name",
        placeholder="e.g. Infosys",
    )
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF / HTML / TXT files",
        type=SUPPORTED_UPLOAD_TYPES,
        accept_multiple_files=True,
    )

else:  # Paste text
    company_name_input = st.sidebar.text_input(
        "Company name",
        placeholder="e.g. Infosys",
    )
    pasted_text = st.sidebar.text_area(
        "Paste company text here",
        height=220,
        placeholder="Paste an article, report extract, or notes...",
    )

use_llm = st.sidebar.checkbox(
    "Use Groq LLM (uncheck for offline demo)",
    value=True,
    help=(
        "When checked, sections are written by the Groq model and require "
        "GROQ_API_KEY in your .env. Uncheck to run a fast offline demo that "
        "uses deterministic fallback text and still shows real evidence."
    ),
)

generate_button = st.sidebar.button(
    "Generate Case Study",
    type="primary",
    use_container_width=True,
)


# ==========================================================
# Input validation
# ==========================================================

def validate_inputs():
    """
    Return (is_valid, company_name, build_fn) or (False, None, None).
    Emits Streamlit error/warning messages on failure.
    """
    if input_mode == "Built-in company":
        if not selected_company:
            st.error("Please select a company.")
            return False, None, None
        company = selected_company.lower()
        return True, company, lambda: build_documents_from_company(company)

    if input_mode == "Upload files":
        if not company_name_input.strip():
            st.error("Please enter a company name.")
            return False, None, None
        if not uploaded_files:
            st.error("Please upload at least one PDF, HTML, or TXT file.")
            return False, None, None
        company = company_name_input.strip().lower()
        return True, company, lambda: build_documents_from_uploads(
            company, uploaded_files
        )

    # Paste text
    if not company_name_input.strip():
        st.error("Please enter a company name.")
        return False, None, None
    if len(pasted_text.strip()) < 100:
        st.error(
            "Please paste more text (at least ~100 characters) so the "
            "pipeline has enough to work with."
        )
        return False, None, None
    company = company_name_input.strip().lower()
    return True, company, lambda: build_document_from_text(company, pasted_text)


# ==========================================================
# Main flow
# ==========================================================

if generate_button:
    is_valid, company, build_documents = validate_inputs()

    if is_valid:
        progress_bar = st.progress(0, text="Starting...")

        def update_progress(step_index, total_steps, message):
            progress_bar.progress(
                step_index / total_steps,
                text=f"Step {step_index}/{total_steps}: {message}",
            )

        try:
            with st.spinner("Running the pipeline..."):
                documents = build_documents()
                final_case_study = run_full_pipeline(
                    company,
                    documents,
                    use_llm=use_llm,
                    progress=update_progress,
                )

            progress_bar.progress(1.0, text="Done.")

            # Persist in session so re-runs (e.g. clicking download) keep it.
            st.session_state["final_case_study"] = final_case_study
            st.success(f"Case study generated for {company.title()}.")

        except ValueError as error:
            progress_bar.empty()
            st.error(f"Input problem: {error}")

        except Exception as error:
            progress_bar.empty()
            st.error(
                "The pipeline failed while generating the case study."
            )
            st.info(
                "Common causes: missing GROQ_API_KEY in .env, a Groq rate "
                "limit or API outage, or an unreadable source file. You can "
                "uncheck 'Use Groq LLM' to run an offline demo."
            )
            st.exception(error)


# ==========================================================
# Render the latest result (if any)
# ==========================================================

if "final_case_study" in st.session_state:
    final_case_study = st.session_state["final_case_study"]
    display_case_study(final_case_study)
    render_download_buttons(final_case_study)

elif not generate_button:
    st.info(
        "Pick an input source in the sidebar, then click "
        "'Generate Case Study' to build an evidence-backed case study."
    )
