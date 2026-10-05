# Live Panel

[中文](./README.zh-CN.md)

Turn a description of a running system into a panel that never stops running:
one fixed layout, packets on the wires, a scrolling log, counters, bars that flip
state past a threshold, side triggers that light up in turn. Output is an H.264
mp4 for X or Xiaohongshu, or a page that runs live in any browser.

<img src="../../screenshots/live-panel/frame_2-t15.png" width="620" alt="Live Panel, terminal-dark theme, skills pipeline example at t=15s">

## What you ask, what you get

| You ask | You get |
| --- | --- |
| "Animate how requests move through our service" | A fixed architecture panel with packets on every wire, an mp4 |
| "Make this system diagram feel alive for X" | The same panel, cropped for a post, rendered at 30 fps |
| "An agent loop that plans, forks and reviews" | Boxes with gauges, trigger rail, typed advice and a session log |
| "A live architecture page for our docs site" | One self-contained HTML file, no dependency |
| "Explain the pipeline" | Nothing. Prose is the right answer unless you asked for a moving panel |

The agent writes one JSON file. The renderer computes the packets, the counters,
the state changes and the log, then drives a real browser frame by frame.

## Why not just ask for a video

A model asked for a video has to draw the picture, describe the motion, and hope
the two agree. Nothing checks the result, so the packet count drifts from the
counter and the log says a number the bar is not showing.

Here the layout never moves, and **every visual is a pure function of `t`** — no
wall clock, no `Math.random()`, no CSS animation. That one constraint is what
makes the result checkable: a checker can seek to any instant, read the same
instant, and compare.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill live-panel
```

Python 3.8+ standard library only, no pip packages. Chrome or Chromium for the
checks and for video, ffmpeg for video. Building the page needs neither.

## Use it

```bash
cd skills/live-panel

# inspect a config without rendering anything
python3 scripts/build_page.py examples/skills-pipeline/config.json --print

# a self-contained page: no browser, no ffmpeg
python3 scripts/build_page.py examples/skills-pipeline/config.json --out page.html

# measure the layout at ~120 instants and export PNGs
python3 scripts/check_frames.py --config examples/skills-pipeline/config.json --out-dir frames

# fail on an unresolved {variable}, or a log number the panel is not showing
python3 scripts/check_truth.py --config examples/skills-pipeline/config.json

# the mp4
python3 scripts/render.py --config examples/skills-pipeline/config.json --out panel.mp4
```

Useful flags:

| Flag | Script | Meaning |
| --- | --- | --- |
| `--out DIR` | `check_frames.py` | where the PNGs go |
| `--samples N` | both checkers | how many instants to read; 90 or more is a real check |
| `--repeat` | `check_frames.py` | seek away and back, and prove the frame is byte-identical |
| `--png N` | `check_frames.py` | how many PNGs to export |
| `--keep-frames DIR` | `render.py` | also keep every PNG the video was made from |
| `--html-out page.html` | `render.py` | keep the self-contained page next to the mp4 |
| `--duration`, `--fps`, `--crf` | `render.py` | override the config's canvas settings |
| `--chrome`, `--ffmpeg` | all | pass the executables instead of searching `PATH` |

## The config

One JSON object holds everything: canvas, theme, boxes with lines of text, wires,
packet paths, the trigger rail, log wording, numbers.

```json
{
  "canvas": { "preset": "4:5", "duration": 30, "fps": 30, "preroll": 12 },
  "theme":  { "preset": "terminal-dark" },
  "machines": {
    "ingest": {
      "type": "triggers", "color": "pu", "period": 5, "on": 3.2,
      "items": [
        { "name": "URL 抓取", "adv": ["» 读完再给结论", "» 别停在摘要"], "to": "→ 归一" }
      ],
      "log": { "who": "入口", "c": "pu",
               "start": { "m": "{name} · 已被叫起" },
               "end":   { "m": "{name} · 建议已给出", "g": "{to}" } }
    }
  },
  "elements": [
    { "type": "box", "x": 34, "y": 172, "w": 300, "h": 1000, "color": "pu",
      "pad": [13, 10, 10], "lines": [ { "t": "采集入口", "c": "pu", "b": 1 } ] }
  ]
}
```

`canvas.preset` is `4:5` (1200x1500), `3:4` (1080x1440) or `1:1` (1080x1080).
Coordinates are absolute canvas pixels, so a config is authored for one ratio;
for another, copy it and re-place the boxes. `references/config-schema.md` is the
full specification, and `references/motion-grammar.md` is the motion rules plus a
timing recipe that works at 30 s.

## The four rules

- **The layout never moves.** No camera, no build-up. Any frame cut from the clip
  is a finished diagram.
- **Three tempos at once.** Fast: packets with trails on every wire, spinners,
  counters. Medium: the log scrolls, bars re-roll and flip colour past a
  threshold. Slow: triggers light one at a time in order, their arrow takes the
  role colour and carries a packet, advice is typed out character by character,
  totals accumulate.
- **One truth everywhere.** The number in the log is the number on the bar. This
  holds by construction — the machines emit their own log rows — and
  `check_truth.py` asserts it anyway.
- **No real data? Say "illustrative".** Fixed facts stay fixed with their source
  named on screen. Anything that moves because the animation moves is the
  animation's own state, and it is labelled. Never invent a measurement and let
  it look real.

<img src="../../screenshots/live-panel/frame_3-t25.png" width="620" alt="The same panel at t=25s: different gauge states, a different trigger lit, the log moved on">

## Validation

```bash
python3 scripts/check_frames.py --config examples/skills-pipeline/config.json --out-dir frames --repeat
python3 scripts/check_truth.py --config examples/skills-pipeline/config.json
```

`check_frames.py` reads the DOM at ~120 instants and fails on text outside the
canvas, text overflowing its own box, text overlapping text, text sitting over a
foreign box, and box over box. `--repeat` seeks elsewhere and back and compares
pixels, which is how replay determinism is proven rather than assumed.

`check_truth.py` catches the two defects a geometry checker cannot see: a run that
reads `{some.var}` with no machine behind it, so the page shows the literal
`{some.var}`; and a number in a log row that is not the machine's own live
reading.

Both need a local Chrome. They write into a temporary folder and leave the
repository alone.

Measured on this repository's example, Chrome 154.0.8037.93, macOS 15.5:

| Check | Result |
| --- | --- |
| `check_frames.py`, 90 sampled instants | 0 problems |
| `check_frames.py --repeat` | 3 exported frames byte-identical on re-render |
| `check_truth.py`, 90 sampled instants | 0 problems, 3 value-carrying gauges |
| the generated page | 47 KB, no external URL of any kind, byte-identical on rebuild |
| `render.py` mp4 | **not verified here** — ffmpeg was not installed on the machine used |

Without ffmpeg, `render.py` exits 1 with `ffmpeg not found on PATH` and writes
nothing, rather than producing a partial file. The mp4 path is the one part of
this skill the numbers above do not cover.

## Known limits

- Diagram geometry is absolute pixels. Changing `theme.preset` changes the font
  and the line height too, which invalidates positions; `references/motion-grammar.md`
  section 7 lists exactly what breaks and why.
- No font files are bundled. The stacks fall back through installed fonts, so a
  machine without JetBrains Mono and Noto CJK renders slightly different glyph
  widths. Re-run `check_frames.py` after changing fonts.
- Rendering video needs ffmpeg. Without it, `build_page.py` still produces the
  live page.
- A config that renders twice identically on one machine still renders twice
  identically only on that machine: fonts and Chrome version move glyph widths.

## Project layout

```text
skills/live-panel/
  SKILL.md
  README.md
  README.zh-CN.md
  manifest.json
  LICENSE
  THIRD-PARTY-NOTICES.md
  assets/template.html   generic page, never edited per diagram
  examples/skills-pipeline/config.json
  references/            config schema, motion grammar
  scripts/
    build_page.py        config to a self-contained page
    render.py            page to mp4
    check_frames.py      geometry, PNG export, replay identity
    check_truth.py       unresolved values, log versus panel
    livepanel.py         shared helpers
tests/live-panel/skills-pipeline/index.html
screenshots/live-panel/
```

## License

Apache-2.0, the same license as the rest of this repository. See
[LICENSE](./LICENSE).

The engine this skill is built on is MIT licensed and vendored here; see
[THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md) for the exact files, the
changes made to them, and the full MIT text.

## Credits

`live-panel` is built on
[ythx-101/live-panel-skill](https://github.com/ythx-101/live-panel-skill) (MIT).
It keeps the same shape: a JSON config drives a deterministic page, and headless
checks measure the result instead of trusting it. This repository adds the
bilingual documentation, `build_page.py`, `check_truth.py`, and an example about
its own skill pipeline.

The idea behind the look — a diagram is the monitoring panel of a running system,
so the motion is system state rather than decoration — comes from an
architecture-diagram clip by **[@thedelost](https://x.com/thedelost/status/2105398038026195279)**,
which spread through a quote-post by
**[@slashui](https://x.com/slashui/status/2105850132365443528)**. That design
belongs to the original author. Nothing of that clip, and no recreation of it, is
bundled here: `examples/skills-pipeline/` is an original panel about this
repository's own skills.

If you render output that recreates or re-animates someone else's diagram, put the
original author and link in the video footer's `credit` field and in the post.