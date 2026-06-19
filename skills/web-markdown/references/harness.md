# Web Markdown Harness

This is the canonical contract for converting URLs, PDFs, DOCX files, Markdown
files, plain text, screenshots/images, and pasted notes into faithful Markdown
archives. It borrows the small harness pattern from article-generation skills,
but the deliverable here is Markdown only.

## 1. Phase Workflow

### 1.1 Phase 0 - Intake

Accept inputs that MarkItDown supports, after sanitising them:

- Absolute `http://` and `https://` URLs.
- Local files supported by MarkItDown, including PDF, DOCX, PPTX, XLS/XLSX,
  CSV, JSON, XML, EPUB, ZIP, Markdown, plain text, and screenshots/images.
- Pasted notes through `--text` or `--stdin`.

Reject:

- Shell commands.
- JavaScript URLs.
- Data URLs.
- Directories.
- Private credentials embedded in URLs.
- Login-only, paywalled, private, or access-controlled content unless the user
  provides an accessible source.

Classify the resource type before loading conversion dependencies or checking
file extensions. This preflight decision owns the rest of the workflow:

| Resource type | Route |
| --- | --- |
| X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, or WeChat Article URL | `x-tweet-fetcher` bridge |
| Generic HTTP(S) URL | MarkItDown URL conversion, then Camofox rendered HTML fallback only if needed |
| Existing local file | MarkItDown file conversion |
| `--html-file` | MarkItDown HTML conversion, then Camofox/rendered HTML parser fallback if needed |
| `--text` or `--stdin` | MarkItDown text conversion |

Capture the intended output mode:

- One-off mode: write `web/<slug>.md` for generic sources, or
  `<platform>/<slug>.md` for platform fetcher sources, unless the user provides
  `--output`.
- Workspace mode: write durable extraction artifacts under:

```text
<workspace>/
  source/   original.url|original.*  original.md  original.<lang>.md  extraction-notes.md
  review/   source-review.md         # only for complex or low-confidence input
```

`source/original.md` is always the faithful Markdown in the original source
language. If the user explicitly requests a translated source copy, create
`source/original.<lang>.md` where `<lang>` is the requested target language
label, for example `original.zh-CN.md`. Record both the original language and
requested translation language in `extraction-notes.md`.

### 1.2 Phase 1 - Source Capture

For URLs, record the exact source URL. For local files, keep the path and avoid
modifying the source file. For pasted text, treat the source label as
`pasted-notes`.

Classify confidence before conversion:

| Confidence | Source Traits | Default Review |
| --- | --- | --- |
| high | Simple document, normal article URL, clear body, direct conversion succeeds | inline checklist |
| medium | JavaScript rendering needed, large tables/code, mixed media, OCR/image input | inline checklist + notes |
| low | partial rendering, blocked resources, obvious missing sections, conversion errors repaired manually | reviewer/subagent when available |

Only complex or low-confidence sources should create `review/source-review.md`.

### 1.3 Phase 2 - Convert With The Selected Route

MarkItDown must be installed with document/image extras:

```bash
pip install 'markitdown[all]'
```

Use the script for every supported input type:

```bash
python3 skills/web-markdown/scripts/web_markdown.py "<URL-or-file>"
python3 skills/web-markdown/scripts/web_markdown.py --text "Pasted notes..."
pbpaste | python3 skills/web-markdown/scripts/web_markdown.py --stdin
```

For X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, and WeChat Article URLs,
the script bridges to local `x-tweet-fetcher` scripts and normalizes the fetched
payload into Markdown. For generic URLs, PDF, DOCX, Markdown, plain text,
screenshot/image, HTML files, and pasted-note inputs, it uses MarkItDown first
and wraps the result in the standard source metadata and output contract.

Use optional notes when a workspace or confidence record is needed:

```bash
python3 skills/web-markdown/scripts/web_markdown.py "<URL-or-file>" \
  --workspace . \
  --notes-output source/extraction-notes.md
```

### 1.4 Phase 2b - Render URL Fallback With Camofox

Camofox must be available on `localhost:9377` only when direct MarkItDown URL
conversion fails and the URL needs rendered HTML fallback.

```bash
curl http://localhost:9377/health
```

For URL and HTML fallback, the script opens a Camofox tab, waits for JavaScript
rendering, retrieves the rendered page content, closes the tab, and sends the
rendered HTML through MarkItDown. If rendered HTML still cannot be converted by
MarkItDown, use the built-in HTML parser fallback and record both issues in the
notes. If the tab cannot be opened or no rendered content can be read, surface
the exact error together with the original MarkItDown conversion error.

### 1.5 Phase 2c - Extract The Main Content Area

Prefer the most specific readable content container:

1. `<article>`
2. `<main>`
3. `[role="main"]`
4. Content-like containers whose id/class includes `content`, `article`,
   `post`, `entry`, `doc`, `markdown`, or `prose`
5. `<body>` as a fallback

Remove obvious non-content regions before conversion: `script`, `style`,
`template`, `noscript`, `nav`, `header`, `footer`, `aside`, `form`, cookie
banners, ads, modals, and social sharing widgets.

### 1.6 Phase 2d - Convert To Markdown

Preserve all meaningful source content:

- Headings map to `#` through `######`.
- Paragraphs remain paragraphs.
- Ordered and unordered lists remain lists.
- Blockquotes remain blockquotes.
- Tables remain Markdown tables when possible. Emit the header, separator, and
  every body row as one contiguous block with no blank lines between rows.
- Inline code remains backticked inline code.
- Multi-line code and `<pre>` blocks become fenced code blocks. Strip rendered
  line-number gutters from the code, and add a language hint on the opening
  fence when it can be inferred from `language-*` / `highlight-source-*` classes
  or a `data-language` attribute.
- Images become `![alt](absolute-url)`.
- Links become `[text](absolute-url)`.
- Line breaks that are semantically visible remain line breaks.

Do not summarise, translate, paraphrase, reorder, or add editorial notes.

### 1.7 Phase 3 - Extraction Notes

Write extraction notes when:

- The user asks for a staged/checkpointed archive.
- The source is medium or low confidence.
- Camofox fallback was required.
- Manual repair was required.
- Multiple inputs are being processed and later traceability matters.

`extraction-notes.md` must be concise and factual:

```markdown
# Extraction Notes

- Source: <URL-or-file>
- Output: <path>
- Source Language: <detected-or-user-provided-source-language>
- Target Language: <requested-translation-language-or-none>
- Translated Source: <path-to-original.lang.md-or-none>
- Method: <platform-fetcher|markitdown-direct|markitdown-file|camofox-fallback|html-file|html-parser-fallback|camofox-html-parser-fallback|text|stdin>
- Confidence: <high|medium|low>
- Issues: <none-or-list>
- Validation: <pass|fail>
```

Do not use extraction notes for summaries, commentary, or invented source
metadata.

### 1.8 Phase 4 - Validate

Default output path:

```text
web/<slug>.md
```

Slug rules:

1. Prefer the first `<h1>`, then `<title>`, then the source host.
2. Lowercase the title.
3. Convert whitespace to hyphens.
4. Strip characters outside `[a-z0-9-]`.
5. Collapse duplicate hyphens.
6. Cap at 80 characters.
7. Append `.md`.

If the target file already exists, append the smallest numeric suffix that
avoids overwriting, for example `article-2.md`.

Before writing the Markdown file, format it for readability. Treat indentation
as tab-based structure with an indent width of 2 spaces for nested Markdown
structures such as lists, blockquotes, and tables, while preserving source
fenced-code indentation exactly as extracted.

Run the checklist in section 2 before declaring success.

For low-confidence sources, compare the Markdown against the original source or
rendered view when available. If a reviewer/subagent is available, write
`review/source-review.md`; otherwise note the fallback in `extraction-notes.md`.

After validation and any required review pass, and before writing the final
Markdown output, call `AskUserQuestion` to ask whether the user wants to modify
or regenerate the Markdown. If the user requests changes, apply them and rerun
validation/review. Write output only after the user confirms no changes are
needed.

### 1.9 Phase 5 - Repair

Repair only the smallest affected slice:

- Missing title: use first Markdown `#`, then source title, then host/file stem.
- Empty body: rerun conversion or fallback; do not ship.
- Unbalanced code fences: repair or stop.
- Rendered line-number gutters in code: strip gutters while preserving code.
- Tables split by blank lines: merge rows into one contiguous table block.
- Broken source order: rerun extraction or stop if it cannot be fixed.

After repair, rerun validation.

### 1.10 Phase 6 - Confirm And Report

After user confirmation and a successful write, report:

```text
Saved web/<slug>.md - <word_count> words - <source> - confidence <level>
```

When notes are written, also report the notes path.

If the command fails, report the failing phase and exact error. Do not write a
partial Markdown file.

## 2. Validation Checklist

Before declaring success:

- [ ] Source URL metadata is present.
- [ ] Markdown has a non-empty title.
- [ ] Body content is non-empty.
- [ ] No placeholder text such as `TODO`, `FIXME`, or `<Title>` remains.
- [ ] Every fenced code block has both opening and closing fences.
- [ ] Every image from the extracted content appears as a Markdown image.
- [ ] Every link from the extracted content appears as a Markdown link or plain
      URL when the source text itself is the URL.
- [ ] `source/original.md` remains in the original source language.
- [ ] If `source/original.<lang>.md` exists, it preserves the same facts,
      structure, links, images, code, numbers, and citations as `original.md`.
- [ ] Extraction notes, when present, accurately state source, output, method,
      source language, target language, confidence, issues, and validation
      result.

## 3. Output Contract

The Markdown starts with source metadata followed by extracted content:

```markdown
# <Detected page title>

> Source: <URL-or-file>
> Fetched: <YYYY-MM-DD HH:mm:ss>

<Complete rendered main content converted to Markdown>
```

When the page has no reliable title, use the source host. For local files, use
the file stem. For pasted text, use `Pasted Notes`.

## 4. Error Handling

| Condition | Action |
| --- | --- |
| Source is neither HTTP(S), an existing local file, `--text`, nor `--stdin` | Reject and stop. |
| URL is X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, or WeChat Articles | Use the `x-tweet-fetcher` bridge inside `web-markdown`; if the bridge dependency is unavailable, surface the exact missing dependency path or fetcher error. |
| Generic URL direct conversion fails | Try Camofox rendered HTML fallback. |
| Rendered HTML MarkItDown conversion fails | Use the built-in HTML parser fallback and record the MarkItDown error. |
| MarkItDown is not installed | Stop and show `pip install 'markitdown[all]'`. |
| MarkItDown cannot convert a local file, screenshot, or pasted text | Surface the MarkItDown error and stop. |
| Camofox is not reachable during URL fallback | Ask the user to start Camofox and report the original MarkItDown error too. |
| Camofox cannot open the tab | Surface the Camofox error and stop. |
| Rendered content cannot be read | Surface the content retrieval error and stop. |
| Extracted content is empty | Stop and report that no readable content area was found. |
| Output file exists | Use a numeric suffix; never overwrite silently. |
| Markdown validation fails | Fix the conversion or stop with the validation error. |
| Notes file exists | Use a numeric suffix; never overwrite silently. |

## 5. Review Contract

`review/source-review.md` is required for low-confidence extraction, user-
requested review, or any translated `source/original.<lang>.md`. The review must
compare the generated Markdown against the real source material:

- For URLs, compare against the rendered page or source payload, not only the
  generated Markdown.
- For local files, compare against the original file content as read by the
  converter.
- For translations, compare `original.<lang>.md` against `original.md` and flag
  any changed facts, missing sections, altered numbers, broken links, dropped
  images, changed code, or unsupported added claims.
- Mark the review `pass` only when the generated content is faithful to the
  real source and any requested translation preserves meaning.
