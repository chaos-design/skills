#!/usr/bin/env python3
"""Browser layout check for generated briefs.

The renderer computes diagram geometry from an estimate of text width, so the
only way to prove a label is not clipped is to measure it in the browser that
will draw it. This script renders every example, asks headless Chrome to report
any text that leaves its SVG viewBox or the page width, and fails when it finds
one.

Usage:
    python3 scripts/check_layout.py
    python3 scripts/check_layout.py --chrome "/path/to/chrome"

The check renders into a temporary folder and writes nothing to the repository.
Chrome is optional. When no browser is available the script reports the check as
skipped and exits 0, so it never fakes a passing result.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from briefkit.cli import build_page, example_files, slugify  # noqa: E402

CANDIDATES = {
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ],
    "Linux": [
        "google-chrome",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
    ],
    "Windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
}

PROBE = """
<script>
window.addEventListener('load', function () {
  var report = {diagrams: [], page: {}, overflow: []};
  document.querySelectorAll('figure.diagram').forEach(function (figure, index) {
    var svg = figure.querySelector('svg');
    var box = svg.viewBox.baseVal;
    var frame = svg.getBoundingClientRect();
    var scale = frame.width / box.width;
    report.diagrams.push({index: index, width: box.width, height: box.height, scale: scale});
    svg.querySelectorAll('text').forEach(function (node) {
      var rect = node.getBoundingClientRect();
      var box2 = {
        left: (rect.left - frame.left) / scale,
        right: (rect.right - frame.left) / scale,
        top: (rect.top - frame.top) / scale,
        bottom: (rect.bottom - frame.top) / scale,
      };
      if (box2.right > box.width || box2.left < 0 || box2.bottom > box.height || box2.top < 0) {
        report.overflow.push({
          diagram: index,
          text: node.textContent.slice(0, 40),
          box: [Math.round(box2.left), Math.round(box2.top), Math.round(box2.right), Math.round(box2.bottom)],
          viewBox: [Math.round(box.width), Math.round(box.height)],
        });
      }
    });
  });
  var doc = document.documentElement;
  report.page = {clientWidth: doc.clientWidth, scrollWidth: doc.scrollWidth};
  var pre = document.createElement('pre');
  pre.id = 'html-brief-probe';
  pre.textContent = JSON.stringify(report);
  document.body.appendChild(pre);
});
</script>
"""


def find_chrome(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() or shutil.which(explicit) else None
    for candidate in CANDIDATES.get(platform.system(), []):
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    return None


def probe(chrome: str, page: Path) -> dict:
    instrumented = page.with_name(page.stem + "-probe.html")
    instrumented.write_text(page.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>"), encoding="utf-8")
    pattern = re.compile(r'<pre id="html-brief-probe">(.*?)</pre>', re.S)
    command = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1280,1600",
        "--virtual-time-budget=4000",
        "--dump-dom",
        instrumented.resolve().as_uri(),
    ]
    try:
        # One retry, because a browser that is still shutting down from a
        # previous run can stall the next one.
        for _attempt in (1, 2):
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=45)
            except subprocess.TimeoutExpired:
                continue
            match = pattern.search(result.stdout)
            if match:
                return json.loads(match.group(1))
    finally:
        instrumented.unlink(missing_ok=True)
    raise RuntimeError("chrome did not return a probe payload")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--examples-dir", default=None)
    parser.add_argument("--chrome", default=None)
    parser.add_argument("--date", default=None, help="fixed stamp for reproducible runs")
    args = parser.parse_args()

    examples_dir = Path(args.examples_dir) if args.examples_dir else Path(__file__).resolve().parents[1] / "examples"
    drafts = example_files(examples_dir)
    if not drafts:
        print(f"no example drafts in {examples_dir}", file=sys.stderr)
        return 1

    chrome = find_chrome(args.chrome)
    if not chrome:
        print("skipped: no headless Chrome found; pass --chrome <path> to run this check")
        return 0

    class Options:
        theme = mode = lang = columns = None
        date = args.date
        no_date = False
        check = "off"

    failures = 0
    with tempfile.TemporaryDirectory(prefix="html-brief-layout-") as work:
        for draft in drafts:
            target = Path(work) / f"{slugify(draft.stem)}.html"
            target.write_text(
                build_page(draft.read_text(encoding="utf-8"), args=Options(), source=str(draft))[0],
                encoding="utf-8",
            )
            report = probe(chrome, target)
            problems = list(report["overflow"])
            if report["page"]["scrollWidth"] > report["page"]["clientWidth"] + 1:
                problems.append({"diagram": -1, "text": "page scrolls sideways", "box": [], "viewBox": []})
            if problems:
                failures += 1
                print(f"FAIL {draft.name}")
                for item in problems:
                    print(f"  {item}")
            else:
                diagrams = ", ".join(
                    f"{item['width']:.0f}x{item['height']:.0f}@{item['scale']:.2f}" for item in report["diagrams"]
                )
                print(f"ok   {draft.name} · diagrams: {diagrams or 'none'}")
    print("layout check failed" if failures else f"layout check passed for {len(drafts)} example(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())