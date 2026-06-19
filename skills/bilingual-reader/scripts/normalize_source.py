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
    title = markdown.splitlines()[0].lstrip("#").strip()
    return web_markdown.slugify(title)


def normalize_url_to_markdown(
    url: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    output_name: str | None = None,
    html_file: Path | None = None,
    port: int = 9377,
    wait: float = 4.0,
) -> Path:
    """Convert a URL to Markdown under the bilingual-reader target directory."""

    web_markdown = load_web_markdown()
    source_url = web_markdown.validate_url(url)
    if html_file:
        source = html_file.read_text(encoding="utf-8")
    else:
        source = web_markdown.fetch_with_camofox(source_url, port=port, wait=wait)
    markdown = web_markdown.html_to_markdown(source, source_url)
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
