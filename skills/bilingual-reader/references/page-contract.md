# Page Contract

Load this document only after the user has approved the normalized Markdown.

## Deliverables

Before page generation, the output directory must already contain:

1. `<slug>.md` - the approved normalized Markdown.

Generate by default:

1. `index.html` - a self-contained, human-editable bilingual reading page.

Only generate `data.json` when the user explicitly asks for a separate data artifact. `index.html` must not depend on `data.json`.

## Static HTML Requirements

- Inline all visible article and learning content in normal HTML elements.
- Do not hide source content in `window.BILINGUAL_READER_DATA`, `window.DATA`, JSON blobs, `fetch()`, module imports, generated render functions, or external files.
- Inline CSS in `<style>`.
- Inline only the JavaScript needed for interactions: view switching, DOM-derived tooltip placement, pronunciation, quiz feedback, theme switching, anchors, and reading progress.
- A third-party code highlighting SDK may enhance code blocks, but code content must remain visible as normal `<pre><code>` HTML when the SDK is unavailable.
- The page must open directly from `file://`.
- Format the generated HTML with 2-space indentation for HTML/CSS/JavaScript while preserving source code block indentation exactly.

## Required Page Content

- Hero with title, source metadata, and bilingual hook only. Do not include stats, metrics, counters, dashboard numbers, or `stats` / `stat` class blocks in the hero.
- Summary view with a primary guide card, secondary summary cards, source-grounded logic framework, comprehension quiz, bilingual sections, one final summary module, and section cards when the source supports them.
- Original view with source metadata, content tags, section anchors, original paragraphs, source images, source code blocks, and source tables in reading order.
- Glossary view grouped by `B1`, `B2`, `C1`, `C2`, and `术语`.
- Footer source link exactly as `原文：<a href="SOURCE_URL" target="_blank" rel="noopener">《SOURCE_TITLE》</a>`.
- Anchor navigation through `nav#toc`, with click-to-scroll and active-state tracking.

## Header Contract

- Left side: one source-document title link opening the original URL with `target="_blank"` and `rel="noopener"`.
- Right side: functional controls.
- `精读`, `原文`, and `词汇` are one mutually exclusive segmented control.
- `主题` is a separate control group. It only changes theme variables and must not change the active reading view.
- Do not render `词汇` as a separate toggle outside the segmented control.

## Template Loading

After Markdown approval and parser conversion:

1. Read `assets/templates/templates.json`.
2. If generating one page, inspect only the selected template under `assets/templates/<name>/template.html`.
3. If validating all indexed templates, use `scripts/static_reader.py` and render each template as `tests/bilingual-reader/<template>/index.html`, plus `tests/bilingual-reader/index.html`.
4. Do not describe the selected template as a `default` choice.
5. Do not replace all templates with one generic stylesheet; reuse the selected template's CSS direction.

