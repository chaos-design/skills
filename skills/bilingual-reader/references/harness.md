# Bilingual Reader Harness

Turn English source material from a URL, image, document file, local file path, attachment, or pasted text into a polished, offline English-Chinese close-reading page.

This prompt follows the same staged workflow as `SKILL.md`: normalize source material to Markdown first, ask the user to approve that Markdown with `AskUserQuestion`, and only then generate bilingual HTML.

## Progressive Disclosure

Do not load every file in this skill at the start of a task.

1. First load `references/progressive-workflow.md`.
2. During source normalization, use `scripts/normalize_source.py` and load only the `web-markdown` files needed for extraction.
3. During Markdown review, load only the generated `.md` file.
4. After Markdown approval, load `scripts/markdown_to_data.py`, `references/page-contract.md`, and `references/quality-rules.md`.
5. Load `assets/templates/templates.json` only when selecting or validating templates.
6. Load individual template files only after template selection, or one by one during all-template preview rendering.
7. Load `references/data-schema.md` only when the user explicitly asks for a separate `data.json`.

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

1. `index.html` - self-contained, human-editable bilingual reading page.

Only generate `data.json` when the user explicitly requests it.

## Approved-Markdown Workflow

Once the Markdown is approved:

1. Parse it with `scripts/markdown_to_data.py` when available.
2. Use `references/page-contract.md` for output structure, static HTML rules, header contract, and template loading rules.
3. Use `references/quality-rules.md` for source fidelity, translation, glossary, hover vocabulary, and validation requirements.
4. Generate visible article and learning content directly into the final HTML body.
5. Validate that the page opens from `file://` and contains no unresolved placeholders, runtime data blobs, forbidden markers, invented replacement images, translated code blocks, or translated table rows.
