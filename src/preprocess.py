"""
preprocess.py

Utilities for cleaning extracted text from PDFs, reports,
HTML pages, and text documents before chunking and
LLM processing.
"""

import logging
import re

logger = logging.getLogger(__name__)


def normalize_unicode(text: str) -> str:
    """Replace common unicode characters with ASCII equivalents."""
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\u2026": "...",
        "\u00A0": " ",
        "\t": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def remove_page_numbers(text: str) -> str:
    """Remove standalone page numbers and common page labels."""
    lines = text.splitlines()
    cleaned = []
    page_pattern = re.compile(r"^\s*(page\s*)?\d+\s*$", re.IGNORECASE)

    for line in lines:
        if page_pattern.match(line.strip()):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def remove_headers_footers(text: str) -> str:
    """Remove repeated document headers and footers (conservative)."""
    lines = text.splitlines()
    frequency = {}

    for line in lines:
        key = line.strip()
        if len(key) < 5:
            continue
        frequency[key] = frequency.get(key, 0) + 1

    repeated = {line for line, count in frequency.items() if count >= 3}

    cleaned = [line for line in lines if line.strip() not in repeated]
    return "\n".join(cleaned)


def remove_extra_newlines(text: str) -> str:
    """Replace 3+ consecutive newlines with two."""
    return re.sub(r"\n{3,}", "\n\n", text)


def clean_whitespace(text: str) -> str:
    """Remove extra spaces while preserving paragraph breaks."""
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ ]{2,}", " ", line)
        lines.append(line.strip())
    return "\n".join(lines)


def remove_empty_lines(text: str) -> str:
    """Remove empty lines."""
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def fix_reversed_text(text: str) -> str:
    """
    Detect and fix character-reversed lines, which can happen
    with certain PDF font encodings.
    """
    lines = text.splitlines()
    fixed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append(line)
            continue

        # Heuristic: if reversing the line produces more real English words
        # than the original, assume it's reversed.
        reversed_line = stripped[::-1]

        original_word_score = _count_common_word_hits(stripped)
        reversed_word_score = _count_common_word_hits(reversed_line)

        if reversed_word_score > original_word_score:
            fixed_lines.append(reversed_line)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


_COMMON_WORDS = {
    "the", "and", "of", "to", "in", "is", "for", "with", "on", "are",
    "we", "our", "company", "infosys", "how", "from", "at", "as", "by"
}


def _count_common_word_hits(line: str) -> int:
    words = re.findall(r"[a-zA-Z]+", line.lower())
    return sum(1 for word in words if word in _COMMON_WORDS)


def preprocess_text(text: str) -> str:
    """
    Master preprocessing pipeline.

    Pipeline:
    Unicode normalization
    -> Remove page numbers
    -> Remove repeated headers/footers
    -> Remove excessive newlines
    -> Remove extra spaces
    -> Remove empty lines
    """
    if not text:
        logger.warning("preprocess_text received empty or None text.")
        return ""

    logger.info("Starting preprocessing pipeline.")

    text = normalize_unicode(text)
    text = remove_page_numbers(text)
    text = remove_headers_footers(text)
    text = remove_extra_newlines(text)
    text = clean_whitespace(text)
    text = remove_empty_lines(text)

    logger.info("Preprocessing completed.")
    return text


if __name__ == "__main__":
    sample = """
    Infosys Annual Report

    Page 1

    Infosys is a global technology company.

    - AI
    - Cloud

    Page 2

    Infosys Annual Report

    The company invests heavily in digital transformation.

    3
    """

    cleaned = preprocess_text(sample)
    print("=" * 80)
    print(cleaned)