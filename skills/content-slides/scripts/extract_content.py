#!/usr/bin/env python3
"""
extract_content.py — Pull clean, readable text from a URL or a local file.

Optional Phase-1 helper. Strips boilerplate from web pages and extracts text
from common document formats so you can build the content brief without
manually reading raw HTML/PDF bytes.

Usage:
    python extract_content.py <url-or-filepath>

Supported:
    - http(s) URLs           (requires: requests; better with beautifulsoup4)
    - .md / .txt files       (read directly)
    - .html files            (tag-stripped)
    - .pdf files             (requires: pdfplumber or PyPDF2)
    - .docx files            (requires: python-docx)

Prints extracted text to stdout. For anything it can't handle, it explains
which package to install. This is a convenience — if it fails, fall back to
the agent's own fetch/read/skill tools.
"""
import os
import re
import sys


def _from_html(html):
    """Very small HTML-to-text fallback when BeautifulSoup is unavailable."""
    html = re.sub(r"(?is)<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def from_url(url):
    try:
        import requests
    except ImportError:
        return "ERROR: 'requests' not installed. Run: pip install --user requests"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        return f"ERROR fetching URL: {e}"
    html = resp.text
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        title = (soup.title.string or "").strip() if soup.title else ""
        body = soup.get_text("\n")
        body = re.sub(r"\n\s*\n\s*\n+", "\n\n", body).strip()
        return (f"# {title}\n\n{body}" if title else body)
    except ImportError:
        return _from_html(html)


def from_pdf(path):
    try:
        import pdfplumber
        out = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                out.append(page.extract_text() or "")
        return "\n\n".join(out).strip()
    except ImportError:
        pass
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        return "\n\n".join((p.extract_text() or "") for p in reader.pages).strip()
    except ImportError:
        return ("ERROR: install a PDF library. Run: pip install --user pdfplumber\n"
                "Or use the 'pdf' skill for richer extraction.")


def from_docx(path):
    try:
        import docx
    except ImportError:
        return ("ERROR: 'python-docx' not installed. Run: pip install --user python-docx\n"
                "Or use the 'docx' skill.")
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def from_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".md", ".txt", ".markdown"):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    if ext in (".html", ".htm"):
        with open(path, encoding="utf-8", errors="replace") as f:
            return _from_html(f.read())
    if ext == ".pdf":
        return from_pdf(path)
    if ext == ".docx":
        return from_docx(path)
    # Unknown extension: try plain read.
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_content.py <url-or-filepath>")
        sys.exit(1)
    src = sys.argv[1]
    if src.startswith("http://") or src.startswith("https://"):
        print(from_url(src))
    elif os.path.isfile(src):
        print(from_file(src))
    else:
        print(f"ERROR: not a URL and not an existing file: {src}")
        sys.exit(1)


if __name__ == "__main__":
    main()
