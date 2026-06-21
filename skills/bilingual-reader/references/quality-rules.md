# Quality Rules

Load this document only after the user has approved the normalized Markdown.

## Source Fidelity

- Use the approved Markdown as the source of truth for title, source URL, publication time, body text, images, links, tables, and code blocks.
- Functional tests must use real source extraction and reviewed learning
  content. Do not mark runs that use unreviewed translators, cached fallbacks,
  or hand-crafted substitutions as successful skill tests.
- If source fetching, image access, translation, or learning-content generation
  cannot run in the current environment, stop and report the test as blocked
  or failed instead of generating substitute output.
- Do not invent source content, source images, captions, metadata, quiz evidence, or glossary terms.
- Do not invent template descriptions or descriptive page modules. Template-related copy must be derived from the approved Markdown and the selected template metadata, and unsupported details must be omitted or identified as source gaps.
- Preserve source code blocks as content. Do not translate identifiers, comments, strings, CLI commands, API URLs, config keys, placeholders, indentation, or line breaks. Keep the approved code highlighting SDK so fenced code remains syntax-highlighted while the raw `<pre><code>` content stays readable without JavaScript.
- Preserve source tables in the original view as editable HTML `<table>` elements in reading order. Translate table text in the paired Chinese table while preserving table structure and inline styles; do not flatten tables into bilingual rows.
- Preserve links, lists, bold, italic, blockquotes, and tables as styled translated HTML. Images and code blocks must remain source-only and must not be translated.
- Preserve accessible source images in the original view near their source position. Inline image bytes as data URIs when accessible. Render source images centered in a fixed 720x405 bounded image box with `object-fit: contain`. If an image is referenced but inaccessible, state the gap; do not substitute generated, stock, decorative, or placeholder images.
- For screenshots or scans, OCR only visible English text in reading order and state uncertainty for unclear regions.

## Language And Learning Content

- Use Chinese by default for explanations, study notes, labels, quiz feedback, and glossary explanations while preserving source English passages.
- Translate prose into natural Chinese with full-width punctuation.
- Every `zh` or `zh*` field under `sections` must contain Chinese translation or Chinese explanation grounded in the corresponding source content. Do not copy English prose into section `zh` fields.
- Build summary, logic framework, quiz, glossary, and final summary from article evidence.
- Every close-reading content block must pair evidence with analysis. The “结论输出” module and each
  close-reading section must present a source-grounded analysis conclusion (`summary.keyPoints` or
  `summary.cards`-derived takeaways, plus each section's Core Idea / Principles). Never emit a block
  that shows only source evidence (blockquotes or Source Basis) with no analysis. Every analysis
  point must be derived from the source through rigorous reasoning, never fabricated.
- Review `data.json` manually before HTML rendering. Check every translation sentence against the source, correct inaccurate or misleading translation, and keep domain terminology consistent.
- Verify all close-reading summaries against the approved Markdown. If a summary point, framework node, quiz explanation, glossary note, caption, or final takeaway is not directly supported by the source, delete it or rewrite it from supported source meaning.
- Do not use plausible but unsupported background knowledge to fill gaps in the article. The close-reading layer may explain the source, but it must not add new claims.
- Quiz questions must include correct answer, wrong-answer reason, and source evidence.
- The glossary should use high-value words, collocations, and domain terms from the article.
- Build the glossary by **selecting words from the approved source, then grading them by English level**. Never invent words. The required process is:
  1. Scan the approved Markdown body, headings, tables, image captions, and code-block comments/strings for candidate words and phrases. Every glossary word must appear verbatim in that source text.
  2. Discard trivial high-frequency words that a beginner already knows (typical A1/A2 basics such as `the`, `make`, `people`, `important`). Keep words that genuinely challenge a learner or carry domain meaning.
  3. Grade each remaining word by its real CEFR difficulty and tag it with the correct level. Do not guess or default a level; the tag must reflect the word's actual difficulty.
  4. Tag domain-specific or proper-noun terms (APIs, product names, acronyms, jargon) as `术语` instead of forcing a CEFR band.
- A single-word lemma is treated as source-backed when the source contains it or one of its
  natural inflected forms (plural, third-person, past tense, participle), matching the autowrap
  inflection rules. Use the dictionary lemma as the glossary `word` even when the source only writes
  an inflected form (for example keep `node` when the source says `nodes`, or `resolve` when the
  source says `resolving`). Multiword and hyphenated terms must match the source verbatim.
- Use CEFR levels `B1`, `B2`, `C1`, `C2`, and `术语`. These are the only allowed values; entries with a missing or out-of-range level are rejected by `markdown_to_data.validate_glossary_entry` and flagged by `review_artifacts.py` (`data.glossary_invalid_level`).
- Level accuracy is a hard requirement. Mislabeled levels (for example tagging a C1 word as B1, or grading a basic word as C2) must be corrected during `data.json` review.
- The `collocationExample` should reuse source-backed wording so the example stays faithful to how the word is used in the article.
- Medium articles should include 60-90 useful glossary entries when enough source terms exist. Long articles may include up to 120 high-value entries. Do not pad unrelated terms.
- Normal glossary entries need `w`, `ipa`, `pos`, `level`, `def`, `eg`, and `egzh`.
- `术语` entries may leave `ipa` empty and use `pos: "术语"`.

## Hover Vocabulary

- In authored summary rows, manual hover markup must be exactly:

```html
<span class="w" data-k="KEY">word<span class="tip"></span></span>
```

- Every `KEY` must exist in `glossary.dict`.
- Do not generate nested or partial hover markup.
- Hover text must cover complete words or phrases, including plurals, possessives, and hyphenated compounds when needed.
- Do not wrap stems inside longer words, such as `agent` inside `agents` or `use` inside `user`.
- Do not apply string-based autowrap to HTML that already contains `.w` markup.
- Autowrap must operate only on plain text nodes and skip existing `.w`, `script`, and `style` descendants.
- Tooltips must remain visible when the pointer moves from the highlighted word into the tooltip, and controls inside the tooltip must be clickable.

## Validation

Before delivery, verify that generated HTML contains:

- content rendered from the reviewed `data.json`, not a freshly regenerated unreviewed data object;
- no user-visible template-name explanation;
- no user-visible `DOCxxx`, `TPLxxx`, or `DOMxxx` markers;
- no unreplaced placeholders such as `__DATA_JSON__` or `__THEME_JSON__`;
- no external scripts or stylesheets except an approved code highlighting SDK;
- no `fetch()`;
- no module imports;
- no unresolved runtime data blobs;
- no invented replacement images;
- no unconstrained original-view image dimensions;
- no translated images or code blocks;
- code blocks keep `language-*` classes and approved Highlight.js CSS/JS for syntax highlighting;
- no flattened table translations;
- translated links, lists, bold, italic, blockquotes, and tables preserve their source structure.
