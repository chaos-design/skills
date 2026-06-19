#!/usr/bin/env python3
"""Normalize URL sources into bilingual-reader's own output directory."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
WEB_MARKDOWN_PATH = SKILL_DIR.parent / "web-markdown" / "scripts" / "web_markdown.py"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tests" / "bilingual-reader"
MAX_HTML_BYTES = 10 * 1024 * 1024
MAX_MARKDOWN_CHARS = 2_000_000
MIN_MARKDOWN_CHARS = 400


def load_web_markdown():
    """Load the dependency script without relying on package names."""

    if not WEB_MARKDOWN_PATH.exists():
        raise FileNotFoundError(f"web-markdown script is missing: {WEB_MARKDOWN_PATH}")
    spec = importlib.util.spec_from_file_location("web_markdown", WEB_MARKDOWN_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load web-markdown script: {WEB_MARKDOWN_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_output_name(name: str | None, markdown: str, web_markdown) -> str:
    """Return a filename that cannot escape the selected output directory."""

    if name:
        candidate = Path(name)
        if candidate.is_absolute() or candidate.name != name or candidate.suffix.lower() != ".md":
            raise ValueError("--output-name must be a plain Markdown filename, for example article.md")
        return candidate.name
    title = markdown.splitlines()[0].lstrip("#").strip() if markdown.splitlines() else "article"
    filename = web_markdown.slugify(title) or "article.md"
    return filename if filename.lower().endswith(".md") else f"{filename}.md"


def validate_camofox_options(port: int, wait: float) -> None:
    """Validate browser capture parameters before opening Camofox."""

    if not 1 <= port <= 65535:
        raise ValueError("--port must be between 1 and 65535.")
    if wait < 0 or wait > 60:
        raise ValueError("--wait must be between 0 and 60 seconds.")


def read_html_file(path: Path) -> str:
    """Read a local HTML capture after size and type checks."""

    html_path = Path(path).expanduser().resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"--html-file does not exist: {html_path}")
    if not html_path.is_file():
        raise ValueError(f"--html-file must be a regular file: {html_path}")
    size = html_path.stat().st_size
    if size == 0:
        raise ValueError("--html-file is empty.")
    if size > MAX_HTML_BYTES:
        raise ValueError(f"--html-file is too large: {size} bytes, max {MAX_HTML_BYTES}.")
    text = html_path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("--html-file has no readable HTML text.")
    return text


def validate_markdown_output(markdown: str) -> None:
    """Ensure HTML conversion produced a usable Markdown source."""

    text = markdown.strip()
    if not text:
        raise ValueError("Converted Markdown is empty.")
    if len(text) > MAX_MARKDOWN_CHARS:
        raise ValueError(f"Converted Markdown is too large: {len(text)} characters.")
    if len(text) < MIN_MARKDOWN_CHARS:
        raise ValueError("Converted Markdown is too short; source extraction is likely incomplete.")
    if not re.search(r"^#\s+\S+", text, re.MULTILINE):
        raise ValueError("Converted Markdown is missing an H1 title.")
    if not re.search(r"^>\s*Source:\s*\S+", text, re.MULTILINE | re.IGNORECASE):
        raise ValueError("Converted Markdown is missing Source metadata.")


def normalize_url_to_markdown(
    url: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    output_name: str | None = None,
    html_file: Path | None = None,
    port: int = 9377,
    wait: float = 4.0,
) -> Path:
    """Convert a URL to Markdown under the bilingual-reader target directory."""

    validate_camofox_options(port, wait)
    web_markdown = load_web_markdown()
    source_url = web_markdown.validate_url(url)
    if html_file:
        source = read_html_file(html_file)
    else:
        source = web_markdown.fetch_with_camofox(source_url, port=port, wait=wait)
    markdown = web_markdown.html_to_markdown(source, source_url)
    validate_markdown_output(markdown)
    target_dir = Path(output_dir).expanduser().resolve()
    target_name = safe_output_name(output_name, markdown, web_markdown)
    target = web_markdown.unique_output_path(target_dir / target_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Normalize a URL for bilingual-reader.")
    parser.add_argument("url", help="HTTP(S) URL to normalize.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for the review Markdown. Defaults to {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument("--output-name", help="Optional Markdown filename, such as article.md.")
    parser.add_argument("--html-file", type=Path, help="Use a local rendered HTML file instead of Camofox.")
    parser.add_argument("--port", type=int, default=9377, help="Camofox port. Defaults to 9377.")
    parser.add_argument("--wait", type=float, default=4.0, help="Seconds to wait after opening the Camofox tab.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    try:
        output = normalize_url_to_markdown(
            args.url,
            output_dir=args.output_dir,
            output_name=args.output_name,
            html_file=args.html_file,
            port=args.port,
            wait=args.wait,
        )
    except Exception as exc:
        print(f"bilingual-reader normalize failed: {exc}", file=sys.stderr)
        return 1
    word_count = len(re.findall(r"\w+", output.read_text(encoding="utf-8")))
    print(f"Saved {output} - {word_count} words - {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
