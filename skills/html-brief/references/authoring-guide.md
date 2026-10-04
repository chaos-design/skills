# Authoring guide

How to brief, what to leave out, and what a page can honestly promise.

## Decide whether a page is the right answer

Write a page when the answer has any of these shapes:

- several concepts that only make sense next to each other
- a flow with branches, retries or failure paths
- messages exchanged between parties over time
- a comparison with more than two options
- a history, a release line or a roadmap
- a number that needs a reference point, such as a limit or a delta

Answer in prose when the answer is one fact, one command, a list of file names,
or a yes/no. A page for a one-line answer costs the reader a scroll.

If the user asks for HTML anyway, make the page and keep it to two or three
panels.

## Size the page

One page means 4 to 8 panels. Past that, the reader stops scanning and starts
scrolling.

When a draft grows too large, cut in this order:

1. Remove the panel that repeats another panel.
2. Turn prose into a table row or a diagram label.
3. Split into a second brief and link to it in the `note` field.

Do not shrink the type, and do not drop a diagram to save space.

## Panel order

Put the answer first. A reader should get the conclusion from the first panel
without scrolling.

```text
conclusion → evidence → how it works → numbers → what to do next
```

Order panels so each one answers a question the previous one raised. A timeline
of a project belongs after the explanation of the project, not before it.

## Choosing components

| The reader wants to | Component |
| --- | --- |
| see how a request moves | `flow LR` |
| see what a system does over time | `flow TB` or `timeline` |
| see who says what to whom | `sequence` |
| see what is inside | `tree` |
| see a value against a limit | `limits` |
| see three numbers | `stat` |
| see how two options differ | table with `ok` / `no` / `warn` |
| see who owns a decision | `kv` |
| see what is wrong with a sentence | `annot` |
| remember one rule | `key` callout |

## Label discipline

Diagram labels are read as a set. Keep them short and parallel:

```markdown
```flow LR
(API) -> Redis: GET
Redis -.-> API: miss
API -> [(DB)]: SELECT
```
```

Not this, which the renderer must wrap into three lines per box:

```markdown
```flow LR
(Application programming interface) -> (Redis in-memory store): GET session key
```
```

Rules of thumb:

- 24 characters or fewer per label.
- Use the same grammar on both ends: verbs on the arrow, nouns in the boxes.
- Do not repeat the panel title inside the diagram.
- Name the actor, not the abstraction: `Client`, `Payment service`, not `Party A`.

## Numbers

Only put a number on the page when it has a source in the draft. If a number is
missing, leave the panel out or write that it is unknown.

- `limits` needs a denominator. `85%` without "of what" is decoration.
- `stat` needs a direction. `-18%` means nothing until the reader knows what fell.
- Comparisons use the same units in every row.
- Rounding is fine if the unit is stated. `1.8ms` and `320ms` can share a table
  only if the reader can tell which is which.

## Honesty

- Do not invent dates, versions, sources or quotes.
- If a claim depends on a source, name it in `note` or inside the panel.
- If the user asks for a recommendation, state the conditions under which it
  holds. `> warn:` exists for the case where the reader would act wrongly.
- Mark inference as inference: `> note:` for context, `> danger:` for the case
  where being wrong is expensive.

## Languages

The page renders one language per draft. Chinese, English and Japanese are
supported for button labels and callout tags; the language is detected from the
characters unless `lang` says otherwise.

Mixed drafts work: technical terms stay in English inside Chinese prose, and the
writing check applies the length limit that matches the sentence's script.

## Themes and modes

- `document` for analysis, reviews and anything with long prose.
- `blueprint` for architecture, protocol and specification material.
- `mode: auto` respects the reader's system setting, which is the right default
  for a page that will be shared.

Do not hard-code a theme per panel. A page that mixes two visual languages reads
as two documents.

## Before delivering

1. Render it.
2. Read the rendered page, not the draft. Panels often need a title that matches
   what the diagram actually shows.
3. Run `python3 scripts/html_brief.py check draft.md` and fix what it reports.
4. Look at one panel in both themes, and one diagram at a narrow width.
5. Tell the user the file path, the components used, and the check results.