#!/usr/bin/env python3
"""html-brief — render a Markdown draft as one self-contained HTML brief.

The agent writes content only. Panel placement, diagram coordinates, colors and
themes are computed here, so a draft stays small and the page stays readable.

Usage:
    python3 html_brief.py render draft.md --out brief.html
    python3 html_brief.py check draft.md
    python3 html_brief.py examples --out-dir ./out
    python3 html_brief.py validate --out-dir ./out
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from briefkit.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())