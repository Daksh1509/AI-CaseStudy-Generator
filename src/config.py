from pathlib import Path
from dotenv import load_dotenv

# ==========================================================
# Base Project Paths
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

PROJECT_NAME = "AI-Powered Business Case Study Generator"

# ==========================================================
# Source Directories
# ==========================================================

APP_DIR = BASE_DIR / "app"
SRC_DIR = BASE_DIR / "src"

# ==========================================================
# Data Directories
# ==========================================================

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"

# ==========================================================
# Output Directories
# ==========================================================

OUTPUTS_DIR = BASE_DIR / "outputs"

SUMMARIES_DIR = OUTPUTS_DIR / "summaries"
INSIGHTS_DIR = OUTPUTS_DIR / "insights"
CASE_STUDIES_DIR = OUTPUTS_DIR / "case_studies"
EVIDENCE_DIR = OUTPUTS_DIR / "evidence"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"

# ==========================================================
# Other Project Directories
# ==========================================================

NOTEBOOKS_DIR = BASE_DIR / "notebooks"
REPORT_DIR = BASE_DIR / "report"
PPT_DIR = BASE_DIR / "ppt"
TESTS_DIR = BASE_DIR / "tests"