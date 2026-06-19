# Frontend Slides Harness

Turn source material from a URL, file, image, pasted text, notes, or PPT-style content into a polished 16:9 HTML slide deck.
Invoke this skill when the user asks to create slides, a presentation, a deck-stage page, or a document-to-slides experience.

## Deliverable

Generate a runnable HTML deck. Prefer a single self-contained HTML file with inline CSS, slide content, and `assets/runtime/deck-stage.js` inlined into the page. Use external sibling assets only when the user provides image files that must remain separate.

Format the generated HTML before delivery. Treat indentation as tab-based structure with an indent width of 2 spaces for nested HTML, CSS, and JavaScript blocks, while preserving source code block indentation exactly as it appeared in the source material.

The deck must use:

```html
<deck-stage width="1920" height="1080">
  <section data-label="Title">...</section>
  <section data-label="Key Point">...</section>
</deck-stage>
```

Every slide must be a direct `section` child of `deck-stage`. Do not create nested slide containers or rely on page scrolling.

## Language

Unless the user explicitly specifies otherwise, generate viewer-facing slide text in Simplified Chinese. Preserve proper nouns, URLs, code, product names, and numbers as-is. Translate English source material naturally rather than literally.

## Workflow

### 1. Ingest Source

- For URLs, fetch the page and extract the article body, title, source, headings, lists, quotes, and useful figures.
- For local files or attachments, read or extract the accessible content directly.
- For images, use vision/OCR to preserve visible text, hierarchy, charts, and visual meaning.
- For pasted text, use it directly and infer structure from headings, paragraphs, and lists.
- Do not invent facts. If extraction is partial, state the gap and proceed only with reliable content.

### 2. Build A Slide Brief

Create a compact working brief before writing HTML:

```text
Title:
Source:
Audience:
Density: low-density speaker-led | high-density reading-first
Sections:
  1. ...
Images:
Notable quotes/stats:
```

Use high density for reports, article digests, handouts, and async reading. Use low density for speeches, pitches, and speaker-led talks.

### 3. Select A Template

Read `templates/templates.json` or `templates/selection-index.json` first. The template set follows the Bold Template Pack reference design. Shortlist by tone, mood, density, scheme, and content shape. Read only the shortlisted `preview.md` files, then read the selected template's `design.md` and `template.html`.

Use these visual templates for custom narrative pacing and stronger art direction; adapt the slide structure to the user's content rather than forcing a fixed document shape.

### 4. Generate The Deck

- Keep the stage fixed at 1920x1080 and scale the whole stage with the runtime.
- Split overflowing content into more slides instead of shrinking type below readable sizes.
- Use `data-label` values that identify slide purpose.
- Keep one visual system across the whole deck.
- Use `references/style-presets.md`, `references/animation-patterns.md`, and `references/viewport-base.css` when implementing custom styling.
- Avoid generic card-grid layouts unless the source content genuinely calls for them.

### 5. Validate

Before delivering, verify:

- The HTML has no unreplaced placeholders.
- All slides fit inside the 1920x1080 stage without scrolling or overlap.
- Keyboard navigation works through `deck-stage`.
- Touch/tap navigation works through `deck-stage`.
- Print layout shows one slide per page.
- A final self-contained HTML deck does not depend on an npm build step.
