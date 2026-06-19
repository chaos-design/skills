# Templates

Deck-stage template shells live under `templates/<slug>/template.html`.

Each generated template follows this shell:

```html
<deck-stage width="1920" height="1080">
  <section data-label="Title">...</section>
</deck-stage>
<script src="../../assets/runtime/deck-stage.js"></script>
```

## Bold Template Pack

`templates/templates.json` and `templates/selection-index.json` are the source of truth for the registered template list. The current set follows the reference design pack at:

`https://github.com/zarazhangrui/frontend-slides/tree/main/plugins/frontend-slides/skills/frontend-slides/bold-template-pack/templates`

The pack contains 34 visual directions. Read `templates/selection-index.json` first, shortlist candidates from metadata, then read only shortlisted `preview.md` files. After choosing a template, read that template's `design.md` before generating the full deck.

## Visual Templates

Visual templates use direct stage sections:

```html
<deck-stage width="1920" height="1080">
  <section data-label="Opening">...</section>
  <section data-label="Key Point">...</section>
</deck-stage>
```

## Required Files

Every registered template directory must include:

- `templates/<slug>/template.html`
- `templates/<slug>/preview.md`
- `templates/<slug>/design.md`
