"""
Document Loading Utilities for Markdown Policies and Guides.
"""

from pathlib import Path
import sys
from typing import List, Tuple, Union
import logging

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ai_engine.rag.cleaner import extract_title_and_clean

logger = logging.getLogger(__name__)


class DocumentNotFoundError(FileNotFoundError):
    """Raised when a specified policy document cannot be located."""
    pass


class DocumentLoader:
    """Loads and parses Markdown policy documents from files or directories."""

    @staticmethod
    def load_file(file_path: Union[str, Path]) -> Tuple[str, str, str]:
        """
        Load a single markdown file.
        Returns:
            Tuple of (cleaned_content, document_title, source_name)
        Raises:
            DocumentNotFoundError: if the file does not exist.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise DocumentNotFoundError(f"Policy document not found at: {path}")

        try:
            raw_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_text = path.read_text(encoding="latin-1")

        default_title = path.stem.replace("_", " ").replace("-", " ").title()
        title, cleaned_content = extract_title_and_clean(raw_text, default_title=default_title)
        return cleaned_content, title, path.name

    @classmethod
    def load_directory(
        cls, dir_path: Union[str, Path], recursive: bool = False
    ) -> List[Tuple[str, str, str]]:
        """
        Load all markdown (.md) documents from a directory.
        Returns:
            List of Tuples: (cleaned_content, document_title, source_name)
        """
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            logger.warning(f"Knowledge documents directory does not exist: {path}")
            return []

        pattern = "**/*.md" if recursive else "*.md"
        results = []
        for file_path in sorted(path.glob(pattern)):
            try:
                results.append(cls.load_file(file_path))
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")

        return results
