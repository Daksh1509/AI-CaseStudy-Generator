from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_DIR = BASE_DIR / "app"
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
OUTPUTS_DIR = BASE_DIR / "outputs"
CASE_STUDIES_DIR = OUTPUTS_DIR / "case_studies"
SUMMARIES_DIR = OUTPUTS_DIR / "summaries"
EVIDENCE_DIR = OUTPUTS_DIR / "evidence"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
REPORT_DIR = BASE_DIR / "report"
PPT_DIR = BASE_DIR / "ppt"
TESTS_DIR = BASE_DIR / "tests"

PROJECT_NAME = "AI-Powered Business Case Study Generator"