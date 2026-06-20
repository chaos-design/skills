# Bilingual Reader Review Rules

Use this document after Markdown approval, `data.json` generation, and HTML rendering. The review
must run before delivery and whenever generated artifacts are changed.

## Review Command

Run the executable review script from the repository root:

```bash
python3 skills/bilingual-reader/scripts/review_artifacts.py \
  --markdown tests/bilingual-reader/a-practical-guide-to-building-ai-agents.md \
  --data tests/bilingual-reader/data.json \
  --html tests/bilingual-reader/compact-study/index.html
```

Multiple HTML files can be checked in one run by repeating `--html`.

```bash
python3 skills/bilingual-reader/scripts/review_artifacts.py \
  --markdown tests/bilingual-reader/a-practical-guide-to-building-ai-agents.md \
  --data tests/bilingual-reader/data.json \
  --html tests/bilingual-reader/compact-study/index.html \
  --html tests/bilingual-reader/midnight-lab/index.html \
  --output tests/bilingual-reader/review-report.json
```

The script prints a JSON report:

- `status: "pass"` means no `error` issues were found.
- `status: "fail"` means at least one `error` issue was found and delivery must stop.
- `warning` issues require review and normally should be fixed before publishing.
- `info` issues are explicit manual review reminders.

The process exits with code `0` on pass and `1` on fail.

## Markdown Review Rules

The Markdown source is the source of truth. The review script checks:

1. **Encoding**
   - File must decode as strict UTF-8.
   - UTF-8 BOM is reported as a warning.
   - Replacement characters (`�`) and invisible control characters are errors.
2. **Required metadata**
   - Exactly one main H1 is expected.
   - `> Source:` must exist and contain the original URL.
   - `> Fetched:` must use `YYYY-MM-DD HH:mm:ss`.
3. **Markdown syntax**
   - Code fences must be balanced.
   - Headings cannot be empty.
   - Markdown table separators must use at least three hyphens.
   - Source image syntax is checked, and insecure `http://` image URLs are warned.
4. **Parse contract**
   - The file must pass `markdown_to_data.parse_markdown`.
   - The parsed source must be long enough to represent a real article.

Clear errors include examples such as:

- `encoding.invalid_utf8`: file is not valid UTF-8.
- `markdown.missing_source`: source metadata is missing.
- `markdown.unclosed_fence`: code block fence is not closed.
- `markdown.parser_contract`: source parser rejected the Markdown.

## Data Review Rules

`data.json` must be generated after Markdown approval and manually reviewed before HTML rendering.
The script checks:

1. **JSON and schema**
   - Root must be a JSON object.
   - Required top-level fields must exist:
     `metadata`, `article`, `hero`, `summary`, `framework`, `sections`, `quiz`,
     `original`, `glossary`, and `footer`.
   - The data must pass `markdown_to_data.validate_learning_data`.
2. **Completeness and ranges**
   - `sections` count must be between 1 and 80.
   - `quiz` should not exceed 20 items.
   - `glossary.entries` should normally stay within 160 items.
   - `quiz[].answer` must be within the `options` array bounds.
   - `sourceUrl` must be an `http(s)` URL.
3. **Field validity**
   - No unresolved placeholders such as `__DATA_JSON__`.
   - No user-visible development markers such as `DOC001`, `TPL001`, or `DOM001`.
   - Every `zh` or `zh*` field must contain Chinese characters.
4. **Source fidelity**
   - Source-backed English fields in `sections[].rows[].en` and original bilingual rows
     must be traceable to the approved Markdown.
   - Generated explanations must not introduce URLs that do not appear in the source.
   - Numbers in summaries and explanations are flagged when not clearly present in the source.

The script can catch structural fabrication, copied placeholders, missing translations, and many
source mismatch cases. It cannot prove every factual statement automatically. Every run therefore
emits `content.manual_review_required` as an `info` item when data is reviewed. Human reviewers must
still compare translations, summaries, quiz explanations, glossary explanations, and final takeaways
against the approved Markdown.

## Content Accuracy Rules

Human review must enforce these rules:

1. Do not add article claims, examples, metrics, captions, dates, product details, or causal
   relationships that are not in the approved Markdown.
2. Translations must preserve the original meaning, modality, scope, and uncertainty.
3. Professional terms must be consistent across `sections`, `original`, `summary`, `quiz`, and
   `glossary`.
4. Summaries may compress or explain source meaning, but must not use external knowledge to fill
   gaps.
5. Quiz correct answers, wrong-answer reasons, and source evidence must match the source section.
6. Glossary terms must come from the source text and examples should use source-backed wording.

When a claim is plausible but not source-backed, delete it or rewrite it from the source.

## HTML Review Rules

The generated HTML must be static, self-contained, and functional from `file://`. The script checks:

1. **Static output contract**
   - No unresolved `__DATA_JSON__` or `__THEME_JSON__`.
   - No visible `DOCxxx`, `TPLxxx`, or `DOMxxx` markers.
   - No `fetch()`, ES module scripts, or module imports.
   - `<!DOCTYPE html>` is expected.
2. **Required page structure**
   - Required IDs: `hero`, `toc`, `originalSection`, and `glossary`.
   - Required mode buttons: `summary`, `original`, and `glossary`.
   - Footer must contain the visible `原文：` source link label.
3. **Content rendering**
   - Code blocks should preserve a language class when language is known.
   - HTML containing code blocks must keep the approved Highlight.js CSS and script so syntax highlighting remains active.
   - Tables, code, images, source links, and original sections must be rendered as visible DOM.
4. **Close-reading evidence chain**
   - Every close-reading block must pair evidence with analysis.
   - The “结论输出” module (`conclusion-output`) and each close-reading section
     (`close-core-section`) are scanned for evidence-only output.
   - `content.evidence_without_analysis` is an `error` when a block renders source evidence
     (blockquotes or Source Basis paragraphs) without a paired analysis conclusion (Final Takeaways
     list, Core Idea, or Principles). Delivery must stop until every evidence block has a
     source-grounded analysis conclusion.

## Boundary And Layout Rules

The script checks common overflow and layout risks:

1. Long text must have wrapping protection such as `overflow-wrap:anywhere`.
2. Grid layouts should use `minmax(0,1fr)` to prevent columns from being forced wider than the
   viewport.
3. Source tables must have horizontal overflow protection.
4. Tooltips must allow wrapping with `white-space: normal`.
5. Original images must use fixed `width="720"` and `height="405"` bounds and the rendered CSS must
   keep them contained.

These checks catch common content overflow, layout breakage, tooltip clipping, table overflow, and
image sizing regressions. They are static checks; visual review in a browser is still required for
final publication.

## Recommended Review Workflow

1. Generate or update Markdown.
2. Ask the user to approve Markdown.
3. Generate `data.json`.
4. Manually review and correct `data.json`.
5. Render HTML from reviewed `data.json`.
6. Run `review_artifacts.py` across Markdown, `data.json`, and all generated HTML outputs.
7. Fix every `error`; review every `warning`.
8. Open representative HTML pages in a browser and check actual layout, mode switching, quiz
   feedback, glossary tooltip behavior, source images, and boundary cases.

Do not deliver if the review script reports `status: "fail"`.
