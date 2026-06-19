# Content Slides

[中文](./README.zh-CN.md)

Content Slides converts existing source material into a self-contained 16:9 HTML slide deck. Use it when the user provides URLs, PDFs, DOCX files, Markdown files, plain text, screenshots, or pasted notes and asks to make slides, a presentation, a frontend slide deck, or an HTML deck. It depends on [Web Markdown](../web-markdown/README.md) to convert raw input into standard Markdown before the deck generation step.

Content Slides is the conversion-first skill: the source already exists, and the skill extracts, restructures, designs, verifies, and delivers one runnable HTML deck file. For reusable deck-stage templates and the larger visual template gallery, see [Frontend Slides](../frontend-slides/README.md).

## Install

Install this skill directly from the Chaos Design Skills repository:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

`web-markdown` is a required dependency and must be installed alongside `content-slides`. If only `content-slides` is installed, URL or complex source content may not be normalized to Markdown and downstream deck generation may fail.

When an agent discovers that `web-markdown` is missing, it should ask the user before installing it, show the command above, and continue only after the dependency is available.

## Features

- Standard workflow: raw input -> `web-markdown` converts it to Markdown -> `content-slides` extracts a content brief and generates the HTML deck.
- Accepts URLs, PDFs, DOCX files, Markdown files, plain text, screenshots, and pasted notes when the Agent platform can access them.
- Final output keeps only `source.md` and one browser-runnable HTML deck authored on a fixed 1920×1080 stage.
- Defaults to Simplified Chinese slide content unless the user requests another language.
- Uses keyboard, wheel, touch, and compact bottom previous/next controls. Slides include no anchor or jump-dot information by default; side anchors are opt-in only.
- Includes a fallback helper script for content extraction.

## Screenshot

<img src="../../screenshots/content-slides/a-practical-guide-to-building-ai-agents.webp" width="520" alt="Content Slides example deck screenshot">

The screenshot is generated from `tests/content-slides/a-practical-guide-to-building-ai-agents/a-practical-guide-to-building-ai-agents.html`.

## Usage

Invoke the skill when the user asks to turn existing material into slides, for example:

```text
Use content-slides to turn this article URL into a Chinese HTML presentation: https://example.com/report
```

```text
用 content-slides 把这份 PDF 做成高密度阅读型汇报页，保留关键数据和来源。
```

```text
Make a slide deck from the attached screenshot. Treat the screenshot as the source content.
```

The source can be a URL, PDF, DOCX file, Markdown file, plain text, screenshot, pasted notes, or a combination of notes plus screenshots when the Agent platform can access those inputs.

### Workflow

1. Detect the input type: URL, PDF, DOCX file, Markdown file, plain text, screenshot, or pasted notes.
2. Invoke `web-markdown` to normalize the raw input into Markdown while preserving title, source, body text, images, links, tables, and code blocks.
3. Ask the user whether the generated Markdown is acceptable or needs modification. Do not continue until the user confirms.
4. Extract a clean content brief from the standard Markdown: title, source, sections, key facts, quotes, stats, and usable images.
5. Choose a density mode:
   - **Low density / speaker-led** for talks, keynotes, and pitches.
   - **High density / reading-first** for reports, articles, and async handouts.
6. Pick one visual style from `references/style-presets.md` and keep it consistent.
7. Generate one self-contained HTML file on a fixed 1920×1080 stage.
8. Verify one-slide-at-a-time visibility, 16:9 scaling, navigation, animation, embedded image rendering, and overflow.
9. Delete temporary review, revision, metadata, scratch, screenshot, or planning artifacts before finishing.

### Output

Final output should contain only the normalized Markdown source and the generated HTML deck. Generated HTML files should be named from the source title, not generic names such as `index.html` or `slides.html`:

```text
source.md
<source-title-slug>.html
```

### Practical Notes

- Default deck language is Simplified Chinese unless the user requests another language.
- Preserve facts, numbers, quotes, and source attribution; do not invent filler content.
- Split overflowing slides instead of shrinking text below comfortable reading size.
- Keep slide chrome outside the scaled stage and verify keyboard, wheel, touch, and bottom control navigation before delivery.

### Troubleshooting

- If content processing fails, the body is empty, or images/code blocks are missing, first confirm that `web-markdown` is installed correctly.
- Run `web-markdown` on the same input and verify that it produces valid Markdown. Fix fetching or Markdown conversion before continuing with deck generation.

## Skill Files

```text
skills/content-slides/
├── SKILL.md
├── references/
│   ├── animation-patterns.md
│   ├── html-template.md
│   ├── style-presets.md
│   └── viewport-base.css
└── scripts/
    └── extract_content.py
```

Read [SKILL.md](SKILL.md) for the full workflow and generation rules.

## Updating Screenshots

When the example deck changes, regenerate the screenshot from the test fixture at 1280×720 and save it as:

```text
screenshots/content-slides/a-practical-guide-to-building-ai-agents.webp
```
