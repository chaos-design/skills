# Chaos Design Skills

[中文](./README.zh-CN.md)

Chaos Design Skills is a curated collection of production-oriented agent skills
maintained at <https://github.com/chaos-design/skills>. The repository packages
repeatable workflows for content extraction, bilingual reading, slide
generation, frontend presentation, one-page HTML briefs, geographic flow
visualization, and social content capture.

Each skill is distributed as a standalone folder under `skills/<name>`. A skill
contains its runtime instructions, supporting scripts, documentation, examples,
and license file so that agents can install and use it independently.

## Features

- Ready-to-install skills for common content and presentation workflows.
- Bilingual English and Chinese documentation for the repository and every
  published skill.
- Shared content pipeline through `web-markdown`, which normalizes web content
  before downstream skills process it.
- `html-brief` renders structured answers as a single offline HTML file, with
  diagram geometry and themes computed rather than written by the model.
- Self-contained generated outputs for previews, slides, and reader pages.
- Repository-level testing conventions under `tests/` for validating generated
  artifacts without mixing outputs from unrelated skills.
- Apache-2.0 licensing for the repository and each distributable skill.

## Available Skills

| Skill | Purpose | Documentation |
| --- | --- | --- |
| `bilingual-reader` | Builds bilingual reading pages with structured summaries, translations, and glossary support. | [English](./skills/bilingual-reader/README.md) / [中文](./skills/bilingual-reader/README.zh-CN.md) |
| `content-slides` | Converts normalized content into self-contained presentation slides. | [English](./skills/content-slides/README.md) / [中文](./skills/content-slides/README.zh-CN.md) |
| `frontend-slides` | Generates frontend-oriented slide pages and visual presentation material. | [English](./skills/frontend-slides/README.md) / [中文](./skills/frontend-slides/README.zh-CN.md) |
| `geo-flow-map` | Produces geographic flow map visualizations from structured movement data. | [English](./skills/geo-flow-map/README.md) / [中文](./skills/geo-flow-map/README.zh-CN.md) |
| `html-brief` | Renders a complex answer as one self-contained HTML brief: panel grid, flow and sequence diagrams, comparison tables, two themes and a light/dark switch. | [English](./skills/html-brief/README.md) / [中文](./skills/html-brief/README.zh-CN.md) |
| `web-markdown` | Fetches and converts web content into stable Markdown for other skills. | [English](./skills/web-markdown/README.md) / [中文](./skills/web-markdown/README.zh-CN.md) |
| `x-tweet-fetcher` | Extracts X/Twitter content for workflows that need social-source input. | [English](./skills/x-tweet-fetcher/README.md) / [中文](./skills/x-tweet-fetcher/README.zh-CN.md) |

## Installation

Install a skill directly from this repository with `npx skills add`:

```bash
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
npx skills add https://github.com/chaos-design/skills --skill frontend-slides
npx skills add https://github.com/chaos-design/skills --skill geo-flow-map
npx skills add https://github.com/chaos-design/skills --skill html-brief
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
```

Install dependencies together when a workflow requires more than one skill.
`bilingual-reader` and `content-slides` both use `web-markdown` as their content
normalization entry point:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

`web-markdown` uses `x-tweet-fetcher` as its low-level bridge for X/Twitter and
supported Chinese platform URLs:

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill web-markdown
```

`html-brief` needs only the Python 3 standard library, so it installs on its
own. It accepts Markdown from `web-markdown`, a local document, or pasted text:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill html-brief
```

## Usage Guide

1. Choose the skill that matches the task and read its dedicated README.
2. Install the skill and any documented dependencies with `npx skills add`.
3. Provide the agent with real input, such as a URL, Markdown file, or structured
   data source supported by the skill.
4. Review the generated output under the matching test or output directory.
5. Run the validation steps documented by the skill before using the result.

For content-based workflows, the typical processing path is:

```text
raw input -> web-markdown -> normalized Markdown -> downstream skill -> final artifact
```

If content fetching, extracted text, images, code blocks, or downstream
processing fails, first verify that `web-markdown` is installed correctly and can
produce valid Markdown for the same input.

When an agent finds a required skill dependency missing, it should ask before
installing it, show the exact `npx skills add` command, and continue only after
the dependency is available. If the dependency is declined, the skill should stop
or use only a documented temporary fallback.

## Technical Architecture

```text
.
|-- skills/
|   |-- <skill-name>/
|   |   |-- SKILL.md
|   |   |-- README.md
|   |   |-- README.zh-CN.md
|   |   |-- LICENSE
|   |   `-- scripts/ or references/
|-- screenshots/
|   `-- <skill-name>/
`-- tests/
    |-- <skill-name>/
    `-- index.html
```

- `skills/<skill-name>/SKILL.md` is the canonical instruction entry point used
  by agents.
- `skills/<skill-name>/README.md` and `README.zh-CN.md` document installation,
  usage, examples, and operational guidance for users.
- `scripts/` and `references/` contain implementation helpers and detailed
  workflow guidance where a skill needs them.
- `screenshots/<skill-name>/` stores documentation screenshots for the matching
  skill.
- `tests/<skill-name>/` stores generated validation artifacts for the matching
  skill.
- `tests/index.html` links to generated HTML previews when a skill produces
  browser-viewable output.

## Development

Clone the repository and inspect the skill you want to work on:

```bash
git clone https://github.com/chaos-design/skills.git
cd skills
find skills/<skill-name> -maxdepth 2 -type f | sort
```

Keep changes scoped to the relevant skill directory, screenshot folder, or test
folder. Generated test outputs must go under `tests/<skill-name>/`. Do not
rename, delete, or reorganize unrelated skill artifacts as part of a focused
change.

Before opening a pull request, run the checks that match the files you changed.
For Python helpers, use a syntax check or the repository's configured test
command where available:

```bash
python -m py_compile skills/<skill-name>/scripts/*.py
pytest
```

For documentation-only changes, verify Markdown structure, relative links, and
any referenced screenshots or generated previews.

## Contribution Guide

We welcome issues, documentation fixes, bug reports, and skill improvements.
Please keep contributions focused and reviewable.

### Reporting Issues

Open an issue with:

- The affected skill name.
- A clear description of the expected and actual behavior.
- Reproduction steps using real, accessible inputs.
- Relevant logs, generated files, screenshots, or command output.
- Environment details such as operating system, runtime versions, and installed
  skill dependencies.

Avoid reporting failures with private, inaccessible, or placeholder inputs unless
you can provide enough detail for maintainers to reproduce the problem.

### Pull Requests

Before submitting a pull request:

- Check whether an existing issue or pull request already covers the change.
- Keep the diff focused on one skill, bug, or documentation topic.
- Update both English and Chinese documentation when user-facing behavior
  changes.
- Add or refresh generated validation artifacts under `tests/<skill-name>/` when
  the change affects output behavior.
- Preserve existing preview entries in `tests/index.html`; only add new links
  when needed.
- Include the commands you ran and any checks you could not run in the pull
  request description.

### Code and Documentation Standards

- Follow the existing style of the skill you are editing.
- Use lowercase, hyphen-separated names for frontend-facing files.
- Keep generated artifacts deterministic and self-contained.
- Use real accessible inputs for validation; do not fabricate source content,
  screenshots, or successful test results.
- Use UTC+8 for generated `Date` values, formatted as `YYYY-MM-DD HH:mm:ss`.
- Keep documentation practical: describe what the skill does, when to use it,
  how to run it, how to validate it, and known limitations.
- Add concise comments only where they explain non-obvious logic.

## Maintainers

Chaos Design maintains this repository. For project-level questions, open a
GitHub issue. For skill-specific questions, use the issue title or description
to name the affected skill so maintainers can route the report quickly.

## License

This repository is licensed under the [Apache License 2.0](./LICENSE). Each
skill directory also includes a copy of the same license for distribution.
