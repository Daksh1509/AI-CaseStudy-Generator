"""
test_preprocess.py

Unit tests for the text-cleaning pipeline in src/preprocess.py.

These are pure unit tests: they use inline sample text, need no
data files and no API key, so they run fast and in CI.
"""

from src.preprocess import (
    normalize_unicode,
    remove_page_numbers,
    remove_headers_footers,
    remove_extra_newlines,
    clean_whitespace,
    remove_empty_lines,
    preprocess_text,
)


def test_normalize_unicode_replaces_smart_characters():
    raw = "“Hello” ‘world’ – dash • bullet …"
    cleaned = normalize_unicode(raw)
    assert '"Hello"' in cleaned
    assert "'world'" in cleaned
    assert "-" in cleaned          # en/em dash and bullet became "-"
    assert "..." in cleaned        # ellipsis
    # No smart characters should remain.
    for smart in ["“", "”", "‘", "’", "•", "…"]:
        assert smart not in cleaned


def test_remove_page_numbers_drops_standalone_numbers():
    raw = "Intro line\nPage 1\n2\nReal content here\nPage 12"
    cleaned = remove_page_numbers(raw)
    lines = cleaned.splitlines()
    assert "Intro line" in lines
    assert "Real content here" in lines
    assert "Page 1" not in lines
    assert "2" not in lines
    assert "Page 12" not in lines


def test_remove_headers_footers_removes_repeated_lines():
    header = "Infosys Annual Report"
    raw = "\n".join([header, "para one", header, "para two", header, "para three"])
    cleaned = remove_headers_footers(raw)
    # The header repeats 3 times, so it should be dropped.
    assert header not in cleaned.splitlines()
    # Real paragraphs stay.
    assert "para one" in cleaned
    assert "para three" in cleaned


def test_remove_headers_footers_keeps_lines_repeated_twice():
    line = "This line appears only twice here"
    raw = "\n".join([line, "other", line])
    cleaned = remove_headers_footers(raw)
    # Repeated only twice (< 3), so it must be kept.
    assert line in cleaned


def test_remove_extra_newlines_collapses_blank_runs():
    raw = "a\n\n\n\n\nb"
    cleaned = remove_extra_newlines(raw)
    assert "\n\n\n" not in cleaned
    assert "a" in cleaned and "b" in cleaned


def test_clean_whitespace_collapses_spaces_and_strips():
    raw = "hello     world  \n   spaced   out   "
    cleaned = clean_whitespace(raw)
    assert "hello world" in cleaned
    assert "spaced out" in cleaned
    # No line should have leading/trailing spaces.
    for line in cleaned.splitlines():
        assert line == line.strip()


def test_remove_empty_lines():
    raw = "a\n\n   \nb\n"
    cleaned = remove_empty_lines(raw)
    assert cleaned.splitlines() == ["a", "b"]


def test_preprocess_text_end_to_end():
    sample = (
        "Infosys Annual Report\n"
        "Page 1\n"
        "Infosys is a global technology company.\n"
        "\n\n\n"
        "The company invests heavily in digital transformation.\n"
        "3\n"
    )
    cleaned = preprocess_text(sample)
    # Page markers gone.
    assert "Page 1" not in cleaned
    assert "\n3\n" not in cleaned
    # Real content preserved.
    assert "global technology company" in cleaned
    assert "digital transformation" in cleaned
    # No blank lines left.
    assert "" not in cleaned.splitlines()


def test_preprocess_text_handles_empty_and_none():
    # Should not raise, and should return an empty string.
    assert preprocess_text("") == ""
    assert preprocess_text(None) == ""


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
