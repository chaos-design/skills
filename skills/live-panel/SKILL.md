---
name: live-panel
description: >
  Turns a description of a running system into an always-running architecture
  panel: one fixed layout, glowing packets on the wires, a scrolling log,
  counters, bars that flip state past a threshold and side triggers that light up
  in turn. Renders to an H.264 mp4 for X or Xiaohongshu, or to a self-contained
  page that runs live in any browser. Invoke when the user wants a system,
  agent, org or data-flow diagram that should feel like a monitoring dashboard
  instead of a static picture, a slide-by-slide reveal or a wall of prose.
---

# Live Panel

Use this skill when the answer is a system, and the reader should see it *run*.
The layout never moves and no step appears one by one: frame 0 is already a
complete, readable diagram, and what changes is the system's state.

Do not use it for a diagram a reader has to explore, for real telemetry, or for
explaining something step by step. Use `html-brief` for a page a reader reads,
`content-slides` or `frontend-slides` for a deck.

Read `references/config-schema.md` before writing the config.
Read `references/motion-grammar.md` before choosing machines and periods.

## Why this exists

Asking a model for a video means asking it to draw a picture, then describe
motion, then hope the two agree. Here the model writes one JSON file: boxes with
lines of text, wires, packet paths, triggers, log wording, numbers. The bundled
renderer computes the packets, the counters, the state changes and the log, and
drives a real browser frame by frame. Two checkers then measure the result instead
of trusting it.

Every visual is a pure function of `t`. That is what makes the checks possible:
the renderer can seek to any instant, and a checker can read the same instant and
compare.

## Workflow

```text
1  Source    List the boxes, who calls whom, what is on call, what the log would
             say. Put the link next to every number. A number with no real source
             is simulated: say so on screen, never let it look measured.
  🔽
2  Config    Copy examples/skills-pipeline/config.json. Place boxes on a pixel
             grid. Read references/motion-grammar.md for the motion rules and the
             timing recipe. The template is never edited.
  🔽
3  Page      python3 scripts/build_page.py my.json --out page.html
             A self-contained page, no Chrome and no ffmpeg needed.
  🔽
4  Geometry  python3 scripts/check_frames.py --config my.json --out-dir frames
             Measures text overflow, text overlap and box overlap from the DOM at
             ~120 instants, exports PNGs. Fix and repeat until it exits 0.
             The checker catches geometry, not taste. Open the PNGs.
  🔽
5  Truth     python3 scripts/check_truth.py --config my.json
             Fails on an unresolved {variable} and on a number in the log that
             is not the machine's own live reading. The rule the motion grammar
             asks for and nothing else enforces.
  🔽
6  Video     python3 scripts/render.py --config my.json --out my.mp4
             Needs ffmpeg and Chrome. 30 fps H.264, silent AAC track so chat
             apps do not treat it as a GIF.
  🔽
7  Deliver   Report the paths, the frames you checked and the check results, and
             name the sources of every number on screen.
```

## The four rules

The full text and the timing numbers are in
`references/motion-grammar.md`.

- **The layout never moves.** No camera, no build-up. Any frame cut from the clip
  is a finished diagram.
- **Three tempos at once.** Fast: packets with trails on every wire, spinners,
  counters. Medium: the log scrolls, bars re-roll and flip colour past a
  threshold. Slow: side triggers light one at a time in order, their arrow takes
  the role colour and carries a packet, advice is typed out, totals accumulate.
- **One truth everywhere.** The number in the log is the number on the bar; the
  trigger the log mentions is the one lit in the rail. Hold it by generating the
  log from the same state machines that drive the boxes, and let
  `check_truth.py` confirm it.
- **No real data? Say "illustrative".** Fixed facts stay fixed with their source
  named. Anything that moves because the animation moves is the animation's own
  state, and it is labelled as such on screen.

## Elements and machines

| Need | Use |
| --- | --- |
| a titled box of text lines | `box` with `lines`; `items` for a flex row, `bar` for a meter |
| a wire with packets on it | `path` (polyline, rounded corners, arrow head) or `line` |
| a number that climbs | `counter` |
| a value that flips state past a threshold | `gauge`, with `high` / `low` labels, and `any_low` to summarise a set |
| a unit working, then done | `lane` |
| "on call" points that light in turn | `triggers`, plus `tarrow` and the `trigger` line sugar |
| a scrolling log | `log`; it has no text of its own, the machines write the rows |
| something to light up from a state | `when` / `then` on a box, path, line, run or flow |

Coordinates are absolute canvas pixels, so a config is authored for one canvas
ratio. `canvas.preset` is `4:5` (1200x1500), `3:4` (1080x1440) or `1:1`
(1080x1080); `render.py --width/--height` only rescales. For another ratio, copy
the config and re-place the boxes.

Themes: `terminal-dark` (monospace, segmented text-mode boxes) and `light-pastel`
(pastel boxes, solid borders, soft glow). Changing preset changes the font, the
line height and the colour table at the same time, so re-run `check_frames.py`
afterwards — `references/motion-grammar.md` section 7 lists what breaks.

## Determinism

`window.seek(t)` draws the frame at second `t`. No wall clock, no
`Math.random()`, no CSS animation; the few "random" picks are a fixed-seed
integer hash. `render.py` seeks and screenshots; `check_frames.py --repeat`
seeks away and back and compares pixels. Opened in a normal browser without
`?manual`, the same function is driven by `requestAnimationFrame` and loops.

## Files

- `scripts/build_page.py` — config to a self-contained page. No browser needed.
- `scripts/render.py` — the page to an H.264 mp4.
- `scripts/check_frames.py` — geometry checks, PNG export, replay determinism.
- `scripts/check_truth.py` — unresolved values and log-versus-panel numbers.
- `scripts/livepanel.py` — shared helpers, standard library only.
- `assets/template.html` — the generic page. Never edit it per diagram.
- `references/config-schema.md`, `references/motion-grammar.md`.
- `examples/skills-pipeline/config.json` — this repository's own pipeline.

## Credit rule

Put the original author and link of any picture you recreate or re-animate in the
video footer (`credit`) and in the post. State when a figure is simulated. See
`THIRD-PARTY-NOTICES.md` for what this skill is built on and who the look belongs
to.