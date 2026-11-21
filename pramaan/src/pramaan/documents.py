"""Read the text of a brief, petition, order or judgment (txt, md, pdf, docx)."""

from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

from .quotes import pdf_to_text


def docx_to_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n\n", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
        text = text.replace(a, b)
    return text


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = pdf_to_text(path)
        if text is None:
            raise SystemExit("Could not read the PDF: install poppler (pdftotext) or `pip install pypdf`.")
        return text
    if suffix == ".docx":
        return docx_to_text(path)
    return path.read_text(errors="ignore")


def read_bytes(name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".pdf", ".docx"}:
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            f.write(data)
            f.flush()
            return read_document(Path(f.name))
    return data.decode("utf-8", errors="ignore")
