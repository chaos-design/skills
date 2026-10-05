#!/usr/bin/env python3
"""Build a self-contained live-panel page from a JSON config.

  python3 scripts/build_page.py examples/skills-pipeline/config.json --out page.html

No browser and no ffmpeg. The page embeds the config, runs the loop on
requestAnimationFrame, and exposes window.seek(t) for the checkers. Use this to
hand someone a linkable artifact or to look at a config without rendering video.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livepanel as lp


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="path to the JSON config")
    ap.add_argument("--out", default="page.html", help="output HTML (default: page.html)")
    ap.add_argument("--template", help="alternative template.html")
    ap.add_argument("--force", action="store_true", help="overwrite instead of writing name-2.html")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print canvas, machines and element counts, then exit")
    args = ap.parse_args()

    cfg = lp.load_config(args.config)
    if args.show:
        w, h, dur, fps = lp.canvas(cfg)
        kinds = {}
        for e in cfg.get("elements") or []:
            kinds[e["type"]] = kinds.get(e["type"], 0) + 1
        print(f"canvas {w}x{h} · {dur}s @ {fps}fps")
        print(f"machines {len(cfg.get('machines') or {})}: "
              f"{', '.join(sorted((cfg.get('machines') or {}).keys())) or 'none'}")
        print(f"elements {sum(kinds.values())}: "
              f"{', '.join(f'{k} x{v}' for k, v in sorted(kinds.items())) or 'none'}")
        print(f"credit: {(cfg.get('credit') or {}).get('text') or '(none)'}")
        return 0

    out = Path(args.out)
    if out.exists() and not args.force:
        n = 2
        stem = out.with_suffix("")
        while Path(f"{stem}-{n}{out.suffix}").exists():
            n += 1
        out = Path(f"{stem}-{n}{out.suffix}")
    out.parent.mkdir(parents=True, exist_ok=True)
    lp.build_page(args.config, out, args.template)

    # A page that silently lost its config is worse than one that refuses to build.
    page = out.read_text(encoding="utf-8")
    if '"live-config"' not in page:
        print("config was not embedded in the page", file=sys.stderr)
        return 1
    size = out.stat().st_size
    print(f"wrote {out} ({size} bytes, {len(page.splitlines())} lines)")
    print("open it in any browser; add ?manual to stop the loop and drive window.seek(t)")
    return 0


if __name__ == "__main__":
    sys.exit(main())