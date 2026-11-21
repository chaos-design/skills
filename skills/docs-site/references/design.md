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

- Mobile: `max-width: 860px` (configurable via `breakpoint`, an integer number
  of pixels; a non-numeric value fails generation with an explicit error).
- Intermediate desktop: below `1200px` the `--sidebar-w` token drops to
  `250px`, so mid-size windows keep a usable content column. Harmless under
  the breakpoint, where the mobile block overrides the shell.
- Desktop: > 860px. Grid: `var(--sidebar-w)` (300px, or 250px intermediate) +
  `minmax(0, 1fr)` content.

## Desktop shell and sidebar

- `.shell` is locked to one viewport (`height: 100vh`, `overflow: hidden`) so a
  long or empty document can never stretch or collapse the menu.
- `.sidebar` is a flex column with three regions:
  - `.sidebar-head` — pinned brand (gradient mark, name, sub-line) plus the
    theme button.
  - `.sidebar-scroll` — the only scrolling part of the sidebar; grouped nav
    with uppercase `.nav-group-label` headings and `.nav-link` items. The
    active item uses `.is-active` (raised surface + border), and exactly one
    link carries it: when the landing page is also a `nav` entry, that entry
    owns the state and the synthetic Home link stays inactive.
  - `.sidebar-github` — pinned footer where the GitHub link and the language
    pill are equal-width `36px` controls with identical box metrics.
- `.content` owns the page scrollbar with `overscroll-behavior: contain`.
  `.content-inner` uses `padding-inline: clamp(20px, 3vw, 56px)` and the
  document body is `max-width: 72ch`, so wide tables and code scroll inside
  themselves instead of widening the column. Markdown tables are wrapped in a
  `.table-scroll` container (`overflow-x: auto`), which is what actually
  absorbs wide tables on narrow viewports.

## Mobile top bar and dropdown

At ≤ 860px:

- `.site-header` is `position: fixed` at the top (`--header-h: 56px`); the shell
  reserves that height with `padding-top`. It holds the brand, a GitHub icon
  button, a theme button, a square language pill and the `.nav-toggle` with
  three bars that morph into an ✕ when open — the theme switch stays reachable
  on mobile because the sidebar head is hidden there.
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
- Config-derived strings are embedded in inline scripts as JSON literals with
  `<`, `>` and `&` escaped, so a label containing `</script>` cannot terminate
  the script element. HTML text (including the breadcrumb, built from raw
  config values) is escaped exactly once for its destination.

## Diagrams

- ` ```mermaid ` fences are emitted inline (at the fence's position) as a
  `.doc-figure` holding an empty `.mermaid-view`, the raw source in a hidden
  `.mermaid-src` block, an `.expand-mark` icon and a `data-i18n` caption.
- `MERMAID_JS` runs in the page and draws each figure as inline SVG. The
  flowchart subset covers `graph`/`flowchart` with TB/LR/RL/BT directions,
  arrow/dotted/thick/open edges (labeled via `--text-->` or `-->|text|`),
  chained statements and rect/rounded/diamond/circle/cylinder/hexagon/
  subroutine nodes; `subgraph`, `classDef`, `class`, `style` and `click` lines
  are ignored. The sequence subset covers participants, `->>`/`-->>`/`-)`/`--)`
  messages, `+`/`-` activations, notes and loop/alt/opt/par frames.
- Unparseable sources flip the figure to `data-rendered='source'`: the view is
  removed and the source block is unhidden, so the page never breaks.
- SVG styling uses the theme tokens (`.mm-node` fills use `var(--surface-3)`,
  edges `var(--muted)`, …), so diagrams recolor when `[data-theme]` flips.
  Marker ids are suffixed with a per-figure counter to stay unique per page.

## Lightbox

- Clicking a `.doc-figure` (or pressing Enter on it) opens a full-viewport
  lightbox. `LIGHTBOX_JS` stages a deep clone of the figure's rendered SVG
  inside a `.lb-box` → `.lb-diagram` pair: the wrap is pinned to the diagram's
  natural size and carries `transform: scale(s)`, while the box takes the
  scaled layout size (`floor(natW·s)` × `floor(natH·s)`), so the stage — an
  `overflow: auto` flex container with the box centered via `margin: auto` —
  grows scrollbars exactly when the zoomed content outgrows the viewport.
- The base scale fits the stage against the SVG's `viewBox`; +/− multiply a
  user zoom on top (fit resets it). Zoom steps re-anchor the currently
  centered point instead of jumping, and the stage gains a `can-pan` grab
  cursor when panning is possible. Mouse drag pans the stage (touch pans
  natively; wheel and scrollbars always work). When the renderer fell back to
  source, the source block is staged the same way. Esc closes and the body
  scroll lock is released.

## Multi-page

- Each config `pages[]` entry emits one self-contained `<slug>.html` file
  (inline CSS/JS, no external assets). `doc` pages render Markdown; `list`
  pages render a data table with sorting, filtering, status badges and a live
  match count. Nav links point at the real sibling files, and the brand links
  to the first configured page.
