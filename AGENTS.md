# AGENTS.md

This file defines repository-specific guidance for agents working in this
project.

## Project Layout

```text
.
|-- skills/
|   |-- bilingual-reader/
|   |-- content-slides/
|   |-- frontend-slides/
|   |-- geo-flow-map/
|   |-- url-content-fetcher/
|   |-- web-markdown/
|   `-- x-tweet-fetcher/
|-- screenshots/
|   |-- bilingual-reader/
|   |-- content-slides/
|   `-- frontend-slides/
`-- tests/
    |-- bilingual-reader/
    |-- content-slides/
    |-- frontend-slides/
    |-- web-markdown/
    `-- index.html
```

- `skills/<skill-name>/` contains each distributable skill and its public
  documentation.
- `screenshots/<skill-name>/` contains documentation screenshots for the
  matching skill.
- `tests/` contains generated fixtures, preview pages, and test files used to
  validate skills in this repository.

Keep edits scoped to the skill, screenshot, or test area required by the task.
Do not reorganize existing directories unless the user explicitly asks for it.

## Skill Testing Rules

When testing a skill in this project:

1. Create or reuse a folder named after the skill under `tests/`.
   - Example: testing `web-markdown` writes outputs under
     `tests/web-markdown/`.
   - Example: testing `bilingual-reader` writes outputs under
     `tests/bilingual-reader/`.
2. Put all generated test outputs for that skill inside its matching
   `tests/<skill-name>/` folder.
3. Preserve existing files and folders for other skills. Do not delete, rename,
   or move unrelated test outputs.
4. If the generated result is HTML and it needs to be available from the shared
   preview page, add a link or preview entry to `tests/index.html`.
5. Changes to `tests/index.html` must be additive and must not break existing
   preview links, layout, or unrelated skill sections.

For skills that generate multiple themed HTML previews, place each preview in a
stable subfolder beneath the skill test folder:

```text
tests/<skill-name>/<preview-name>/index.html
```

For skills that generate Markdown, JSON, or other non-HTML artifacts, keep those
artifacts directly under `tests/<skill-name>/` unless the test requires multiple
named fixture groups.

## Validation Expectations

Before considering a change complete:

- Run the most relevant unit tests for the touched skill.
- Run static checks when the repository provides them. If no linter is
  configured for the changed language, use a lightweight syntax check where
  possible, such as `python -m py_compile` for Python files.
- For generated HTML, open or otherwise verify the generated page and any
  `tests/index.html` preview entry that was added.
- Report any checks that could not be run, including the reason.

## Output Discipline

- Keep generated artifacts deterministic and self-contained.
- Tests must exercise real scenarios with real accessible inputs and the actual
  skill workflow. Do not use demo, mock, placeholder, cached, or hand-crafted
  data as a successful test result.
- If a required runtime dependency, network source, browser service, or real
  content-generation step is unavailable, report the test as blocked or failed
  instead of fabricating fallback output.
- Do not generate test code for testing Python scripts.
- Only place skill-generated result content in test output folders.
- Use UTC+8 for every generated date/time value across all skills. Generated
  `Date` fields must use `YYYY-MM-DD HH:mm:ss`.
- Do not introduce external runtime fetches for static preview output.
- Avoid fabricating source content, screenshots, or images.
- Keep file names lowercase with hyphens for frontend-facing generated files.
- Prefer small, focused diffs over broad cleanup.
