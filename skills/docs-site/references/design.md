# Design reference

The generated layout is a dependency-free, dark-first responsive documentation
design: a pinned sidebar, a single scrolling content column, a mobile dropdown
menu, a diagram zoom lightbox, a light/dark theme switch and a full EN/中
language toggle.

## Color and type tokens

- Dark is the default palette: `--bg #0c0d0e`, `--surface #141618`,
  `--surface-2 #1b1e21`, `--surface-3 #24282c`, `--ink #f3f0e9`,
  `--muted #9da3a7`, `--faint #696f73`, `--line #34393d`.
- Accents: `--accent #6f9dff` with `--cyan`, `--green`, `--yellow`, `--red`,
  `--purple` for links, the brand gradient and status badges.
- The brand mark is a gradient square (accent → cyan) with a condensed display
  font; the body uses a system sans stack and code uses a monospace stack.
- `[data-theme='light']` overrides the surface/ink/line/accent tokens, so a
  single component tree renders in both themes.

## Breakpoints

- Mobile: `max-width: 860px` (configurable via `breakpoint`).
- Desktop: > 860px. Grid: `300px` sidebar + `minmax(0, 1fr)` content.

## Desktop shell and sidebar

- `.shell` is locked to one viewport (`height: 100vh`, `overflow: hidden`) so a
  long or empty document can never stretch or collapse the menu.
- `.sidebar` is a flex column with three regions:
  - `.sidebar-head` — pinned brand (gradient mark, name, sub-line) plus the
    theme button.
  - `.sidebar-scroll` — the only scrolling part of the sidebar; grouped nav
    with uppercase `.nav-group-label` headings and `.nav-link` items. The
    active item uses `.is-active` (raised surface + border).
  - `.sidebar-github` — pinned footer where the GitHub link and the language
    pill are equal-width `36px` controls with identical box metrics.
- `.content` owns the page scrollbar with `overscroll-behavior: contain`.
  `.content-inner` uses `padding-inline: clamp(20px, 3vw, 56px)` and the
  document body is `max-width: 72ch`, so wide tables and code scroll inside
  themselves instead of widening the column.

## Mobile top bar and dropdown

At ≤ 860px:

- `.site-header` is `position: fixed` at the top (`--header-h: 56px`); the shell
  reserves that height with `padding-top`. It holds the brand, a GitHub icon
  button, a square language pill and the `.nav-toggle` with three bars that
  morph into an ✕ when open.
- `.sidebar` becomes `position: fixed` below the header, filling the rest of the
  viewport with its own scroll area. It is hidden until `body.nav-open` is set.
- `.nav-backdrop` is only rendered (`display: block`) while the panel is open;
  it dims the page and is a tap target for closing.
- JS keeps `aria-expanded` / `aria-controls` in sync, moves focus into the panel
  on open, scrolls the active link into view, closes on link click, backdrop
  click, Esc (restoring focus to the toggle), navigation and a switch back to a
  desktop-width viewport. `prefers-reduced-motion` disables the animations.

## Language and theme

- Static markup carries `data-i18n` / `data-i18n-title` / `data-i18n-ph` keys.
  `I18N_JS` holds flat `zh` / `en` tables built from the config, re-labels every
  marked element on toggle, updates `<html lang>`, and persists to
  `docs-site-lang`. It emits a `docs:lang` event so the list count re-renders.
- `THEME_JS` applies `data-theme` on `<html>`, resolving `auto` through
  `prefers-color-scheme`, and persists explicit choices to `docs-theme`.

## Lightbox

- Any ` ```mermaid ` fence becomes a figure. Clicking it opens a full-viewport
  lightbox; the figure's `<pre>` is re-staged there and scaled with
  `transform: scale()` (fit, +/− and close). Esc closes it.

## Multi-page

- Each config `pages[]` entry emits one self-contained `<slug>.html` file
  (inline CSS/JS, no external assets). `doc` pages render Markdown; `list`
  pages render a data table with sorting, filtering, status badges and a live
  match count. Nav links point at the real sibling files, and the brand links
  to the first configured page.
