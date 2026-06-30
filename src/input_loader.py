from pathlib import Path
from typing import List, Dict
import pdfplumber

from src.config import RAW_DATA_DIR


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".html", ".htm"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


def get_company_folder(company_name: str) -> Path:
    """
    Return the folder path for a company's raw files.
    """
    return RAW_DATA_DIR / company_name.lower()


def list_company_files(company_name: str) -> List[Path]:
    """
    List all files inside a company's raw data folder.
    """
    company_folder = get_company_folder(company_name)

    if not company_folder.exists():
        raise FileNotFoundError(f"Company folder not found: {company_folder}")

    return sorted([file for file in company_folder.iterdir() if file.is_file()])


def read_text_file(file_path: Path) -> str:
    """
    Read plain text or HTML files.
    """
    return file_path.read_text(encoding="utf-8", errors="ignore")


def read_pdf_file(file_path: Path) -> str:
    """
    Extract text from PDF using pdfplumber.
    """
    extracted_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text.append(page_text)

    return "\n".join(extracted_text)


def detect_source_type(file_path: Path) -> str:
    """
    Infer a simple source type from filename keywords.
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


def load_single_file(company_name: str, file_path: Path, source_id: str) -> Dict:
    """
    Load one file and return it in a common structured format.
    """
    extension = file_path.suffix.lower()

    if extension in SUPPORTED_TEXT_EXTENSIONS:
        text = read_text_file(file_path)
    elif extension in SUPPORTED_PDF_EXTENSIONS:
        text = read_pdf_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.name}")

    return {
        "company_name": company_name.lower(),
        "source_id": source_id,
        "source_type": detect_source_type(file_path),
        "source_name": file_path.name,
        "file_path": str(file_path),
        "text": text.strip()
    }


def load_company_documents(company_name: str) -> List[Dict]:
    """
    Load all supported files for a company and return structured document records.
    """
    files = list_company_files(company_name)
    documents = []

    for index, file_path in enumerate(files, start=1):
        source_id = f"src_{index:02d}"

        try:
            document = load_single_file(company_name, file_path, source_id)
            documents.append(document)
        except Exception as error:
            print(f"Skipping {file_path.name}: {error}")

    return documents