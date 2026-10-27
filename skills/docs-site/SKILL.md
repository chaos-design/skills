---
name: docs-site
description: >
  Quickly creates a responsive, multi-page static documentation site from
  Markdown plus a small JSON config. Generates the documentation structure
  automatically, wires a configurable navigation menu, integrates existing
  Markdown / data formats, and adds a responsive layout, a light/dark theme
  switch, an EN/中 toggle and a data "list" page type with client-side
  sorting (commit count, last-updated), text filters and status badges.
  Invoke when the user asks to build a docs site, documentation page,
  multi-page help center, or to publish structured content as an offline,
  self-contained static site.
---

# Docs Site

Use this skill to turn Markdown content and a JSON config into a responsive,
multi-page, self-contained static documentation site. The output is a set of
offline HTML files that open as-is — no build step, no external runtime
fetches.

The layout follows the ragx site work (PR #8): an 860px mobile breakpoint,
a mobile top bar with a full-screen navigation panel, fluid content width,
a diagram lightbox that zooms to the viewport, a theme switch, and an EN/中
language toggle.

## What the skill does

- Generates the documentation structure from your config (one HTML per page).
- Configures the navigation menu (flat or grouped) with active-state tracking.
- Integrates existing formats: Markdown (with optional front-matter) for doc
  pages, JSON data for list pages.
- Produces a responsive layout with multi-page support.
- Adds a list page type that renders a data table with client-side sorting
  (e.g. commit count, last-updated time), text search, status filters and
  color-coded status badges.

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
  "theme": "auto",
  "i18n": ["en", "zh"],
  "nav": [
    {"slug": "introduction", "label": "Introduction"},
    {"slug": "pull-requests", "label": "Pull Requests"},
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

- `nav` entries with `group` render as a labeled section whose `items` are
  nested links. Entries without `group` are top-level links.
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

## Diagrams

A ` ```mermaid ` fence inside a doc page is rendered as a figure with a
click-to-enlarge lightbox that zooms/panns to fit the viewport.

## Output contract

Generated files live under the `--out` directory, one `<slug>.html` per page,
self-contained (inline CSS/JS), offline-capable. Page titles come from the
config or the Markdown front-matter `title`.

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
