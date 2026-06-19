# Chaos Design Skills

[中文](./README.zh-CN.md)

This repository contains the agent skills maintained at
<https://github.com/chaos-design/skills>.

Each skill lives under `skills/<name>` and uses `SKILL.md` as the canonical
instruction entry point. Skill introductions, install commands, usage examples,
and extended notes live in the matching skill directory.

# Install

Install a skill directly from this repository with `npx skills add`:

```bash
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
npx skills add https://github.com/chaos-design/skills --skill frontend-slides
npx skills add https://github.com/chaos-design/skills --skill geo-flow-map
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
```

# Dependencies

`bilingual-reader` and `content-slides` both depend on `web-markdown` as the content normalization entry point. When either skill is used, the collaboration flow is:

```text
raw input -> web-markdown converts it to standard Markdown -> bilingual-reader / content-slides processes the Markdown -> final output
```

Install `web-markdown` together with `bilingual-reader` or `content-slides`:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

If content fetching, extracted text, images, code blocks, or downstream processing fails, first verify that `web-markdown` is installed correctly and can produce valid Markdown for the same input.

`url-content-fetcher` depends on `x-tweet-fetcher` for X/Twitter URLs:

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

When an agent finds a required skill dependency missing, it should ask the user before installing it, show the exact `npx skills add` command, and continue only after the dependency is available. If the user declines, the skill should either stop or use only the documented temporary fallback.

# Skill Docs

- [Bilingual Reader](./skills/bilingual-reader/README.md) ([中文](./skills/bilingual-reader/README.zh-CN.md))
- [Content Slides](./skills/content-slides/README.md) ([中文](./skills/content-slides/README.zh-CN.md))
- [Frontend Slides](./skills/frontend-slides/README.md) ([中文](./skills/frontend-slides/README.zh-CN.md))
- [Geo Flow Map](./skills/geo-flow-map/README.md) ([中文](./skills/geo-flow-map/README.zh-CN.md))
- [URL Content Fetcher](./skills/url-content-fetcher/README.md) ([中文](./skills/url-content-fetcher/README.zh-CN.md))
- [Web Markdown](./skills/web-markdown/README.md) ([中文](./skills/web-markdown/README.zh-CN.md))
- [X Tweet Fetcher](./skills/x-tweet-fetcher/README.md) ([中文](./skills/x-tweet-fetcher/README.zh-CN.md))

Skill directories under `skills/` contain the files needed by the skill itself,
including a copy of this repository's Apache-2.0 `LICENSE`.

# Skill Shape

Skills are folders with a `SKILL.md` file containing YAML frontmatter and
instructions:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

The required frontmatter fields are:

- `name` - A unique identifier for your skill (lowercase, hyphens for spaces)
- `description` - A complete description of what the skill does and when to use it
