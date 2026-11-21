# Docs Site

[中文](./README.zh-CN.md)

Generates a responsive, multi-page, self-contained static documentation site
from Markdown content plus a small JSON config. No build step, no external
runtime fetches — every page is an offline HTML file.

The layout is a dark-first, responsive documentation design: a pinned 300px
sidebar (brand header, scrollable grouped nav, and a matched GitHub / language
footer pinned in place), a content column that owns its own scroll inside a
viewport-locked shell, fluid content width, and a diagram lightbox. At 860px and
below, a fixed top bar (brand, GitHub, theme, language pill and a three-bar
toggle) expands the sidebar into a full-width dropdown with its own scroll area
and a dimming backdrop. A light/dark theme switch and a real EN/中 label toggle
are included; both persist to localStorage.

## Features

- **Automatic structure** — one self-contained HTML file per page, generated
  from your config.
- **Configurable navigation** — flat or grouped menus with active-state
  tracking and real sibling-page links; rendered as a pinned desktop sidebar
  and a full-width mobile dropdown that scrolls the active entry into view.
- **Format integration** — Markdown (with optional front-matter) for doc
  pages, JSON data for list pages.
- **Responsive + multi-page** — a viewport-locked two-column shell where only
  the content scrolls, a ≤860px mobile top bar with a morphing hamburger, a
  tap-to-close backdrop, and fluid content width that never overflows; wide
  Markdown tables scroll inside their own wrapper, and the sidebar narrows to
  250px between 860px and 1200px.
- **List page type** — a data table with client-side sorting (any column,
  including commit count and last-updated time), free-text search, status
  filters and color-coded status badges, plus a live match count.
- **Diagram rendering + lightbox** — ` ```mermaid ` fences are drawn as inline
  SVG by a built-in, dependency-free renderer (flowcharts and sequence
  diagrams; unsupported syntax falls back to the source block), and clicking a
  diagram opens a full-viewport lightbox with zoom-to-fit and +/− controls.
- **Theme + i18n** — a persisted light/dark switch (dark by default) and an
  EN/中 toggle that re-labels every piece of UI chrome, nav entries, list
  controls and lightbox buttons in place, keeping `<html lang>` in sync.

## Usage

```bash
python3 skills/docs-site/scripts/docs_site.py generate \
  --config site.json --content ./docs --out ./out
python3 skills/docs-site/scripts/docs_site.py check --out ./out
```

## Config

```json
{
  "title": "My Docs",
  "tagline": "Short one-liner",
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

`breakpoint` is an integer pixel width; a non-numeric value fails generation
with a clear error. Config-derived text is escaped once for its destination
(HTML text, or JSON for inline scripts), and only one nav link is active even
when the landing page is also listed in `nav`.

See `templates/site-config.sample.json` and `references/design.md` for the full
reference.

## Pull-request list

The `list` page type is designed for rendering a pull-request table. Feed it
**real data** (from git history or the GitHub API), never hand-written
fixtures. Columns marked in `sortable` are click-to-reorder; the
`status_field` column renders as a badge; `filters` drive the status dropdown.

```json
[
  {"number": 8, "title": "feat(site): mobile navigation panel",
   "author": "Rain120", "commits": 5, "status": "merged",
   "last_updated": "2026-10-14 14:17:19",
   "url": "https://github.com/chaos-design/skills/pull/8"}
]
```

## Output

Generated files live under the `--out` directory, one `<slug>.html` per page,
self-contained (inline CSS/JS) and offline-capable.

## License

Apache-2.0. See [LICENSE](./LICENSE).
