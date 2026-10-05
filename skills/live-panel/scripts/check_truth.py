#!/usr/bin/env python3
"""Check that a live-panel config keeps one truth, and that no variable is left unresolved.

Two defects that a geometry checker cannot see, both of which reach the reader:

  1. An unresolved value. A run reads ``{some.var}`` and no machine defines it, so
     the page shows the literal ``{some.var}``. ``undefined`` and ``NaN`` leak the
     same way. Every sampled frame is scanned for those.

  2. A second truth. The motion grammar requires the number in a log row to be the
     number on the bar. Each state machine emits its own log lines, so this holds
     by construction - this asserts it anyway, because the failure is silent and a
     stale hand-written log line is exactly how it breaks. Every number a gauge
     writes into the log must be that gauge's own live reading.

  python3 scripts/check_truth.py --config examples/skills-pipeline/config.json
Exit status 1 when any problem is found. Needs a local Chrome, like check_frames.py.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livepanel as lp

# A "{name}" the engine could not fill, or a JS value that leaked into the page.
LEAK = re.compile(r"\{[A-Za-z_][\w.\-]*\}|undefined|NaN|\[object Object\]")

# Every number a machine can print. Compared as text, so 0.90 and 0.9 are equal.
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")

# What the page hands back at one instant: every machine variable, and the visible
# log rows as [time, who, message, tag].
SNAPSHOT = """(function(){
  var rows=[].map.call(document.querySelectorAll('.lgrow'),function(r){
    return [].map.call(r.querySelectorAll('span'),function(s){return s.textContent});
  }).filter(function(c){return c.join('').trim()!==''});
  var texts=[].map.call(document.querySelectorAll('#stage [data-t]'),function(e){
    return e.textContent;
  }).join('\\n');
  return {vars:window.__vars(),rows:rows,texts:texts};
})()"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--samples", type=int, default=90,
                    help="how many instants to read the page at")
    ap.add_argument("--chrome", help="Chrome/Chromium executable (default: search PATH)")
    ap.add_argument("--template", help="alternative template.html")
    ap.add_argument("--no-sandbox", action="store_true")
    args = ap.parse_args()

    chrome = lp.find_exe(args.chrome, lp.CHROME_NAMES, "Chrome")
    work = Path(tempfile.mkdtemp(prefix="livepanel-truth-"))
    lp.build_page(args.config, work / "page.html", args.template)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    _, _, duration, _ = lp.canvas(cfg)

    # Gauges whose log line carries their live value. Their message is index-driven
    # and state-free, so the value in the tag is the only stateful part of the row.
    gauged = []
    for mid, m in (cfg.get("machines") or {}).items():
        log = m.get("log") or {}
        if m.get("type") == "gauge" and (log.get("tail") or ""):
            gauged.append((mid, m, log.get("who"), list(log.get("msgs") or [])))

    # Machines that write rows indistinguishable on screen - same role, same message -
    # can only be checked as a group, since a reader cannot tell them apart either.
    groups = {}
    for mid, m, who, msgs in gauged:
        groups.setdefault((who, tuple(msgs)), []).append((mid, m))

    def text_of(v):
        return v["text"] if isinstance(v, dict) else v

    def readings(mid, variables):
        """Every number this machine is currently showing anywhere on the panel."""
        out = set()
        for key in (mid, f"{mid}.num", f"{mid}.label", f"{mid}.dest"):
            v = variables.get(key)
            if v is None:
                continue
            out.update(NUMBER.findall(str(text_of(v))))
        return out

    problems = {}
    def flag(msg, t):
        problems.setdefault(msg, []).append(round(t, 2))

    with lp.Chrome(chrome, 1200, 1500, True if args.no_sandbox else None) as br:
        br.open("file://" + os.path.abspath(str(work / "page.html")) + "?manual")
        for i in range(args.samples):
            t = duration * (i + 0.5) / args.samples
            br.seek(t)
            snap = br.eval(SNAPSHOT)
            if snap is None:
                flag("page returned no snapshot", t)
                continue
            err = br.eval("window.__error||''")
            if err:
                flag("page error: " + err.strip(), t)
            for m in LEAK.finditer(snap["texts"]):
                flag(f"unresolved value {m.group(0)!r} on screen", t)
            variables = snap["vars"]
            for (who, msgs), members in groups.items():
                hits = [r for r in snap["rows"]
                        if len(r) >= 4 and r[1] == who and (not msgs or r[2] in msgs)]
                if not hits:
                    continue
                tag = hits[-1][3]
                allowed = set()
                for mid, _ in members:
                    allowed |= readings(mid, variables)
                for number in NUMBER.findall(tag):
                    if number not in allowed:
                        names = " / ".join(mid for mid, _ in members)
                        flag(f"log row {names} shows {number}, the panel reads "
                             f"{sorted(allowed) or ['nothing numeric']}", t)

    for msg, ts in problems.items():
        print(f"PROBLEM: {msg}  (first at t={ts[0]}s, {len(ts)} samples)")
    print(f"read {args.samples} instants, {len(gauged)} value-carrying gauges in "
          f"{len(groups)} distinguishable group(s), {len(problems)} distinct problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()