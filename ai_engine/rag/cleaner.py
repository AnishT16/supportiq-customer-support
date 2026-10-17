"""
Text Cleaning and Normalization Utilities for RAG Documents.
"""

import re
import unicodedata
from typing import Tuple


def normalize_whitespace(text: str) -> str:
    """Normalize excessive internal whitespace and consecutive blank lines."""
    if not text:
        return ""
    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)
    # Replace carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace 3 or more newlines with two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize spaces and tabs within lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def strip_markdown_decorations(text: str) -> str:
    """
    Remove markdown blockquote markers and formatting tags while retaining readable text.
    """
    if not text:
        return ""
    # Remove blockquote markers '> '
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def extract_title_and_clean(content: str, default_title: str = "Untitled Policy") -> Tuple[str, str]:
    """
    Extract H1 title from Markdown if present, and clean the remaining content.
    Returns:
        (title, cleaned_content)
    """
    if not content or not content.strip():
        return default_title, ""

    lines = content.split("\n")
    title = default_title
    body_start_idx = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# ") and not stripped.startswith("## ") and title == default_title:
            title = stripped[2:].strip()
            body_start_idx = idx + 1
            break
        else:
            # First non-empty line is not an H1 header
            body_start_idx = idx
            break

    body_lines = lines[body_start_idx:]
    remaining_text = "\n".join(body_lines)
    cleaned = normalize_whitespace(strip_markdown_decorations(remaining_text))
    return title, cleaned

