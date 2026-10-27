# Docs Site

[中文](./README.zh-CN.md)

Generates a responsive, multi-page, self-contained static documentation site
from Markdown content plus a small JSON config. No build step, no external
runtime fetches — every page is an offline HTML file.

The layout is a dependency-free distillation of the ragx site work
(`chaos-design/ragx` PR #8): an 860px mobile breakpoint, a mobile top bar with
a full-screen navigation panel, fluid content width, a diagram lightbox that
zooms to the viewport, a light/dark theme switch, and an EN/中 toggle.

## Features

- **Automatic structure** — one self-contained HTML file per page, generated
  from your config.
- **Configurable navigation** — flat or grouped menus with active-state
  tracking, rendered as a desktop sidebar and a mobile full-screen panel.
- **Format integration** — Markdown (with optional front-matter) for doc
  pages, JSON data for list pages.
- **Responsive + multi-page** — desktop two-column grid, mobile top-bar layout,
  fluid content width that never overflows at narrow viewports.
- **List page type** — a data table with client-side sorting (any column,
  including commit count and last-updated time), free-text search, status
  filters and color-coded status badges, plus a live match count.
- **Diagram lightbox** — ` ```mermaid ` fences become figures that open in a
  full-viewport lightbox and zoom/pan to fit.
- **Theme + i18n** — persisted light/dark switch and EN/中 label toggle.

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
  "theme": "auto",
  "i18n": ["en", "zh"],
  "nav": [
    {"slug": "introduction", "label": "Introduction"},
    {"slug": "guides", "label": "Guides", "group": "Deep dive",
     "items": [{"slug": "quick-start", "label": "Quick start"}]}
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
   "url": "https://github.com/chaos-design/ragx/pull/8"}
]
```

## Output

Generated files live under the `--out` directory, one `<slug>.html` per page,
self-contained (inline CSS/JS) and offline-capable.

## License

Apache-2.0. See [LICENSE](./LICENSE).
