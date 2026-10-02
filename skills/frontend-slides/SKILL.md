---
name: "frontend-slides"
description: "Generates deck-stage HTML presentation pages. Invoke for articles, notes, documents, images, or PPT-style content that should become slides."
---

# Frontend Slides

Create HTML slide decks from articles, notes, documents, images, or PPT-style source content. Final runnable decks use the shared deck-stage component:

- `assets/runtime/deck-stage.js`
- `<deck-stage width="1920" height="1080">...</deck-stage>`
- direct `<section>` slide children with `data-label`

Do not delete or modify files inside `assets/runtime/`.

## Workflow

1. **Confirm purpose and mood.** Ask one concise question only when the deck purpose, audience, or tone is genuinely unclear.
2. **Discover content density.** Decide whether the deck is low-density speaker-led or high-density reading-first.
3. **Choose visual direction.** Read `references/style-presets.md` and `templates/templates.json`; for bold candidates, read only shortlisted `preview.md` files before selection.
4. **Generate cover preview when useful.** Save a deck-stage preview HTML and open it in the browser for visual confirmation on substantial decks.
5. **Generate the full deck.** Use a single template and render each slide as a direct `section` child inside `deck-stage`.
6. **Verify.** Open the resulting HTML and check stage scaling, keyboard navigation, touch zones, print behavior, and content fit.

## Output Contract

Template files load only:

```html
<script src="../../assets/runtime/deck-stage.js"></script>
```

When producing a final standalone deck, inline `assets/runtime/deck-stage.js` into the HTML unless the user explicitly asks for a multi-file output. Do not load other runtime entry points directly. The stage component owns presentation navigation and scaling.

Format the generated HTML before delivery. Treat indentation as tab-based structure with an indent width of 2 spaces for nested HTML, CSS, and JavaScript blocks, while preserving source code block indentation exactly as it appeared in the source material.

## Template References

The template set follows the Bold Template Pack reference design. Use `templates/templates.json` or `templates/selection-index.json` to shortlist by tone, mood, density, scheme, and content shape. Then use visual templates for custom pacing through direct stage sections:

```html
<deck-stage width="1920" height="1080">
  <section data-label="Title">...</section>
  <section data-label="Principle">...</section>
</deck-stage>
```

Read `preview.md` only during shortlisting. Read the selected template's `design.md` before generating the full deck.

## Project Assets

- `references/harness.md` provides the portable harness.
- `assets/runtime/deck-stage.js` is the browser runtime used by template shells.
- `assets/runtime-manifest.json` records the migrated runtime file hashes.
- `templates/templates.json` is the compact template index.
- `templates/selection-index.json` is the inherited visual selection index.
- `templates/<slug>/template.html` contains the runnable template shell.
- `templates/<slug>/preview.md` and `templates/<slug>/design.md` provide visual selection and implementation guidance.
- `references/style-presets.md`, `references/animation-patterns.md`, and `references/viewport-base.css` provide generation guidance.
