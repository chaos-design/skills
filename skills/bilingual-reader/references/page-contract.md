# Page Contract

Load this document only after the user has approved the normalized Markdown.

## Deliverables

Before page generation, the output directory must already contain:

1. `<slug>.md` - the approved normalized Markdown.
2. `data.json` - generated from the approved Markdown, manually reviewed, and corrected.

Generate by default:

1. `index.html` - a self-contained, human-editable bilingual reading page.

Always generate `data.json` before HTML rendering. `index.html` must not depend on `data.json` at runtime, but it must be rendered from the reviewed `data.json` so translation and summary corrections are preserved.
If the delivery target is stdout or chat instead of a file, emit the same complete standalone HTML document only: no Markdown code fences, no prose explanation, no status lines, and no surrounding formatting.

## Static HTML Requirements

- Inline all visible article and learning content in normal HTML elements.
- Do not hide source content in `window.BILINGUAL_READER_DATA`, `window.DATA`, JSON blobs, `fetch()`, module imports, generated render functions, or external files.
- Inline CSS in `<style>`.
- Inline only the JavaScript needed for interactions: view switching, DOM-derived tooltip placement, pronunciation, quiz feedback, theme switching, anchors, and reading progress.
- Keep the approved third-party code highlighting SDK for syntax-highlighted code blocks, while ensuring code content remains visible as normal `<pre><code>` HTML when the SDK is unavailable.
- The page must open directly from `file://`.
- The page must include a complete document shell: `<!DOCTYPE html>`, `<html>`, `<head>`, and `<body>`.
- Format the generated HTML with 2-space indentation for HTML/CSS/JavaScript while preserving source code block indentation exactly.

## Required Page Content

- Hero with title, source metadata, and bilingual hook only. Do not include stats, metrics, counters, dashboard numbers, or `stats` / `stat` class blocks in the hero.
- Summary view with a primary guide card, secondary summary cards, source-grounded logic framework, comprehension quiz, bilingual sections, one final summary module, and section cards when the source supports them.
- Original view with source metadata, content tags, section anchors, consecutive original paragraphs merged into larger translation units, source images, source code blocks, and source tables in reading order.
- Glossary view grouped by `B1`, `B2`, `C1`, `C2`, and `术语`.
- Footer source link exactly as `原文：<a href="SOURCE_URL" target="_blank" rel="noopener">《SOURCE_TITLE》</a>`.
- Anchor navigation through `nav#toc`, with click-to-scroll and active-state tracking.

## Source-Grounded Template Content

- Template descriptions, selection notes, guide copy, summary cards, captions, and visual labels must be organized from the approved Markdown and the selected template metadata only.
- Do not invent source facts, section titles, examples, metrics, captions, image meanings, or article claims to make a template feel fuller.
- If the source does not support a descriptive module, omit the module or state the source-backed gap plainly instead of filling it with generic copy.

## Reviewed Data Contract

- Generate `data.json` first and stop before rendering HTML.
- Review every `zh` and `zh*` field sentence by sentence against the source-backed English text.
- Review close-reading summaries in `summary`, `framework`, `quiz`, summary sections, captions, and glossary explanations against the approved Markdown.
- Correct inaccurate translation, misleading terminology, unsupported interpretation, and missing source nuance directly in `data.json`.
- Render HTML from the corrected `data.json`; do not regenerate data after manual corrections unless the review is repeated.

## Original Image Presentation

- Original-view images must be inserted only from source images present in the approved Markdown or extracted document input.
- Place images in reading order near the source position they belong to.
- Render original images centered in a bounded media block, with fixed `width="720"` and `height="405"` attributes or equivalent CSS, and `object-fit: contain`.
- Do not use unconstrained image dimensions, full natural-size rendering, decorative replacement images, stock images, generated images, or placeholder images.

## Header Contract

- Left side: one source-document title link opening the original URL with `target="_blank"` and `rel="noopener"`.
- Right side: functional controls.
- `精读`, `原文`, and `词汇` are one mutually exclusive segmented control.
- `主题` is a separate control group. It only changes theme variables and must not change the active reading view.
- Do not render `词汇` as a separate toggle outside the segmented control.

## Template Loading

After Markdown approval and parser conversion:

1. Generate and review `data.json`.
2. Read `assets/templates/templates.json`.
3. If generating one page, inspect only the selected template under `assets/templates/<name>/template.html`.
4. If validating all indexed templates, use `scripts/static_reader.py --data-file <reviewed-data.json>` and render each template as `tests/bilingual-reader/<template>/index.html`, plus `tests/bilingual-reader/index.html`.
5. Do not describe the selected template as a `default` choice.
6. Do not replace all templates with one generic stylesheet; reuse the selected template's CSS direction.
7. When a complete HTML document must be written to stdout, select exactly one template and run `scripts/static_reader.py --data-file <reviewed-data.json> --output-dir <output-dir> --template <template-name> --stdout-html`. This mode must not print progress, summaries, Markdown, or code fences.
