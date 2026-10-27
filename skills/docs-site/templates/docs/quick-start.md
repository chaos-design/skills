# Quick start

Generate a site in one command:

```bash
python3 skills/docs-site/scripts/docs_site.py generate \
  --config site.json \
  --content ./docs \
  --out ./out
```

Then validate the output:

```bash
python3 skills/docs-site/scripts/docs_site.py check --out ./out
```

## Config fields

| Field | Purpose |
| --- | --- |
| `title` | Site name shown in the brand and title bar. |
| `nav` | Navigation menu; each entry has `slug`, `label`, optional `label_zh`, and `group`/`items` for grouped sections. |
| `pages` | One entry per page. `type` is `doc` (markdown) or `list` (data table). |
| `pages[].type: list` | Reads JSON data, defines `columns`, `sortable`, `status_field` and `filters`. |

## List pages

A list page sorts by any column marked in `sortable` (typically commit count
and last-updated time), supports a status filter and free-text search, and
renders `status_field` values as color-coded badges.
