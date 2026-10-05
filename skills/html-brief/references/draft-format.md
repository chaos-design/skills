# Draft format specification

A draft is Markdown plus fenced blocks whose info string names a component. The
renderer owns layout, colors and geometry; the draft owns content and order.

## Front matter

Optional. Keys are `key: value`, one per line, between two `---` lines.

```markdown
---
title: TCP three-way handshake
subtitle: Why the third packet cannot be removed
theme: blueprint
mode: auto
lang: auto
columns: 2
note: Sources: RFC 793, RFC 7413
---
```

| Key | Values | Default | Meaning |
| --- | --- | --- | --- |
| `title` | text | first `##` | page title, shown in the masthead |
| `subtitle` | text | none | one line under the title |
| `theme` | `blueprint`, `document` | `document` | blueprint is a ruled engineering sheet, document is an editorial memo |
| `mode` | `auto`, `light`, `dark` | `auto` | starting color mode; the toolbar can still change it |
| `lang` | `auto`, `en`, `zh`, `ja` | `auto` | auto reads the characters; `lang` sets the button labels and `<html lang>` |
| `columns` | `1`, `2` | `2` | grid width |
| `note` | text | none | colophon line |

Command-line flags `--theme`, `--mode`, `--lang`, `--columns` win over front
matter.

## Panels

Each `##` heading starts a panel. Content before the first `##` becomes the
opening panel.

```markdown
## Why this matters {span=2}

Body of the panel.

### Optional sub-heading

More body.
```

- `{span=2}` gives the panel the full grid width. Any other value is an error.
- Without the marker a panel takes one column.
- A trailing one-column panel is widened automatically, because an empty cell at
  the end of the grid reads as a missing panel.
- Deeper headings stay inside their panel. A draft with no `##` at all renders
  as a single full-width panel.

## Prose

Markdown inline: `**bold**`, `*italic*`, `` `code` ``, `~~strike~~`,
`[label](https://example.com)`, and bare URLs become links.

Block elements:

| Element | Example |
| --- | --- |
| Paragraph | plain lines |
| List | `- item` or `1. item` |
| Table | GFM table with a separator row |
| Code block | ```` ```python ```` … ```` ``` ```` |
| Quote | `> text` |
| Callout | `> warn: text`, or `> key: Title` then `> body` |

Alignment row syntax works as usual: `| --- | ---: | :---: |`.

### Table cells

These words become glyphs, so a comparison table stays scannable:

| Write | Shows |
| --- | --- |
| `ok`, `yes`, `支持` | ✓ green |
| `no`, `不支持` | ✗ red |
| `warn`, `!`, `部分` | ! amber |
| anything else | the text, unchanged |

### Callouts

`> note:`, `> tip:`, `> warn:`, `> danger:`, `> key:` followed by text.

- One paragraph is body text, however the source wraps it.
- A bare `>` line starts a second paragraph, and the first paragraph becomes
  the title.
- A completely empty line ends the quote, so it separates two callouts.

```markdown
> warn: A lossy link often loses the third packet first.
> Budget for one extra handshake, not one extra packet.

> key: Only one title per callout
>
> The body starts after a bare `>` line, so a wrapped sentence never turns
> into a half sentence title.
```

The tag follows the page language: Note / 注记 / メモ, Warning / 警告.

## Components

A component is a fenced block whose info string starts with the component name.

### flow

```markdown
```flow LR
(Client) -> Gateway: TLS
Gateway -> {token valid}: check
{token valid} -> [*Response]*: allow
{token valid} -> [(Audit log)]: deny
Gateway -.-> Cache: stale read
Cache ==> Gateway: refresh
```
```

- `LR` (default in the examples) lays out left to right, `TB` top to bottom.
- Node shapes use Mermaid-style brackets: `(Start)` stadium, `{Decision}`
  diamond, `[(Store)]` cylinder, `[[Queue]]` parallelogram, `((Service))`
  rounded. A plain name is a rectangle.
- `*Name*` emphasises a node.
- Arrows: `->` solid, `-.->` dashed, `==>` thick.
- A pair of opposite arrows between the same two nodes draws the answer on a
  lane below the pair, so request and response never overlap.
- Cyclic edges route around the outside of the drawing.
- Layers are ordered to cut edge crossings: alternating median sweeps, then
  bounded local swaps. The swap budget exists because its returns flatten — on
  random graphs it removes about 9% of what the sweeps leave, and nearly all of
  that arrives within the first couple of hundred probes per layer pair.
- A node label that starts with `[` is rejected: brackets are not a shape here.
- Groups frame the nodes first declared inside them:

```markdown
```flow TB
group Edge {
  WAF -> Gateway: filter
}
Gateway -> Service: forward
```
```

### sequence

```markdown
```sequence num
participant C as Client
C -> S: SYN
S -.-> C: SYN-ACK
activate S
C -> S: ACK
note C, S: ESTABLISHED
alt timeout {
  C -> S: retry
} else ok {
  C -> Done: close
}
deactivate S
```
```

- Participants appear in first-use order, left to right.
- `participant X as Label` renames a box without changing the lane name.
- `->` solid, `-.->` dashed, `==>` thick; `num` numbers the messages.
- `note A, B: text` draws a box across those lanes.
- `activate` / `deactivate` draw the activation bar.
- `alt`, `opt`, `loop`, `par`, `try`, `critical`, `break` open a fragment;
  `} else <label> {` starts the next branch. Fragments may nest: a nested
  frame steps inwards so its tab stays readable inside the outer frame.

### tree

```markdown
```tree
skills
  html-brief
    SKILL.md
    scripts
      html_brief.py
```
```

Two spaces or one tab per level. The first line is the root.

### timeline

```markdown
```timeline
2024-01 | First release | solo project
2025-06 | GA | 10k installs
*2026-02 | Stable | two themes
```
```

`date | title | description`. A leading `*` highlights the entry.

### limits

```markdown
```limits
Context used | 142k of 200k | 71% | p99 across 30 days
Error budget | 3h of 10h | 30% | last quarter
```
```

`name | value | percent | note`. The percentage must be 0-100. The bar turns
amber at 75 and red at 90, so a full bar always means the same thing.

### stat

```markdown
```stat
Output tokens | 923 | -87% | good
Render time | 48ms | -12% | good
```
```

`name | value | delta | status` with status `good`, `warn` or `bad`. The last two
fields are optional.

### kv

```markdown
```kv
Owner | Platform team
Status | GA
```
```

`key | value`. Extra fields join with ` · `.

### annot

```markdown
```annot
The {bad|service} {warn|was restarted} before the {fix|retry budget expired}.
```
```

`{kind|text}` or `{kind|text::why}`, with kind `bad`, `warn`, `good` or `fix`.
Marks are numbered in reading order and the reasons are listed underneath.

## Writing check

Rules adapted from ASD-STE100, applied to prose only:

| Rule | Threshold |
| --- | --- |
| Sentence length | 25 English words, 45 Chinese characters |
| Paragraph length | 6 sentences |
| List item length | 30 words |
| Passive voice | any occurrence in English |
| Wordy pairs | in order to, prior to, utilize, leverage, due to the fact that, … |
| Chinese empty verbs | 进行优化, 开展分析, 加以说明, … |
| Chinese 的 density | 3 or more in one sentence |
| Stock phrases | 赋能, 闭环, 抓手, 颗粒度 |

`--check off` skips the check, `--check warn` prints findings and renders,
`--check strict` refuses to render while any finding remains.

## Errors

Every failure names the line, the component and a correct form:

```text
draft.md:26 · flow: node `[Cookie present]` uses square brackets, which are part of the label
  correct form: ```flow LR
Gateway -> Service: rpc
{payload ok} -> Cache: read
(Query) -> *Response*
group Edge {
  A -> B
}
```
```

Common cases: an unknown component or language in a fence, a flow line without an
arrow, a table row with the wrong cell count, a percentage outside 0-100, a
timeline line that is not `date | title | description`, a fragment closed without
being opened, and a `##` missing before a deeper heading.

## Validation

```bash
# renders every bundled draft and asserts the page stays self-contained
python3 scripts/html_brief.py validate --out-dir out

# re-derives panels, headings, language, callout titles, table glyphs, limit
# bars and sequence order from the draft and compares them with the page
python3 scripts/check_semantics.py

# renders every bundled draft in headless Chrome and fails when a diagram label
# leaves its viewBox or the page scrolls sideways
python3 scripts/check_layout.py
```

`check_semantics.py` keeps its own small parser on purpose. If it reused the
renderer's parser, a parser bug would agree with itself and stay invisible.

It also holds the embedded source to a round trip: whatever a draft contains,
reading it back out of the page must return the draft unchanged, and no closing
tag variant may terminate the script element early. `check_semantics.py` proves
that with a parser rather than a string search, because a string search and a
browser disagree on forms such as `</SCRIPT >`.

Finally it renders hostile drafts — a script tag, an event handler, a
`javascript:` url — and reports anything the browser would act on. That check
uses a parser for the same reason: `<p>" onmouseover="x</p>` is escaped prose, and
only a parser can tell it apart from a real event handler.

## Determinism

The same draft and the same flags produce the same bytes. The generation stamp
is the only variable input: pin it with `--date 'YYYY-MM-DD HH:MM:SS'` or
`SOURCE_DATE_EPOCH`, or remove it with `--no-date`.