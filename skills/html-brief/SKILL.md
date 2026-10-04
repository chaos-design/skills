---
name: html-brief
description: >
  Turns a complex question, review, comparison or explanation into one
  self-contained HTML brief with computed panel layout, flow and sequence
  diagrams, comparison tables and a theme switch. The agent writes a short
  Markdown draft; the bundled renderer computes geometry, colors and themes, so
  the page reads like a document instead of a wall of text. Invoke when the user
  asks for an HTML brief, one-pager, explainer page, decision memo, architecture
  map, timeline or diagram page, or asks to explain, compare or review something
  visually instead of in prose.
---

# HTML Brief

Use this skill when an answer is too structured for prose: several concepts, a
multi-step flow, a protocol exchange, a comparison, a history, or a decision
with numbers attached. The deliverable is one HTML file that opens offline and
can be forwarded as-is.

Do not use it for a one-line answer, plain text output, or a slide deck. Use
`content-slides` or `frontend-slides` for decks.

Read `references/draft-format.md` before writing the first draft. Read
`references/authoring-guide.md` before writing about money, risk or anything
else a reader will act on.

## Why this exists

Asking a model for HTML directly means it types every wrapper, every CSS rule
and every SVG coordinate. The output tokens are what the user waits for. Here
the model writes content only, and `scripts/html_brief.py` computes panel
placement, diagram coordinates, label wrapping, themes and the light/dark
switch. A typical brief is a few hundred output tokens of draft instead of
thousands of tokens of markup.

## Workflow

```text
1  Decide    Is the answer worth a page? Related concepts, flows, comparisons,
             histories. One fact or one command gets a sentence, not a page.
  🔽
2  Gather    Use web-markdown when the source is a URL or a document. Keep the
             facts, numbers, dates and names from the real source.
  🔽
3  Outline   List the panels first: 4 to 8 sections, each with one job. Add
             {span=2} to a heading that needs the full width.
  🔽
4  Draft     Write the Markdown draft with the component that matches each
             shape of information. Aim for one page; cut a panel before you
             shrink the type.
  🔽
5  Render    python3 scripts/html_brief.py render draft.md --out brief.html
  🔽
6  Fix       The renderer reports the line number, the component and a correct
             example. Fix that line, re-render. Never hand-edit the HTML.
  🔽
7  Deliver   Report the file path, the panels used and the check results.
```

## Components

Pick the component by the shape of the information, not by habit.

| Component | Use for | Lines |
| --- | --- | --- |
| `flow LR` / `flow TB` | Architecture, request paths, state machines, decisions | `A -> B: label` |
| `sequence` | Messages between parties over time, protocols | `Client -> Server: SYN` |
| `tree` | Folder layouts, module maps, taxonomies | `repo` + two-space indent |
| `timeline` | Releases, phases, history | `2024-01 \| First release \| note` |
| `limits` | A value against its limit, budgets, quotas | `Name \| value \| 85% \| note` |
| `stat` | Headline numbers with a direction | `Name \| value \| -18% \| good` |
| `kv` | Metadata, a title block, a decision record | `Owner \| Platform team` |
| `annot` | Reviewing a sentence word by word | `{bad\|word :: why}` |
| Markdown table | Multi-way comparison, `ok` / `no` / `warn` become ✓ ✗ ! | `\| A \| B \|` |
| Blockquote | A conclusion, tip, warning or risk | `> warn: text`; a bare `>` line adds a title |

Full syntax, node shapes, groups, fragments and every error message are in
`references/draft-format.md`.

## Commands

```bash
# render one draft
python3 scripts/html_brief.py render draft.md --out brief.html

# render into a stable folder, keep the browser closed
python3 scripts/html_brief.py render draft.md --out-dir out --quiet

# read the draft from stdin
cat draft.md | python3 scripts/html_brief.py render -

# writing findings only, machine readable
python3 scripts/html_brief.py check draft.md --json

# render every bundled example and assert the page stays self-contained
python3 scripts/html_brief.py validate --out-dir out

# prove no diagram label is clipped, needs a local Chrome, writes nothing
python3 scripts/check_layout.py
```

Useful flags: `--theme blueprint|document`, `--mode auto|light|dark`,
`--lang auto|en|zh|ja`, `--columns 1|2`, `--date 'YYYY-MM-DD HH:MM:SS'`
(UTC+8), `--no-date`, `--check off|warn|strict`, `--open`, `--force`.

The writing check runs by default and only warns. Use `--check strict` when the
brief is final: the renderer refuses to write a page while findings remain.

## Draft rules

1. Front matter first: `title`, optional `subtitle`, `theme`, `mode`, `lang`,
   `columns`, `note`.
2. One `##` heading per panel. Deeper headings become sub-headings inside a
   panel. Content before the first `##` becomes the opening panel.
3. `{span=2}` on a `##` heading gives that panel the full width. A trailing
   narrow panel is widened automatically so the grid never ends with a hole.
4. Node shapes use Mermaid-style brackets: `(Start)` stadium, `{Decision}`
   diamond, `[(Store)]` cylinder, `[[Queue]]` parallelogram, `*Result*`
   emphasised. Square brackets alone are literal text and are rejected.
5. Labels are short. The renderer wraps long labels; it cannot invent a shorter
   one. Prefer `rpc` over `RPC call from the gateway to the billing service`.
6. Never write coordinates, colours, CSS or SVG. The renderer owns layout.
7. Keep prose short: 25 words per English sentence, 45 characters per Chinese
   sentence, at most 6 sentences per paragraph.

## Output contract

- One `.html` file, no CDN, no web font, no remote image, no JavaScript
  dependency. It opens offline and can be attached to a ticket.
- The masthead shows the title, the subtitle, the UTC+8 generation stamp and
  the source path.
- The toolbar switches theme, switches light/dark/auto and copies the source
  draft. Choices persist in `localStorage`.
- The draft is embedded in the page, so the source can always be recovered.
- Diagrams are SVG with a `<title>` and an `aria-label`, and every figure scrolls
  rather than overflowing on a narrow screen.

## Validation before reporting success

```bash
python3 scripts/html_brief.py validate --out-dir <folder>
python3 scripts/check_layout.py
python3 scripts/html_brief.py check <draft.md>
```

Then open the page and confirm: both themes, light and dark, the widest panel,
one diagram per component type, and a narrow viewport around 390px. Report which
commands ran and any check that could not run.

## Hard rules

- Never invent data, dates, sources or quotes. Missing facts stay missing or
  become an explicit "needs input" panel.
- Never hand-edit generated HTML. Fix the draft and re-render.
- Never add an external resource. If a draft needs an image, describe it in
  words instead.
- Never render a page from a draft that still has findings when `--check strict`
  is in effect.
- Keep every generated file for one skill inside that skill's own folder.
- Keep file names lowercase with hyphens.

## Files

- `scripts/html_brief.py` — CLI entry point.
- `scripts/briefkit/parser.py` — front matter, Markdown blocks, component
  parsing, and every error message with a line number.
- `scripts/briefkit/diagrams.py` — flow, sequence, tree and timeline layout.
- `scripts/briefkit/blocks.py` — prose, tables, callouts and data components.
- `scripts/briefkit/render.py` — panel grid, masthead, toolbar.
- `scripts/briefkit/theme.py` — light and dark variables, two themes.
- `scripts/briefkit/check.py` — writing check.
- `scripts/check_layout.py` — headless browser check for clipped labels; needs a
  local Chrome, Edge or Chromium, and reports itself as skipped without one.
- `references/draft-format.md` — the draft specification.
- `references/authoring-guide.md` — how to brief, and what not to promise.
- `examples/` — five complete drafts.