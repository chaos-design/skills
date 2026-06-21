---
name: "bilingual-reader"
description: "Generates offline English-Chinese close-reading pages from Markdown normalized through web-markdown. Invoke for URLs, images, documents, files, or pasted text needing bilingual study."
---

# Bilingual Reader

Use this skill when the user provides English source material as a URL, image, document file, local file path, attachment, or pasted text and wants a polished Chinese-English close-reading page.

This skill must normalize raw source material to Markdown first, stop for explicit user review, and continue only after the user confirms that the Markdown is acceptable.

## Mandatory First Read

After this file, read only:

1. `references/progressive-workflow.md`

Do not read parser files, renderer files, templates, runtime assets, `references/harness.md`, or page-quality references until the workflow stage allows them.
## Workflow Overview

Use this checkpointed workflow when the skill output is a publishable article-style artifact. Keep checkpoints explicit and stop at each checkpoint until the user confirms the listed decisions.

```
Phase 0  Intake
         Decide whether this skill applies and identify the initial article type.
  🔽
Phase 1  Source -> Markdown
         Convert URL/PDF/DOCX/MD/text into source.md + extraction-notes.md.
         The main agent runs a 5-item inline checklist; only complex or low-confidence sources escalate to a SubAgent.
  🔽
Phase 2  Editorial Planning
         Create one plan.md with four sections: Brief / Outline / Theme / Assets.
         The main agent self-checks inline; no SubAgent and no review file.
  🔽
Phase 3  Plan Checkpoint
         Checkpoint 1 must stop. Confirm five items one by one:
         article type with standard retention ratio / theme / layout / image mode / cover.
  🔽
Phase 4  First Spread
         Build the hero, first section, and one representative visual block. Create the scaffold here.
         First Spread Reviewer SubAgent writes review/first-spread-review.md.
         Checkpoint 2 must stop. Confirm two items one by one:
         acceptance result / development mode A or B.
  🔽
Phase 5  Full Article Build
         Generate the complete web article. Default to one agent; isolate by section only for very long articles.
         Section Reviewer SubAgent returns pass/fail in the message and does not write a review file.
  🔽
Phase 6  Final Review
         Run Editorial / Visual / Technical final review and write review/final-review.md.
  🔽
Phase 7  Repair
         Apply minimal-slice repairs. Write repair-log.md only when repairs are made.
  🔽
Phase 8  Delivery
         Checkpoint 3 must stop. Confirm the delivery decision one by one.
         Deliver article.html plus a short editorial note.
```


## Hard Gates

- Output directory resolution is mandatory before any file generation or filesystem inspection. If the user explicitly specifies an output directory, use that directory for the Markdown, `data.json`, and HTML; do not inspect the broader filesystem to choose or discover another location.
- Markdown review is mandatory. After generating `<slug>.md`, call `AskUserQuestion` and stop.
- Before writing a generated Markdown file, inspect the target directory for an existing related `.md` file. If one exists, call `AskUserQuestion` to ask whether to overwrite it, create a new filename, or cancel.
- A normal chat message is not a substitute for `AskUserQuestion`.
- If the user says the Markdown has issues, fix or regenerate only the Markdown, then ask again with `AskUserQuestion`.
- Do not parse, translate, select templates, generate `data.json`, or generate HTML until the user explicitly approves the Markdown.
- `data.json` review is mandatory after Markdown approval. Generate `data.json` first, review and correct it before rendering HTML, and use the reviewed data for final page generation.
- Use progressive disclosure. Load only the files required for the current stage.

## Dependency

`web-markdown` must be installed and available alongside this skill for URL normalization.

If it is missing, pause and ask the user whether to install it. Show:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
```

Continue only after the dependency is available or the user provides an already-normalized Markdown file.

## Resource Loading Map

Load resources in this order only:

1. Start: `SKILL.md`, then `references/progressive-workflow.md`.
2. Normalize source: `scripts/normalize_source.py`, plus `../web-markdown/SKILL.md`, `../web-markdown/references/harness.md`, and `../web-markdown/scripts/web_markdown.py` only if needed.
3. Markdown review and revision loop: generated `.md` file only, plus source-normalization files needed to fix it.
4. Approved Markdown: `scripts/markdown_to_data.py`, `references/data-schema.md`, `references/page-contract.md`, and `references/quality-rules.md`.
5. Data artifact: generate `data.json`, then review and correct it before HTML rendering.
6. Template selection: `assets/templates/templates.json`.
7. Single-template page: only the selected `assets/templates/<name>/template.html` plus required runtime assets.
8. All-template previews: `scripts/static_reader.py`, `assets/templates/templates.json`, and each indexed template as it is rendered.
9. Final artifact review: `references/review-rules.md` and `scripts/review_artifacts.py`.

## Workflow

1. Resolve the bilingual-reader output directory first. If the user specified a directory, use it directly and do not inspect the broader filesystem.
2. Inspect only the resolved target output directory for an existing related Markdown file.
3. If a related Markdown file exists, call `AskUserQuestion` before overwriting or choosing a replacement filename.
4. Convert raw input to normalized Markdown in the resolved output directory using `scripts/normalize_source.py`; do not let dependency skills choose the output directory.
5. Immediately call `AskUserQuestion` with the Markdown path and ask whether the Markdown is acceptable.
6. If the user requests changes, revise or regenerate only the Markdown in the same output directory and repeat step 5.
7. After explicit approval, parse the Markdown into article data.
8. Generate Chinese translation, learning structure, glossary, quiz, and `data.json` in the same output directory.
9. Review `data.json` manually before HTML rendering: check every translation sentence, correct inaccurate or misleading wording, verify all close-reading summaries against the approved Markdown, and remove or rewrite unsupported claims.
10. Render the final static HTML from the reviewed `data.json`.
11. Validate the output against `references/page-contract.md`, `references/quality-rules.md`, and `references/review-rules.md`.
12. Run `scripts/review_artifacts.py` on the approved Markdown, reviewed `data.json`, and generated HTML before delivery.

## Output

- Always produce the review Markdown file before page generation.
- Produce `data.json` after Markdown approval and before HTML rendering.
- Produce `index.html` only after `data.json` has passed manual translation and summary review.
- Keep the approved Markdown, reviewed `data.json`, and generated HTML in the same resolved output directory.
- The final HTML artifact must be a complete standalone HTML document with `<!DOCTYPE html>`, `<html>`, `<head>`, and `<body>`, and it must open directly from `file://` without runtime data files.
- If the user asks to output the HTML content in chat or stdout, output only the raw HTML document content. Do not wrap it in Markdown fences, headings, explanations, logs, status lines, or any non-HTML text.
- For script-based pure output, use `scripts/static_reader.py --data-file <output-dir>/data.json --output-dir <output-dir> --template <template-name> --stdout-html`; this mode writes only the selected complete HTML document to stdout.
