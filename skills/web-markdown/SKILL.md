---
name: web-markdown
description: >
  Converts URLs, PDFs, DOCX files, Markdown files, plain text, screenshots, and
  pasted notes into faithful Markdown archives using Microsoft MarkItDown, with
  Camofox as a rendered URL fallback and an auditable extraction harness. Invoke
  when users ask to fetch, archive, preserve, or convert web/document content
  into Markdown, except specialized social/content platforms handled by
  url-content-fetcher.
---

# Web Markdown

Use this skill for faithful Markdown extraction from URLs, PDFs, DOCX files,
Markdown/plain-text files, screenshots/images, or pasted notes. The deliverable
is source-preserving Markdown, not a summary, translation, article redesign, web
app, dashboard, or slide deck.

Before any conversion, read `references/harness.md`.

## Workflow Overview

Use this checkpointed workflow when the user wants a durable, auditable Markdown
archive rather than a one-off conversion. Keep checkpoints explicit for
multi-input, low-confidence, or publishable archival work. For simple one-off
conversions, run the same phases inline without creating extra files beyond the
Markdown output.

```
Phase 0  Intake
         Decide whether web-markdown applies, reject unsafe inputs, route
         social/content platforms to url-content-fetcher, and choose one-off
         or workspace mode.
  🔽
Phase 1  Source -> Markdown
         Capture original source reference, run MarkItDown, and for URLs use
         Camofox rendered fallback only after direct conversion fails.
  🔽
Phase 2  Persist
         Write web/<slug>.md by default or source/original.md in workspace mode.
         Never overwrite; use numeric suffixes.
  🔽
Phase 3  Extraction Notes
         Write source/extraction-notes.md only when requested, when fallback or
         repair was needed, for medium/low confidence sources, or for
         multi-input traceability.
  🔽
Phase 4  Validation
         Run the inline checklist for title, source metadata, non-empty body,
         code fences, images, links, source language, and notes accuracy.
  🔽
Phase 5  Review / Repair
         Complex or low-confidence sources may use a reviewer/subagent and
         write review/source-review.md. Repair minimal slices and rerun
         validation.
  🔽
Phase 6  Delivery
         Report Markdown path, word count, source, confidence, notes path when
         present, and any residual risk.
```

## Checkpoints

A: after intake, stop only when the source is ambiguous, unsafe, or requires another skill.
B: after conversion, stop only when validation fails, coverage is low-confidence, or manual review was requested.
C: before delivery, stop only when a reviewer found unresolved source-loss risk.

## Durable Workspace Shape

```text
<workspace>/
  source/   original.url|original.*  original.md  original.<lang>.md  extraction-notes.md
  review/   source-review.md
```

`review/source-review.md` is not a routine artifact. Create it only for
complex, low-confidence, or user-requested review cases.

## Boundary Check

Do not use this skill for X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, or
WeChat Articles. Route those URLs to `url-content-fetcher`; that skill owns any
internal `x-tweet-fetcher` setup for X/Twitter.

```bash
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

Reject shell commands, JavaScript/data URLs, directories, embedded credentials,
login-only content, paywalls, and private workspaces unless the user provides an
accessible source. Do not summarise, translate, paraphrase, reorder, or add
editorial notes unless the user separately asks after faithful extraction.

## Workflow

1. Intake: confirm this skill applies, reject unsafe inputs, and choose one-off
   mode (`web/<slug>.md`) or workspace mode (`source/original.md` plus optional
   `source/original.<lang>.md` and `source/extraction-notes.md`).
2. Convert: use MarkItDown first. For URLs, use Camofox-rendered HTML only when
   direct conversion fails or misses JavaScript-rendered content.
3. Persist: write UTF-8 Markdown without overwriting existing files; append
   `-2`, `-3`, etc. when needed.
4. Validate: check title, source metadata, non-empty body, balanced code fences,
   source order, images, links, language preservation, and notes accuracy.
5. Repair: fix minimal slices and rerun validation before reporting success.
6. Deliver: report Markdown path, word count, source, confidence, and notes path
   when present.

Create `review/source-review.md` only for complex, low-confidence, or
user-requested review cases, or when a translated `original.<lang>.md` is
produced. Review must compare generated Markdown with the real source content.

## Markdown Requirements

1. Convert the complete extracted content without summarising, translating,
   paraphrasing, or dropping normal text, images, links, lists, tables,
   blockquotes, inline code, or fenced code blocks.
2. Preserve source order. The Markdown must follow the same reading sequence as
   the rendered page or document.
3. Preserve images as Markdown image links. Use existing `alt` text when
   present; leave alt text empty when absent.
4. Preserve code exactly. Inline `<code>` becomes inline Markdown code, and
   `<pre>` / multi-line code blocks become fenced code blocks. Drop rendered
   line-number gutters and add a language hint when it can be inferred from
   `language-*`, `highlight-source-*`, or `data-language`.
5. Preserve outbound links as Markdown links with original hrefs resolved
   against the source URL. Do not shorten, redirect, rewrite, or remove links.
6. Format nested Markdown structures with 2-space indentation while preserving
   fenced-code indentation exactly as extracted.
7. Surface failures honestly. If MarkItDown is unavailable, the input cannot be
   converted, the URL cannot be rendered, or validation fails, stop and report
   the concrete error instead of producing a partial archive.

## Script

```bash
python3 skills/web-markdown/scripts/web_markdown.py \
  "https://example.com/article" \
  --output web/example-article.md \
  --notes-output source/extraction-notes.md
```

Supported inputs: HTTP(S) URL, PDF, DOCX, Markdown, text file, screenshot/image,
PPTX, XLS/XLSX, CSV, JSON, XML, EPUB, ZIP, `--text`, `--stdin`, and
`--html-file` for local verification.

## Runtime Requirements

Install MarkItDown with document/image extras before converting:

```bash
pip install 'markitdown[all]'
```

## Camofox Requirement

Camofox is required only for URL fallback rendering and must be running locally
on port `9377` when direct MarkItDown URL conversion fails.

```bash
curl http://localhost:9377/health
```

## Output Contract

The Markdown starts with source metadata followed by the extracted content:

```markdown
# <Detected page title>

> Source: <URL>
> Fetched: <YYYY-MM-DD HH:mm:ss>

<Complete rendered main content converted to Markdown>
```

When the page has no reliable title, use the source host as the heading. Do not
invent author names, dates, summaries, tags, or image captions.

Extraction notes, when written, must include:

```markdown
# Extraction Notes

- Source: <URL-or-file>
- Output: <path>
- Source Language: <source-language>
- Target Language: <target-language-or-none>
- Translated Source: <path-or-none>
- Method: <markitdown-direct|markitdown-file|camofox-fallback|html-file|text|stdin>
- Confidence: <high|medium|low>
- Issues: <none-or-list>
- Validation: <pass|fail>
```
