---
name: docs-site
description: >
  Quickly creates a dark-first, responsive, multi-page static documentation
  site from Markdown plus a small JSON config. Generates the documentation
  structure automatically, wires a configurable navigation menu with a pinned
  desktop sidebar and a mobile dropdown panel, integrates existing Markdown /
  data formats, and adds a light/dark theme switch, a full EN/中 UI toggle and
  a data "list" page type with client-side sorting (commit count,
  last-updated), text filters and status badges. Invoke when the user asks to
  build a docs site, documentation page, multi-page help center, or to publish
  structured content as an offline, self-contained static site.
---

# Docs Site

Use this skill to turn Markdown content and a JSON config into a responsive,
multi-page, self-contained static documentation site. The output is a set of
offline HTML files that open as-is — no build step, no external runtime
fetches.

The layout is a dark-first, viewport-locked documentation design: a pinned
300px sidebar with a gradient brand mark, grouped navigation and a matched
GitHub / language footer; a content column that owns the only scrollbar; and
an 860px breakpoint where a fixed top bar (brand, GitHub, language pill,
three-bar toggle) expands the sidebar into a full-width dropdown with a
backdrop. Fluid content width, a diagram lightbox, a light/dark switch and a
full EN/中 UI toggle complete the design.

## What the skill does

- Generates the documentation structure from your config (one HTML per page).
- Configures the navigation menu (flat or grouped) with active-state tracking
  and real sibling-page links; the active item is scrolled into view when the
  mobile panel opens.
- Integrates existing formats: Markdown (with optional front-matter) for doc
  pages, JSON data for list pages.
- Produces a pinned, responsive layout: the shell never stretches, the brand
  and footer stay put, and only the content scrolls.
- Adds a list page type that renders a data table with client-side sorting
  (e.g. commit count, last-updated time), text search, status filters and
  color-coded status badges.
- Renders ` ```mermaid ` fences as real diagrams: a built-in, dependency-free
  client-side renderer draws flowcharts and sequence diagrams as inline SVG
  (theme-aware, offline, with a graceful fallback to the source block), and
  every diagram opens in a zoom lightbox.
- Adds a sticky right-rail mini TOC (h2/h3/h4 anchor links with scrollspy
  highlight and a list that auto-follows the active entry) to doc pages that
  have two or more headings, and a prev/next chapter bar pinned to the
  bottom of the content column on every page following the config order.
- Re-labels the entire UI on EN/中 switch (nav, chrome, list controls,
  toc, pager, lightbox) and persists both language and theme choices to
  localStorage.

## Inputs

1. **Content** — a folder with Markdown files and optional JSON data files.
2. **Config** — a single JSON file. See `templates/site-config.sample.json`.

## Workflow

```text
1  Gather    Collect the real source content. For docs use web-markdown to
             pull URLs into Markdown; for a pull-request list, get real data
             (git history or the GitHub API) — never hand-write fixture data.
  🔽
2  Draft     Write the site JSON config: title, tagline, theme, nav menu,
             and one entry per page. Each page is type "doc" (points at a
             .md file) or "list" (points at .json data with columns,
             sortable keys, status_field and filters).
  🔽
3  Generate  python3 scripts/docs_site.py generate --config site.json \
                 --content ./docs --out ./out
  🔽
4  Validate  python3 scripts/docs_site.py check --out ./out — confirms every
             page is doctype-complete, responsive, and that list pages carry
             the sortable/filter/badge controls.
  🔽
5  Deliver   Report the out dir, the pages produced, and the check results.
             Open the HTML pages to verify the mobile breakpoint, nav panel,
             theme switch and list sorting all work.
```

## Config reference

```json
{
  "title": "My Docs",
  "tagline": "Short one-liner",
  "description": "Page hero copy",
  "repo": "github.com/owner/repo",
  "theme": "dark",
  "lang": "zh",
  "i18n": ["zh", "en"],
  "brand_mark": "M",
  "brand_sub": "Documentation",
  "brand_sub_zh": "文档中心",
  "breakpoint": 860,
  "nav": [
    {"slug": "introduction", "label": "Introduction", "label_zh": "简介"},
    {"slug": "pull-requests", "label": "Pull Requests", "label_zh": "拉取请求"},
    {"slug": "guides", "label": "Guides", "label_zh": "指南", "group": "Deep dive",
     "group_zh": "深入阅读",
     "items": [{"slug": "quick-start", "label": "Quick start", "label_zh": "快速开始"}]}
  ],
  "pages": [
    {"slug": "introduction", "type": "doc", "source": "docs/introduction.md"},
    {"slug": "pull-requests", "type": "list",
     "source_data": "pr-data/pull-requests.json",
     "columns": [
       {"key": "number", "label": "#"},
       {"key": "title", "label": "Title", "link": "url"},
       {"key": "commits", "label": "Commits"},
       {"key": "last_updated", "label": "Last updated"},
       {"key": "status", "label": "Status"}
     ],
     "sortable": ["commits", "last_updated"],
     "status_field": "status",
     "filters": ["merged", "closed", "open", "in-review"]}
  ]
}
```

- `nav` entries with `group` render as a labeled section whose `items` are
  nested links. Entries without `group` are top-level links. Every entry links
  to `<slug>.html`, so the menu navigates between the generated pages.
- `label_zh` / `group_zh` provide the Chinese label for nav items and group
  headings; without them the English label is reused. `brand_mark` is the
  logo glyph (defaults to the first letter of `title`), `brand_sub` /
  `brand_sub_zh` are the two lines under the brand name, and `repo` feeds the
  GitHub entries in the sidebar footer and mobile header.
- `lang` is the initial language (`zh` by default) and `i18n` is the toggle
  cycle order. `theme` accepts `dark` (default), `light` or `auto`.
- `breakpoint` is the mobile width in pixels (`860` by default) and must be an
  integer; generation fails with a clear error on a non-numeric value.
- A `list` page `columns` with `"link": "url"` turns that column's value into
  an outbound link. `sortable` lists the column keys the user may click to
  reorder; `status_field` is the column rendered as a badge; `filters` are
  the status options for the filter dropdown.

## List page behavior

- Columns in `sortable` show a ⇅ hint and sort ascending/descending on click
  (numeric for numbers, string compare otherwise).
- A free-text search filters across the whole row; a status dropdown filters
  by `status_field`.
- Status values render as color-coded badges (open, merged, closed, draft,
  in-review, changes-requested, …).
- A live count shows how many rows match the current filters.

## Layout, menu and mobile behavior

- Desktop (> breakpoint): a `300px` sidebar and a fluid content column inside a
  `100vh` grid. The brand head and the GitHub / language footer are pinned; the
  nav scrolls independently; only the content column scrolls the page. Between
  the breakpoint and `1200px` the sidebar narrows to `250px` so mid-size
  windows keep a usable content column, and wide Markdown tables scroll inside
  a `.table-scroll` wrapper instead of stretching the column.
- Doc pages with two or more h2/h3/h4 headings also get a sticky right-rail
  `.toc` (multi-level anchor links with per-level indent, scrollspy
  highlight, an internally scrolling list that follows the active entry,
  hidden below the breakpoint); every page carries a `.page-pager` linking
  the previous and next chapter in config page order — `position: fixed` at
  the viewport bottom under the content column (one compositor layer, so
  scrolling never jitters it), styled as a frosted blur band with a single
  top hairline instead of a floating bordered box — re-labeled by the
  language toggle.
- Mobile (≤ breakpoint, `860px` by default): a fixed `56px` top bar carries the
  brand, a GitHub icon button, a theme button, a square language pill and a
  three-bar toggle that morphs into a close cross. The sidebar becomes a
  full-width panel below the bar with its own scroll area and a tap-to-close
  backdrop. Esc closes it and restores focus to the toggle; navigation and a
  switch back to desktop width close it too.
- There is exactly one active nav link: when the landing page also appears in
  `nav`, that entry owns the active state and the synthetic Home link stays
  inactive. The active link is scrolled into view when the mobile panel opens,
  and `aria-expanded` / `aria-controls` stay in sync with the panel state.

## Language and theme

- The EN/中 button cycles through `i18n`, persists the choice under
  `docs-site-lang`, and re-labels all `data-i18n` elements (nav, chrome, list
  search/filter, count, lightbox) in place. `<html lang>` follows the choice.
- The theme button cycles dark/light, persists under `docs-theme`, and `auto`
  resolves via `prefers-color-scheme`.

## Diagrams

A ` ```mermaid ` fence inside a doc page becomes a figure at the fence's
original position (never a second source block):

- A built-in, dependency-free renderer in the page draws the diagram as inline
  SVG. Flowcharts (`graph`/`flowchart` with TB/LR/RL/BT, arrow/dotted/thick/
  open edges, labeled edges via `--text-->` or `-->|text|`, and rect/rounded/
  diamond/circle/cylinder/hexagon/subroutine nodes) and sequence diagrams
  (participants, `->>`/`-->>`/`-)` messages, `+`/`-` activations, notes,
  loop/alt/opt/par frames) are supported. `subgraph`, `classDef`, `class`,
  `style` and `click` lines are ignored gracefully instead of failing.
- The SVG is theme-aware: it is styled with CSS variables, so diagrams recolor
  automatically when the light/dark switch flips.
- If the source cannot be parsed, the figure falls back to showing the source
  as a code block — the page never breaks on unsupported syntax.
- Clicking a figure opens a full-viewport lightbox that stages the rendered
  SVG with fit/+−/close SVG-icon controls and Esc to close. Oversized
  diagrams shrink to fit the viewport; small ones open at their natural size
  instead of being upscaled. Zooming past the viewport makes the stage
  scrollable and mouse-draggable (touch pans natively), so any region of a
  zoomed diagram stays reachable; +/− keep the centered point anchored
  instead of jumping the view.

## Output contract

Generated files live under the `--out` directory, one `<slug>.html` per page,
self-contained (inline CSS/JS), offline-capable. Page titles come from the
config or the Markdown front-matter `title`.

Config-derived text is escaped exactly once for its destination: HTML text uses
`html.escape`, while strings embedded in inline `<script>` blocks use a JSON
literal with `<`, `>` and `&` escaped, so a label containing `</script>` cannot
break out of the script element. Breadcrumbs are built from raw config values
and escaped once.

## Boundaries

- This skill builds the docs *site*; use `web-markdown` to fetch source
  content, `content-slides`/`frontend-slides` for decks, and `html-brief` for
  a single explainer page. It does not deploy or host the site.
- Do not fabricate fixture data. A list page must be fed real data (real git
  history or a real API response).

Read `references/design.md` before adapting the layout.

## Script

```bash
python3 skills/docs-site/scripts/docs_site.py generate \
  --config site.json --content ./docs --out ./out
python3 skills/docs-site/scripts/docs_site.py check --out ./out
```
