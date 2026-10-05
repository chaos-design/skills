# HTML Brief

[中文](./README.zh-CN.md)

Turn a complex answer into one HTML page a human can read. The agent writes a
short Markdown draft; a bundled renderer computes panel layout, diagram
coordinates, label wrapping, themes and the light/dark switch.

<img src="../../screenshots/html-brief/blueprint-tcp-handshake.png" width="860" alt="HTML Brief, blueprint theme, TCP handshake example">

## Why not just ask for HTML

A model asked for HTML directly has to type every wrapper, every CSS rule and
every SVG coordinate. Output tokens are also what the reader waits for.

With this skill the model writes content only. A typical brief is a few hundred
output tokens of draft; the renderer does the rest. Every label position, arrow
route and grid cell is computed, not guessed.

## What you ask, what you get

| You ask | You get |
| --- | --- |
| "Explain the TCP three-way handshake" | A sequence diagram, a state flow and a comparison table |
| "Map how the skills in this repo feed each other" | A pipeline flow, a folder tree and a fact table |
| "Redis or Memcached for the cache?" | A table with ✓ ✗ !, a request flow, limits and a migration list |
| "How did TCP congestion control evolve?" | A timeline, a comparison table and a recovery loop |
| "What is wrong with this paragraph?" | Word-level annotations with a reason for each mark |
| "How do I show hidden files with `ls`?" | No page. One line of question gets one line of answer |

The agent decides whether a page is worth it: related concepts, multi-step
flows, multi-way comparisons, histories, numbers against limits. You can also
just say "explain it as an HTML brief".

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill html-brief
```

No `npm install`, no `pip install`. The renderer is Python 3 standard library
only, and it travels with the skill.

## Use it from an agent

```bash
cd skills/html-brief

# render a draft
python3 scripts/html_brief.py render draft.md --out brief.html

# writing findings only
python3 scripts/html_brief.py check draft.md

# render every bundled example and assert the page stays self-contained
python3 scripts/html_brief.py validate --out-dir out

# prove the page still says what the draft says, no browser needed
python3 scripts/check_semantics.py

# prove no diagram label is clipped (uses a local Chrome, writes nothing)
python3 scripts/check_layout.py
```

`html_brief.py` accepts a bare path as shorthand for `render`, and `-` reads the
draft from stdin:

```bash
cat draft.md | python3 scripts/html_brief.py render - --out brief.html
```

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--theme blueprint\|document` | override front matter; blueprint is a ruled engineering sheet, document is an editorial memo |
| `--mode auto\|light\|dark` | starting color mode |
| `--lang auto\|en\|zh\|ja` | button labels, callout tags and `<html lang>` |
| `--columns 1\|2` | grid width |
| `--out-dir DIR` | write `<slug>.html` into a folder instead of one file |
| `--date 'YYYY-MM-DD HH:MM:SS'` | pin the UTC+8 stamp for reproducible output |
| `--no-date` | omit the stamp entirely |
| `--check off\|warn\|strict` | writing check; `strict` refuses to render while findings remain |
| `--open` | open the page in a browser when it is written |
| `--force` | overwrite instead of writing `name-2.html` |

## The draft

```markdown
---
title: TCP three-way handshake
subtitle: Why the third packet cannot be removed
theme: blueprint
---

## The exchange {span=2}

```sequence num
Client -> Server: SYN, seq=x
Server -.-> Client: SYN-ACK, seq=y, ack=x+1
Client -> Server: ACK, ack=y+1
```

## State changes

```flow TB
(CLOSED) -> LISTEN: passive open
LISTEN -> SYN-RECEIVED: get SYN
SYN-RECEIVED -> *ESTABLISHED*: get ACK
```
```

Each `##` is a panel. `{span=2}` gives it the full width. Everything else is
Markdown. The full specification, including node shapes, groups, fragments and
every error message, is in
[references/draft-format.md](./references/draft-format.md).

## Components

| Component | Use for |
| --- | --- |
| `flow LR` / `flow TB` | Architecture, request paths, state machines, decisions |
| `sequence` | Messages between parties over time, with notes, activations and `alt` / `else` fragments |
| `tree` | Folder layouts, module maps, taxonomies |
| `timeline` | Releases, phases, history |
| `limits` | A value against its limit |
| `stat` | Headline numbers with a direction |
| `kv` | Metadata and title blocks |
| `annot` | Word-level review of a sentence |
| Tables | Multi-way comparison; `ok` / `no` / `warn` become ✓ ✗ ! |
| Callouts | `> note:`, `> tip:`, `> warn:`, `> danger:`, `> key:` |

Layout is computed: nodes are sized from measured label text, layers are ordered
to reduce crossings, return arrows get their own lane, and labels are wrapped so
they never collide.

<img src="../../screenshots/html-brief/document-cache-choice.png" width="860" alt="HTML Brief, document theme, Chinese cache decision example">

## What the page contains

- One `.html` file. No CDN, no web font, no remote image, no dependency.
- A masthead with the title, the subtitle, the UTC+8 stamp and the source path.
- A toolbar that switches theme, cycles light / dark / auto, and copies the
  source draft. The choice persists in `localStorage`.
- The draft embedded in the page, so the source is always recoverable.
- SVG diagrams with a `<title>` and an `aria-label`.
- A print stylesheet that drops the toolbar and keeps panels intact.
- A single column below 880px, with figures that scroll instead of overflowing.

## Writing check

Rules adapted from [ASD-STE100](https://www.asd-ste100.org/), the controlled
English used in aircraft maintenance manuals. Only what a machine can judge is
checked:

- sentence length: 25 English words or 45 Chinese characters
- paragraph length: 6 sentences
- English passive voice
- wordy pairs such as *in order to*, *prior to*, *utilize*
- Chinese empty verbs such as *进行优化*
- three or more 的 in one sentence
- stock phrases such as 赋能 and 闭环

Findings warn by default. `--check strict` refuses to render, which is the right
gate before a brief is shared.

## Examples

| Draft | Shows |
| --- | --- |
| `examples/tcp-handshake.md` | Sequence with notes, state flow, comparison table, limits |
| `examples/skill-pipeline.md` | Wide pipeline flow, folder tree, ownership block |
| `examples/congestion-control-history.md` | Timeline with a highlighted entry, comparison table, recovery loop |
| `examples/cache-choice.zh-cn.md` | Chinese brief: cache decision with verdict, table, flow, limits, steps |
| `examples/writing-check.md` | Annotations, findings panel and the fix loop |

Render all of them with:

```bash
python3 scripts/html_brief.py examples --out-dir out
```

## Validation

```bash
# renders every example and checks doctype, embedded CSS, embedded source and
# the absence of any external URL
python3 scripts/html_brief.py validate --out-dir out

# re-derives the expected structure from each draft and compares it with the
# rendered page
python3 scripts/check_semantics.py

# renders every example in headless Chrome and fails if any diagram label
# leaves its viewBox or the page scrolls sideways
python3 scripts/check_layout.py
```

`check_semantics.py` is the one that catches meaning rather than breakage. It
re-reads each draft with its own small parser and asserts:

| Asserted | What it catches |
| --- | --- |
| the embedded source matches the draft byte for byte | escaping or truncation |
| panel count and headings match the `##` lines | a panel or its title lost |
| an explicit `lang:` reaches `<html lang>` | the front matter ignored |
| the toolbar and callout tags match that language | an English page with Chinese controls |
| a callout has a title only when its quote has two paragraphs | a title turned into body |
| every `ok` / `no` / `warn` cell produced one glyph | a comparison column lost |
| every limits row produced a bar at the declared percentage | a wrong number on a bar |
| sequence participants appear in first-use order | lanes drawn in the wrong order |
| every figure has a title, an aria-label and a viewBox | a diagram left unnamed |
| two renders of one draft are identical | hidden nondeterminism |
| one render stays inside its wall-clock budget | a layout change that trades seconds for milliseconds of polish |
| the embedded source reads back unchanged and no closing-tag variant escapes it | a draft becoming executable markup |
| no injected payload becomes live markup anywhere on the page | a script tag, event handler or `javascript:` url reaching the reader |

A small snapshot in the script also pins each example's title, language, panel
count and diagram kinds, so an intentional change has to be a deliberate edit.

`check_layout.py` needs a local Chrome, Edge or Chromium. Without one it reports
the check as skipped and exits 0; it never reports a pass it did not measure.

Both checkers write into a temporary folder and leave the repository alone.

## Known limits

- Diagram geometry uses an estimate of text width, not font metrics. The
  estimate is padded, and `check_layout.py` measures the result in a browser.
  Fonts far from the system stack may shift a label by a pixel or two.
- The writer's font stack is fixed to system fonts on purpose. A page with no web
  font request cannot be restyled by a reader.
- One language per page. Mixed-language drafts render correctly; the button
  labels follow `lang`.
- The writing check judges prose only. It does not judge a diagram for accuracy.

## Project layout

```text
skills/html-brief/
  SKILL.md
  README.md
  README.zh-CN.md
  manifest.json
  LICENSE
  examples/            five complete drafts
  references/          draft format and authoring guide
  scripts/
    html_brief.py      CLI entry point
    check_semantics.py semantic checks against the draft
    check_layout.py    headless browser layout check
    briefkit/          parser, diagrams, blocks, theme, render, check
tests/html-brief/      generated previews, one folder per example
screenshots/html-brief/
```

## License

Apache-2.0, the same license as the rest of this repository. See
[LICENSE](./LICENSE).

## Credits

`html-brief` was modeled on
[answer-me-with-html](https://github.com/QingYunA/answer-me-with-html). It
keeps the same split: an agent writes a short Markdown draft, and a program
decides the layout, the diagrams and the theme.
