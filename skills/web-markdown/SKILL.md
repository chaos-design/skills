---
name: web-markdown
description: >
  Converts URLs, PDFs, DOCX files, Markdown files, plain text, screenshots, and
  pasted notes into faithful Markdown archives using Microsoft MarkItDown, with
  platform-aware URL fetcher bridging, Camofox as a rendered URL fallback, and
  an auditable extraction harness. Invoke when users ask to fetch, archive,
  preserve, or convert web/document/social/content URLs into Markdown.
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
         Validate safety, classify the resource type first, and choose the
         execution route before checking conversion dependencies.
  🔽
Phase 1  Source -> Markdown
         Route X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, and WeChat to
         x-tweet-fetcher. Route generic URLs/files/text/HTML to MarkItDown,
         with Camofox only as generic URL or HTML fallback.
  🔽
Phase 2  Prepare
         Derive the target path and notes path. Do not write final output yet.
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
         Use review only for low confidence, failed validation, translated
         source copies, or explicit user request. Repair minimal slices.
  🔽
Phase 6  User Confirmation
         After validation/review passes and before writing output, call
         AskUserQuestion to ask whether the user wants modifications.
  🔽
Phase 7  Delivery
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

Use this skill directly for generic web URLs and platform-specific social or
content URLs, including X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, and
WeChat Articles. Platform routing is a preflight rule: once the URL host is
classified as one of those platforms, call the local `x-tweet-fetcher` scripts
before checking MarkItDown or Camofox. Only generic URLs, files, and pasted text
continue to MarkItDown.

Reject shell commands, JavaScript/data URLs, directories, embedded credentials,
login-only content, paywalls, and private workspaces unless the user provides an
accessible source. Do not summarise, translate, paraphrase, reorder, or add
editorial notes unless the user separately asks after faithful extraction.

## Workflow

1. Intake: confirm this skill applies, reject unsafe inputs, classify the input
   as platform URL, generic URL, local file, rendered HTML, text, or stdin, and
   choose one-off mode (`web/<slug>.md`) or workspace mode.
2. Convert: for X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, and WeChat,
   route to `x-tweet-fetcher`. For generic URLs, files, pasted text, stdin, and
   `--html-file`, use MarkItDown first. If MarkItDown fails for generic URL or
   HTML, try Camofox-rendered HTML and then the built-in HTML parser fallback.
3. Prepare output: derive the target path without overwriting existing files;
   append `-2`, `-3`, etc. when needed.
4. Validate: check title, source metadata, non-empty body, balanced code fences,
   source order, images, links, language preservation, and notes accuracy.
5. Review/repair: review only when confidence is low, validation fails, a
   translated source copy is produced, or the user asks. Fix minimal slices and
   rerun validation before reporting success.
6. Confirm: after validation/review passes and before final output, call
   `AskUserQuestion` with the question "是否需要修改生成的 Markdown？". If the
   user chooses modify/regenerate, apply the requested change and rerun
   validation/review. Continue only when the user confirms no changes are
   needed.
7. Deliver: write UTF-8 Markdown, then report Markdown path, word count, source, confidence, and notes path
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

Supported inputs: HTTP(S) URL, X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili,
WeChat Articles, PDF, DOCX, Markdown, text file, screenshot/image, PPTX,
XLS/XLSX, CSV, JSON, XML, EPUB, ZIP, `--text`, `--stdin`, and `--html-file` for
local verification.

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
- Method: <platform-fetcher|markitdown-direct|markitdown-file|camofox-fallback|html-file|html-parser-fallback|camofox-html-parser-fallback|text|stdin>
- Confidence: <high|medium|low>
- Issues: <none-or-list>
- Validation: <pass|fail>
```
