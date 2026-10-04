"""Command line interface for the html-brief renderer."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import __version__
from .check import check_draft
from .parser import DraftError, parse_draft
from .render import render_page
from .textutil import slugify

UTC8 = timezone(timedelta(hours=8))
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
COMMANDS = ("render", "check", "examples", "validate", "help")
DEFAULT_OUT_DIR = "briefs"

USAGE = """html-brief — turn a Markdown draft into one self-contained HTML brief.

  render <draft.md|-> [--out FILE] [--theme blueprint|document] [--mode auto|light|dark]
         [--lang auto|en|zh|ja] [--columns 1|2] [--date 'YYYY-MM-DD HH:MM:SS'] [--no-date]
         [--check off|warn|strict] [--open]
  check <draft.md> [--json]
  examples [--out-dir DIR] [--theme ...] [--date ...]
  validate [--out-dir DIR]
  help

The model writes the draft; this renderer computes layout, diagrams and theme.
"""


def resolve_date(value: str | None, use_date: bool) -> str:
    if not use_date:
        return ""
    if value:
        try:
            datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            raise DraftError(
                f"`{value}` is not a valid date", 0, "date", "2026-10-04 17:30:00"
            ) from None
        return value
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        moment = datetime.fromtimestamp(int(epoch), tz=UTC8)
    else:
        moment = datetime.now(UTC8)
    return moment.strftime(DATE_FORMAT)


def display_source(path: str | Path, limit: int = 68) -> str:
    """Prefer a path relative to the working directory for the page stamp.

    A path that is still too long keeps its last two segments, so provenance
    survives without pushing the masthead onto three lines.
    """
    candidate = Path(path)
    try:
        shown = str(candidate.resolve().relative_to(Path.cwd()))
    except (ValueError, OSError):
        shown = str(path)
    if len(shown) <= limit:
        return shown
    parts = Path(shown).parts
    if len(parts) > 2:
        return ".../" + "/".join(parts[-2:])
    return shown


def read_draft(path: str) -> tuple[str, str]:
    if path == "-":
        return sys.stdin.read(), "stdin"
    file_path = Path(path)
    if not file_path.is_file():
        raise DraftError(f"draft not found: {path}", 0, "input", "html_brief.py render draft.md")
    return file_path.read_text(encoding="utf-8"), display_source(file_path)


def next_free_path(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for index in range(2, 1000):
        candidate = target.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise DraftError(f"cannot find a free file name near {target}", 0, "output")


def target_path(out: str | None, title: str, out_dir: str) -> Path:
    if out:
        candidate = Path(out)
        if out.endswith(("/", os.sep)) or candidate.is_dir():
            candidate = candidate / f"{slugify(title)}.html"
        return candidate
    return Path(out_dir) / f"{slugify(title)}.html"


def build_page(
    draft_text: str,
    *,
    args: argparse.Namespace,
    source: str,
) -> tuple[str, str, list]:
    document = parse_draft(draft_text, source)
    title = document.title or slugify(source)
    date = resolve_date(getattr(args, "date", None), not getattr(args, "no_date", False))
    stamp_bits = []
    if date:
        stamp_bits.append(f"Generated {date} (UTC+8)")
    stamp_bits.append(f"Source: {source}")
    stamp = " · ".join(stamp_bits)
    columns = int(getattr(args, "columns", 0) or document.meta.get("columns") or 2)
    if columns not in (1, 2):
        raise DraftError(f"columns must be 1 or 2, got {columns}", 0, "front matter", "columns: 2")
    theme = getattr(args, "theme", None) or document.meta.get("theme", "document")
    mode = getattr(args, "mode", None) or document.meta.get("mode", "auto")
    lang = getattr(args, "lang", None) or document.meta.get("lang", "auto")
    if theme not in ("blueprint", "document"):
        raise DraftError(
            f"theme must be blueprint or document, got {theme}", 0, "front matter", "theme: blueprint"
        )
    if mode not in ("auto", "light", "dark"):
        raise DraftError(
            f"mode must be auto, light or dark, got {mode}", 0, "front matter", "mode: auto"
        )
    page = render_page(
        document,
        source_text=draft_text,
        theme=theme,
        mode=mode,
        lang=lang,
        columns=columns,
        stamp=stamp,
        source_label=source,
        note=document.meta.get("note", ""),
    )
    return page, title, document.panels


def run_render(args: argparse.Namespace, draft_text: str, source: str) -> int:
    page, title, panels = build_page(draft_text, args=args, source=source)
    target = target_path(args.out, title, args.out_dir)
    target = next_free_path(target) if not args.force else target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    if args.open:
        webbrowser.open(target.resolve().as_uri())
    if not args.quiet:
        print(f"{target.resolve()}")
        print(f"  panels: {len(panels)} · bytes: {len(page.encode('utf-8'))} · theme: {args.theme or 'front matter'}")
    return 0


def run_check(args: argparse.Namespace) -> int:
    draft_text, source = read_draft(args.draft)
    findings = check_draft(draft_text)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "line": item.line,
                        "rule": item.rule,
                        "message": item.message,
                        "hint": item.hint,
                    }
                    for item in findings
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if findings else 0
    if not findings:
        print(f"{source}: no writing findings")
        return 0
    print("\n".join(item.render(source) for item in findings))
    print(f"{len(findings)} finding(s); set `--check off` to skip this gate")
    return 1


def example_files(examples_dir: Path) -> list[Path]:
    return sorted(path for path in examples_dir.glob("*.md") if path.is_file())


def run_examples(args: argparse.Namespace) -> int:
    examples_dir = Path(args.examples_dir)
    files = example_files(examples_dir)
    if not files:
        print(f"no example drafts in {examples_dir}", file=sys.stderr)
        return 1
    out_root = Path(args.out_dir)
    failures = 0
    for path in files:
        target_dir = out_root / slugify(path.stem)
        target = target_dir / "index.html"
        try:
            page, _title, panels = build_page(
                path.read_text(encoding="utf-8"), args=args, source=display_source(path)
            )
        except DraftError as error:
            print(error.render(str(path)), file=sys.stderr)
            failures += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        print(f"{target} ({len(panels)} panels)")
    return 1 if failures else 0


FORBIDDEN = re.compile(
    r"""(?:src|href)\s*=\s*["'](?:https?:)?//|@import\s|url\(\s*["']?(?:https?:)?//|fonts\.googleapis|cdn\.""",
    re.IGNORECASE,
)


def run_validate(args: argparse.Namespace) -> int:
    """Render every example and assert the page stays self-contained."""
    examples_dir = Path(args.examples_dir)
    files = example_files(examples_dir)
    if not files:
        print(f"no example drafts in {examples_dir}", file=sys.stderr)
        return 1
    problems = 0
    for path in files:
        draft_text = path.read_text(encoding="utf-8")
        try:
            page, _title, panels = build_page(draft_text, args=args, source=display_source(path))
        except DraftError as error:
            print(f"FAIL {path.name}: {error.render(display_source(path))}", file=sys.stderr)
            problems += 1
            continue
        target = Path(args.out_dir) / slugify(path.stem) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        checks = {
            "panels": len(panels) >= 1,
            "doctype": page.startswith("<!doctype html>"),
            "inline-style": "<style>" in page,
            "no-external": not FORBIDDEN.search(page),
            "source-embedded": 'id="html-brief-source"' in page,
            "closed-html": page.rstrip().endswith("</html>"),
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            problems += 1
            print(f"FAIL {path.name}: {', '.join(failed)}", file=sys.stderr)
        else:
            print(f"ok   {path.name} → {target} ({len(panels)} panels, {len(page)} chars)")
    print("validation failed" if problems else f"validation passed for {len(files)} example(s)")
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="html_brief.py",
        description="Render a Markdown draft as one self-contained HTML brief.",
        add_help=True,
    )
    parser.add_argument("--version", action="version", version=f"html-brief {__version__}")
    sub = parser.add_subparsers(dest="command")

    def add_shared(target: argparse.ArgumentParser) -> None:
        target.add_argument("--theme", choices=("blueprint", "document"), default=None)
        target.add_argument("--mode", choices=("auto", "light", "dark"), default=None)
        target.add_argument("--lang", choices=("auto", "en", "zh", "ja"), default=None)
        target.add_argument("--columns", type=int, default=None, choices=(1, 2))
        target.add_argument(
            "--date",
            default=None,
            help="stamp the page, format " + DATE_FORMAT.replace("%", "") + " (UTC+8)",
        )
        target.add_argument("--no-date", action="store_true", help="omit the generation stamp")
        target.add_argument("--check", choices=("off", "warn", "strict"), default="warn")
        target.add_argument(
            "--examples-dir",
            default=str(Path(__file__).resolve().parents[2] / "examples"),
            help="folder of example drafts used by `examples` and `validate`",
        )

    render = sub.add_parser("render", help="render one draft")
    render.add_argument("draft")
    render.add_argument("--out", default=None, help="output file or directory")
    render.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    render.add_argument("--open", action="store_true", help="open the page in a browser")
    render.add_argument("--force", action="store_true", help="overwrite an existing file")
    render.add_argument("--quiet", action="store_true")
    add_shared(render)

    check = sub.add_parser("check", help="report writing findings for a draft")
    check.add_argument("draft")
    check.add_argument("--json", action="store_true")

    examples = sub.add_parser("examples", help="render every example draft")
    examples.add_argument("--out-dir", required=True)
    add_shared(examples)

    validate = sub.add_parser("validate", help="render examples and check they stay offline")
    validate.add_argument("--out-dir", required=True)
    add_shared(validate)

    sub.add_parser("help", help="show this message")
    return parser


def run_gate(draft_text: str, source: str, mode: str) -> int:
    if mode == "off":
        return 0
    findings = check_draft(draft_text)
    if not findings:
        return 0
    for item in findings:
        print(f"warning: {item.render(source)}", file=sys.stderr)
    if mode == "strict":
        print("strict mode: fix the findings above, or use --check warn", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if argv[0] in ("--version", "-V"):
        print(f"html-brief {__version__}")
        return 0
    if argv[0] not in COMMANDS:
        argv = ["render"] + argv
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if command == "help":
        print(USAGE)
        return 0
    try:
        if command == "render":
            draft_text, source = read_draft(args.draft)
            gate = run_gate(draft_text, source, args.check)
            if gate:
                return gate
            return run_render(args, draft_text, source)
        if command == "check":
            return run_check(args)
        if command == "examples":
            return run_examples(args)
        if command == "validate":
            return run_validate(args)
    except DraftError as error:
        print(f"error: {error.render()}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        return 130
    print(USAGE)
    return 1