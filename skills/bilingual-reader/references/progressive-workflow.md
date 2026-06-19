# Progressive Workflow

This document is the mandatory execution flow for `bilingual-reader`. Load it after the root `SKILL.md` when starting a task, before reading any generation assets.

## Hard Gates

1. Normalize first. For URLs and other raw sources, use `scripts/normalize_source.py` so the review Markdown is created in the user-specified bilingual-reader output directory. Dependency skills may extract content, but they must not choose the final output directory.
2. Stop immediately after the Markdown file exists.
3. Call `AskUserQuestion` explicitly. A normal chat message is not enough.
4. The question must include the generated Markdown file path and offer only these meanings:
   - continue with this Markdown;
   - revise or regenerate Markdown first.
5. Until the user explicitly confirms the Markdown is acceptable, do not:
   - parse the Markdown into article data;
   - translate the article;
   - load `markdown_to_data.py`;
   - load `static_reader.py`;
   - read `assets/templates/templates.json`;
   - read any `assets/templates/<name>/template.html`;
   - generate HTML, `data.json`, screenshots, or previews.
6. If the user says the Markdown has a problem, update or regenerate only the Markdown file, then ask with `AskUserQuestion` again. Repeat this loop until the user confirms the Markdown is acceptable.
7. After Markdown approval, generate `data.json` before rendering HTML.
8. Stop for `data.json` review. Check translations sentence by sentence, correct inaccurate or misleading Chinese, and verify every close-reading summary against the approved Markdown.
9. Render HTML only from the reviewed `data.json`.

## Progressive Disclosure Loading

Load only the files needed for the current stage.

| Stage | Allowed files | Forbidden until later |
| --- | --- | --- |
| Start | `SKILL.md`, then this file | Prompt, renderer, templates, data schema |
| Normalize source | `scripts/normalize_source.py`, `web-markdown/SKILL.md`, `web-markdown/references/harness.md`, and its extraction script only if needed | `bilingual-reader` parser, renderer, templates |
| Markdown review | Generated `.md` file only | Parser, renderer, templates, page contracts |
| Markdown revision | The `.md` file and extraction files needed to fix it | HTML generation assets |
| Approved Markdown | `scripts/markdown_to_data.py`, `references/data-schema.md`, `references/page-contract.md`, `references/quality-rules.md` | Template HTML files until template selection |
| Data review | Generated `data.json` and approved Markdown | HTML generation until data review is complete |
| Template selection | `assets/templates/templates.json` | Individual template files not selected |
| Single-page generation | Reviewed `data.json`, only the selected `assets/templates/<name>/template.html` plus required runtime assets | Other templates |
| All-template previews | `scripts/static_reader.py`, `assets/templates/templates.json`, and each indexed template as it is rendered | Unrelated skills and assets |

## Review Question Shape

Use one `AskUserQuestion` call like this after Markdown generation:

- Question: `已生成 Markdown：<absolute-path>。请确认这个 Markdown 的正文、图片、表格、代码块和阅读顺序是否可以作为双语精读页面的来源？`
- Option 1: `继续生成` - The Markdown is acceptable; proceed to parsing and page generation.
- Option 2: `需要修正` - The Markdown has issues; collect the user's requested changes and revise or regenerate the Markdown first.

If the user chooses `需要修正` or replies with concrete problems, do not continue to page generation. Apply the requested Markdown fix, then ask the same confirmation question again.

## Data Review Shape

After Markdown approval, generate `data.json` with:

```bash
python3 skills/bilingual-reader/scripts/static_reader.py <markdown-file> --output-dir <output-dir> --data-only
```

Then manually review `<output-dir>/data.json` before rendering:

- Check every translation field (`zh` and `zh*`) against its English source sentence.
- Correct terminology, tone, omissions, mistranslations, and wording that could mislead readers.
- Check `summary`, `framework`, `quiz`, and summary-type sections against the approved Markdown.
- Delete or rewrite any claim, inference, quiz explanation, glossary note, or summary that is not supported by the source.

After the corrected data is saved, render from that reviewed artifact:

```bash
python3 skills/bilingual-reader/scripts/static_reader.py --data-file <output-dir>/data.json --output-dir <output-dir>
```
