"""Serves guideline files for the source-preview modal. Looks only inside AUFI_KB_DOCS_DIR."""
from pathlib import Path
from typing import Optional

from . import config


def document_path(filename: str) -> Optional[Path]:
    """Safe lookup: bare filenames only, must exist inside the guideline folder."""
    if not filename or filename != Path(filename).name:
        return None
    p = (config.KB_DOCS_DIR / filename).resolve()
    if config.KB_DOCS_DIR.resolve() not in p.parents or not p.is_file():
        return None
    return p


def document_text(filename: str) -> Optional[str]:
    p = document_path(filename)
    if p is None:
        return None
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)
    return p.read_text(encoding="utf-8", errors="replace")
