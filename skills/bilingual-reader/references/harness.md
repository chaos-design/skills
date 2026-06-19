# Bilingual Reader Harness

Turn English source material from a URL, image, document file, local file path, attachment, or pasted text into a polished, offline English-Chinese close-reading page.

This prompt follows the same staged workflow as `SKILL.md`: normalize source material to Markdown first, ask the user to approve that Markdown with `AskUserQuestion`, generate and review `data.json`, and only then generate bilingual HTML.

## Progressive Disclosure

Do not load every file in this skill at the start of a task.

1. First load `references/progressive-workflow.md`.
2. During source normalization, use `scripts/normalize_source.py` and load only the `web-markdown` files needed for extraction.
3. During Markdown review, load only the generated `.md` file.
4. After Markdown approval, load `scripts/markdown_to_data.py`, `references/page-contract.md`, and `references/quality-rules.md`.
5. Load `assets/templates/templates.json` only when selecting or validating templates.
6. Load individual template files only after template selection, or one by one during all-template preview rendering.
7. Load `references/data-schema.md` after Markdown approval, before generating and reviewing `data.json`.

## Mandatory Markdown Review Gate

Before writing a generated Markdown file, inspect the target output directory for an existing related `.md` file.

If one exists, stop immediately and call `AskUserQuestion` to ask whether to:

1. Overwrite the existing Markdown.
2. Create a new Markdown filename.
3. Cancel Markdown generation.

After generating `<slug>.md`, stop immediately and call `AskUserQuestion`.

The question must include the absolute Markdown path and ask whether the Markdown's body text, images, tables, code blocks, and reading order are acceptable as the source for the bilingual page.

Offer only choices that mean:

1. Continue with this Markdown.
2. Revise or regenerate Markdown first.

Before the user explicitly approves the Markdown, do not:

- parse Markdown into article data;
- translate the article;
- select a visual template;
- read template files;
- generate `index.html`;
- generate previews;
- generate `data.json`.

If the user reports Markdown problems, revise or regenerate the Markdown in the same output directory, then ask for confirmation again with `AskUserQuestion`. Repeat until the user confirms the Markdown is acceptable.

For URL input, run the bilingual-reader normalization entrypoint instead of invoking the dependency skill directly:

```bash
python3 skills/bilingual-reader/scripts/normalize_source.py "<URL>" --output-dir tests/bilingual-reader
```

This keeps the review Markdown in the bilingual-reader target directory. The `web-markdown` skill remains a dependency for extraction only and must not decide the final output path for bilingual-reader tasks.

## Deliverables

Before page generation:

1. `<slug>.md` - normalized Markdown generated from the source or supplied by the user.

After Markdown approval:

1. `data.json` - generated article data, reviewed and corrected before HTML rendering.
2. `index.html` - self-contained, human-editable bilingual reading page rendered from reviewed data.

Do not render the final HTML until `data.json` has been reviewed.

## Mandatory Data Review Gate

After generating `data.json`, stop and review the file before rendering HTML.

The review must cover:

1. Every `zh` or `zh*` translation field in `sections`, `original.groups`, `summary`, `framework`, `quiz`, and `glossary`.
2. Translation accuracy, terminology consistency, professional phrasing, and whether the Chinese could mislead readers about the source meaning.
3. All close-reading summaries, including `summary.lead`, `summary.cards`, `summary.keyPoints`, `framework.nodes[].summary`, quiz explanations, and final summary sections.
4. Source support: any summary, interpretation, quiz option, glossary explanation, or caption that cannot be traced to the approved Markdown must be deleted or rewritten from source-backed content.

After correction, render HTML from the reviewed `data.json` rather than regenerating unreviewed data.

Supported CLI pattern:

```bash
python3 skills/bilingual-reader/scripts/static_reader.py tests/bilingual-reader/<slug>.md --output-dir tests/bilingual-reader --data-only
# review and edit tests/bilingual-reader/data.json
python3 skills/bilingual-reader/scripts/static_reader.py --data-file tests/bilingual-reader/data.json --output-dir tests/bilingual-reader
```

## Approved-Markdown Workflow

Once the Markdown is approved:

1. Parse it with `scripts/markdown_to_data.py` when available.
2. Let the parser reject boundary failures before data generation: empty or oversized Markdown, unsupported control characters, missing or malformed metadata, unclosed code fences, malformed tables, unsupported image sources, and incomplete article text.
3. Generate `data.json` and complete the mandatory data review gate.
4. Validate reviewed data before rendering so missing top-level fields, duplicate quiz options, invalid answer indexes, untranslated Chinese fields, invalid glossary regex, or missing glossary dictionary keys stop with clear errors.
5. Use `references/page-contract.md` for output structure, static HTML rules, header contract, and template loading rules.
6. Use `references/quality-rules.md` for source fidelity, translation, glossary, hover vocabulary, and validation requirements.
7. Generate visible article and learning content directly into the final HTML body from the reviewed data.
8. Validate that the page opens from `file://` and contains no unresolved placeholders, runtime data blobs, forbidden markers, duplicate IDs, invented replacement images, translated code blocks, translated table rows, or forbidden external runtime resources.
