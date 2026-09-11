from pathlib import Path
from typing import List, Dict
import logging
from src.preprocess import preprocess_text
from bs4 import BeautifulSoup
import fitz

import pdfplumber

from src.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".html", ".htm"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


def get_company_folder(company_name: str) -> Path:
    """
    Return the raw data folder for a company.
    """
    return RAW_DATA_DIR / company_name.lower()


def list_company_files(company_name: str) -> List[Path]:
    """
    Return all supported files inside the company's raw data folder.
    """
    company_folder = get_company_folder(company_name)

    if not company_folder.exists():
        raise FileNotFoundError(f"Company folder not found: {company_folder}")

    return sorted(
        [
            file
            for file in company_folder.iterdir()
            if file.is_file()
        ]
    )

def read_pdf_file_fitz(file_path: Path) -> str:
    """
    Extract text using PyMuPDF, which handles font encoding
    issues (e.g. reversed glyph order) better than pdfplumber
    for some PDFs.
    """
    extracted_text = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            page_text = page.get_text()
            if page_text:
                extracted_text.append(page_text)
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to extract PDF '{file_path.name}' with fitz: {e}")

    return "\n".join(extracted_text).strip()

def read_text_file(file_path: Path) -> str:
    """
    Read a plain text or HTML file.
    """
    try:
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:
        raise RuntimeError(
            f"Failed to read text file '{file_path.name}': {e}"
        )


def read_pdf_file(file_path: Path) -> str:
    """
    Extract text from a PDF using pdfplumber.
    """
    extracted_text = []

    try:
        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    extracted_text.append(page_text)

    except Exception as e:
        raise RuntimeError(
            f"Failed to extract PDF '{file_path.name}': {e}"
        )

    return "\n".join(extracted_text).strip()


def extract_pdf_metadata(file_path: Path) -> Dict:
    """
    Extract useful metadata from a PDF.
    """
    try:
        with pdfplumber.open(file_path) as pdf:

            return {
                "page_count": len(pdf.pages)
            }

    except Exception:
        return {
            "page_count": 0
        }


def detect_source_type(file_path: Path) -> str:
    """
    Infer a source type from the filename.
    """
    name = file_path.name.lower()

    if "annual_report" in name:
        return "annual_report"

    if "annual_return" in name:
        return "annual_return"

    if "investor_presentation" in name:
        return "investor_presentation"

    if "open_source" in name or "report" in name:
        return "report"

    if "about" in name:
        return "official_page"

    if "success_story" in name or "origin_story" in name:
        return "founder_story"

    if "businessline" in name or "news" in name:
        return "news_article"

    if "case_study" in name:
        return "case_study"

    if "narrative" in name or "secrets" in name:
        return "narrative_summary"

    return "other"

def strip_html(raw_html: str) -> str:
    """Extract visible text content from an HTML file."""
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return text

def load_single_file(
    company_name: str,
    file_path: Path,
    source_id: str
) -> Dict:
    """
    Load one supported file and return it in the
    common project data format.
    """

    extension = file_path.suffix.lower()

    metadata = {}
    if extension == ".html" or extension == ".htm":
        raw_text = read_text_file(file_path)
        text = preprocess_text(strip_html(raw_text))
    elif extension == ".txt":
        text = preprocess_text(read_text_file(file_path))

    elif extension in SUPPORTED_PDF_EXTENSIONS:
        text = preprocess_text(read_pdf_file_fitz(file_path))
        metadata = extract_pdf_metadata(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {file_path.name}"
        )

    if len(text.strip()) < 50:
        logger.warning(
            "Weak extraction: %s produced only %d characters of text.",
            file_path.name,
            len(text.strip()),
        )

    return {
        "company_name": company_name.lower(),
        "source_id": source_id,
        "source_type": detect_source_type(file_path),
        "source_name": file_path.name,
        "file_path": str(file_path),

        # Filled in by chunker.py later
        "chunk_id": None,

        # Useful metadata
        "metadata": metadata,

        # Raw extracted text
        "text": text.strip()
    }


def load_company_documents(company_name: str) -> List[Dict]:
    """
    Load every supported file belonging to a company.
    """

    files = list_company_files(company_name)

    documents = []

    for index, file_path in enumerate(files, start=1):

        source_id = f"src_{index:02d}"

        try:
            document = load_single_file(
                company_name,
                file_path,
                source_id
            )

            documents.append(document)

        except Exception as error:
            logger.warning(
                "Skipping %s: %s",
                file_path.name,
                error
            )

    return documents


if __name__ == "__main__":
    print("Starting input loader test...")

    company = "infosys"      # Change to your folder name

    docs = load_company_documents(company)

    print(f"\nLoaded {len(docs)} documents\n")

    for doc in docs:

        print("=" * 70)

        print(f"Company      : {doc['company_name']}")
        print(f"Source ID    : {doc['source_id']}")
        print(f"Source Type  : {doc['source_type']}")
        print(f"Source Name  : {doc['source_name']}")
        print(f"Metadata     : {doc['metadata']}")

        print("\nPreview:\n")

        print(doc["text"][:500])

        print("\n")