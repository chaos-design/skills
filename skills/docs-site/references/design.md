# Design reference (based on ragx PR #8)

The generated layout is a faithful, dependency-free distillation of the ragx
site work in `chaos-design/ragx` PR #8 ("mobile header navigation,
full-screen navigation panel, fluid content width, and diagram zoom lightbox").

## Breakpoints

- Mobile: `max-width: 860px` (configurable via `breakpoint`).
- Desktop: > 860px. Two-column grid: `280px` sidebar + fluid content.

## Mobile top bar + full-screen nav panel

At ≤ 860px:

- A `position: sticky` top bar holds the brand (link to `/`), the theme
  switch and a hamburger toggle (three bars morph into an ✕ when open).
- The sidebar becomes `position: fixed`, filling the viewport below the top
  bar; `.sidebar-scroll` scrolls independently with `overscroll-behavior:
  contain`. A translucent backdrop dims the page.
- Open/close is driven by `body.nav-open`. Esc closes and returns focus to
  the toggle. Clicking a nav link or switching back to the desktop breakpoint
  auto-closes. `aria-expanded` / `aria-controls` stay in sync with state.

## Fluid content width

- Content padding is `clamp(20px, 3vw, 56px)`. The content column has no hard
  `max-width`; it tracks the available width so the layout never overflows.
- Document body is `max-width: 72ch` for readability, with
  `overflow-wrap: break-word` (and `anywhere` for inline code) so long tokens
  never break the column.

## Lightbox

- Any ` ```mermaid ` fence becomes a figure. Clicking it opens a full-viewport
  lightbox; the figure's `<pre>` is re-staged there and scaled with
  `transform: scale()` (fit, +/−, and close). Panning is clamped.

## Theme + i18n

- `data-theme` on `<html>` toggles CSS variables; a button switches light/dark
  and persists to `localStorage` (default `auto` follows `prefers-color-scheme`).
- EN/中 toggle switches nav and control labels via the `label_zh` fields.

## Multi-page

- Each config `pages[]` entry emits one self-contained `<slug>.html` file
  (inline CSS/JS, no external assets). `doc` pages render Markdown; `list`
  pages render a data table with sorting, filtering and status badges.
