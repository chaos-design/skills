---
title: Skill repository content pipeline
subtitle: How one skill feeds the others, and where each writes its output
theme: document
mode: auto
columns: 2
---

## Pipeline {span=2}

`web-markdown` is the shared entry point. Every content skill takes its output
instead of fetching a URL on its own, so one fetcher failure has one fix.

```flow LR
(URL) -> web-markdown: normalize
web-markdown -> x-tweet-fetcher: platform bridge
x-tweet-fetcher -> web-markdown: text
web-markdown -> bilingual-reader: Markdown
web-markdown -> content-slides: Markdown
web-markdown -> frontend-slides: Markdown
web-markdown -> html-brief: Markdown draft
bilingual-reader -> [(preview pages)]
content-slides -> [(slide deck)]
frontend-slides -> [(slide pages)]
html-brief -> [(one-page brief)]
```

## Repository layout {span=2}

```tree
skills
  web-markdown
    SKILL.md
    scripts
      web_markdown.py
  x-tweet-fetcher
    SKILL.md
    scripts
  bilingual-reader
    SKILL.md
    references
  content-slides
    SKILL.md
  frontend-slides
    SKILL.md
  html-brief
    SKILL.md
    scripts
      html_brief.py
tests
  bilingual-reader
  content-slides
  frontend-slides
  html-brief
  web-markdown
  index.html
```

## Ownership {span=2}

```kv
Entry point | web-markdown
Platform bridge | x-tweet-fetcher
Reading output | bilingual-reader
Slide output | content-slides, frontend-slides
Brief output | html-brief
Shared preview | tests/index.html
```

## Rules that hold everywhere

> key: Each skill writes only under its own tests folder, and never moves or
> renames another skill's output.

- A skill that needs another skill asks before installing it and shows the exact
  `npx skills add` command.
- A missing runtime dependency is reported as a blocked test, never replaced
  with mock or placeholder output.
- Generated dates use UTC+8 in the format `YYYY-MM-DD HH:mm:ss`.
- Preview links in `tests/index.html` are added, never rewritten.

## Coverage today

| Skill | Tests folder | Preview link |
| --- | --- | --- |
| `web-markdown` | yes | no |
| `bilingual-reader` | yes | yes |
| `content-slides` | yes | yes |
| `frontend-slides` | yes | yes |
| `html-brief` | yes | yes |
| `x-tweet-fetcher` | yes | no |