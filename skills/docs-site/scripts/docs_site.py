#!/usr/bin/env python3
"""docs_site.py — generate a responsive, multi-page static docs site.

Zero-dependency. The agent supplies content (Markdown) plus a small JSON
config; this script computes the HTML, navigation, themes, i18n and a
responsive, dependency-free layout:

- Pinned 300px sidebar + a content column that owns its own scroll, locked to
  one viewport so long docs never stretch the menu.
- Brand header at the top of the sidebar, scrollable nav in the middle, and a
  matched pair of GitHub / language controls pinned at the bottom.
- 860px mobile breakpoint: a fixed top bar (brand, GitHub, language pill and a
  three-bar toggle that morphs into a close cross) expands the sidebar into a
  full-width dropdown with its own scroll area and a dimming backdrop.
- EN/中 toggle switches every piece of UI chrome, persists to localStorage and
  keeps <html lang> in sync.
- Multi-page static output: one self-contained HTML file per page.
- Markdown integration with optional YAML front-matter.
- A "list" page type that renders a data table (e.g. pull requests) with
  client-side sorting (by any column, incl. commit count and last-updated),
  text filters and status badges.
- A light/dark theme switch; dark is the default palette.

Usage:
  python3 docs_site.py generate --config site.json --content ./docs --out ./out
  python3 docs_site.py check   --out ./out
"""

import argparse
import html
import json
import os
import re
import sys

DEFAULTS = {
    "title": "Documentation",
    "tagline": "",
    "description": "",
    "repo": "",
    "base_url": "",
    "theme": "dark",
    "lang": "zh",
    "i18n": ["zh", "en"],
    "nav": [],
    "pages": [],
    "breakpoint": 860,
    "brand_mark": "",
    "brand_sub": "Documentation",
    "brand_sub_zh": "文档中心",
}


def fail(msg):
    print("docs_site: error: " + msg, file=sys.stderr)
    raise SystemExit(2)


def read_config(path):
    if not os.path.isfile(path):
        fail("config not found: " + path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = dict(DEFAULTS)
    cfg.update(data)
    if not isinstance(cfg.get("pages"), list) or not cfg["pages"]:
        fail("config must define a non-empty 'pages' list")
    return cfg


def read_file(path):
    if not os.path.isfile(path):
        fail("missing file: " + path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def slug_filename(slug):
    """The on-disk filename for a page slug (kept in sync with render_page)."""
    return re.sub(r"[^a-z0-9-]", "-", slug.lower()) + ".html"


def page_slug(page):
    return page.get("slug") or re.sub(
        r"[^a-z0-9]+", "-", page.get("title", "page").lower()
    ).strip("-")


def repo_url(cfg):
    repo = str(cfg.get("repo", "")).strip()
    if not repo:
        return "#"
    if repo.startswith("http://") or repo.startswith("https://"):
        return repo
    return "https://" + repo


def brand_mark(cfg):
    mark = str(cfg.get("brand_mark", "")).strip()
    if mark:
        return mark[:2]
    return str(cfg.get("title", "D"))[:1].upper()


def js_literal(value):
    """JSON literal safe to embed inside an inline <script> block.

    json.dumps alone leaves `<`, `>` and `&` raw, so a config label containing
    `</script>` could break out of the script element.
    """
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def split_front_matter(text):
    """Return (meta_dict, body). Only supports a YAML-ish 'key: value' block."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            body = text[end + 4:]
            for line in block.splitlines():
                m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
                if m:
                    key = m.group(1).strip().lower()
                    val = m.group(2).strip().strip('"').strip("'")
                    meta[key] = val
            return meta, body
    return meta, text


def md_to_html(md):
    """Minimal, deterministic Markdown -> HTML. No external libs."""
    lines = md.splitlines()
    out = []
    in_code = False
    code_lang = ""
    code_buf = []
    in_list = None
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            in_table = False
            return
        head, rows = table_rows[0], table_rows[1:]
        html_out = ["<table class='doc-table'>"]
        html_out.append("<thead><tr>")
        for cell in head:
            html_out.append("<th>" + inline(md_cell(cell)) + "</th>")
        html_out.append("</tr></thead>")
        if len(table_rows) > 2:
            html_out.append("<tbody>")
            for r in rows:
                if r and all(c.strip() in ("", "-") for c in r):
                    continue
                html_out.append("<tr>")
                for cell in r:
                    html_out.append("<td>" + inline(md_cell(cell)) + "</td>")
                html_out.append("</tr>")
            html_out.append("</tbody>")
        html_out.append("</table>")
        out.append("\n".join(html_out))
        table_rows = []
        in_table = False

    def md_cell(c):
        return c.strip()

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_buf = []
            else:
                block = "<pre><code"
                if code_lang:
                    block += " class='language-" + html.escape(code_lang) + "'"
                block += ">" + html.escape("\n".join(code_buf)) + "</code></pre>"
                out.append(block)
                in_code = False
                code_lang = ""
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if "|" in stripped and stripped.startswith("|"):
            cells = [c for c in stripped.strip("|").split("|")]
            table_rows.append([c.strip() for c in cells])
            in_table = True
            i += 1
            continue
        if in_table:
            flush_table()

        if stripped.startswith("#"):
            lvl = len(stripped) - len(stripped.lstrip("#"))
            lvl = min(lvl, 6)
            text = stripped.lstrip("#").strip()
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append("<h%d id='%s' class='doc-h%d'>%s</h%d>" % (lvl, slug, lvl, inline(text), lvl))
            i += 1
            continue

        if stripped.startswith(">"):
            out.append("<blockquote>" + inline(stripped.lstrip("> ").strip()) + "</blockquote>")
            i += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            if in_list != "ul":
                if in_list == "ol":
                    out.append("</ol>")
                if in_list:
                    out.append("</ul>")
                in_list = "ul"
                out.append("<ul class='doc-list'>")
            out.append("<li>" + inline(re.sub(r"^[-*]\s+", "", stripped)) + "</li>")
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            if in_list != "ol":
                if in_list == "ul":
                    out.append("</ul>")
                if in_list:
                    out.append("</ol>")
                in_list = "ol"
                out.append("<ol class='doc-list'>")
            out.append("<li>" + inline(re.sub(r"^\d+\.\s+", "", stripped)) + "</li>")
            i += 1
            continue

        if in_list:
            if in_list == "ul":
                out.append("</ul>")
            else:
                out.append("</ol>")
            in_list = None

        if not stripped:
            i += 1
            continue

        out.append("<p>" + inline(stripped) + "</p>")
        i += 1

    if in_list:
        out.append("</" + in_list + ">")
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    if in_table:
        flush_table()
    return "\n".join(out)


def build_figure_block(md):
    """If markdown contains fenced mermaid or an svg placeholder, wrap for lightbox."""
    m = re.search(r"```mermaid\n(.*?)```", md, re.DOTALL)
    if m:
        diagram = html.escape(m.group(1))
        return (
            "<figure class='doc-figure' data-lightbox='true' tabindex='0'>"
            "<pre class='mermaid-src'><code class='language-mermaid'>" + diagram + "</code></pre>"
            "<figcaption data-i18n='diagramZoom'>Diagram — click to enlarge</figcaption></figure>"
        )
    return ""


def build_nav_html(cfg, active_slug):
    """Render the grouped navigation. Links point at real sibling pages and
    carry data-i18n keys so the language toggle can re-label them in place."""
    items = []
    for idx, nav in enumerate(cfg.get("nav", [])):
        if "group" in nav:
            label = nav.get("label", nav["group"])
            items.append(
                '<div class="nav-group"><div class="nav-group-label" data-i18n="group.%d">%s</div>'
                % (idx, html.escape(label))
            )
            for child in nav.get("items", []):
                slug = child.get("slug", "")
                act = " is-active" if slug == active_slug else ""
                items.append(
                    '<a class="nav-link%s" href="%s" data-i18n="nav.%s">%s</a>'
                    % (act, slug_filename(slug), html.escape(slug), html.escape(child.get("label", slug)))
                )
            items.append("</div>")
        else:
            slug = nav.get("slug", "")
            act = " is-active" if slug == active_slug else ""
            items.append(
                '<a class="nav-link%s" href="%s" data-i18n="nav.%s">%s</a>'
                % (act, slug_filename(slug), html.escape(slug), html.escape(nav.get("label", slug)))
            )
    return "\n".join(items)


def status_badge(status):
    cls = "badge-" + status
    return "<span class='status-badge %s'>%s</span>" % (cls, html.escape(status))


def build_list_page(cfg_page):
    data = cfg_page.get("data", [])
    columns = cfg_page.get("columns", [])
    sortables = cfg_page.get("sortable", ["last_updated", "commits"])
    filters = cfg_page.get("filters", [])
    status_field = cfg_page.get("status_field", "status")

    th = []
    for c in columns:
        key = c.get("key", "")
        sortable = " data-sortable='true'" if key in sortables else ""
        th.append("<th%s>%s</th>" % (sortable, html.escape(c.get("label", key))))
    head = "<tr>" + "".join(th) + "</tr>"

    rows = []
    for rec in data:
        tds = []
        for c in columns:
            key = c.get("key", "")
            val = rec.get(key, "")
            if key == status_field:
                tds.append("<td>" + status_badge(str(val)) + "</td>")
            elif key in sortables:
                tds.append("<td data-value='%s'>%s</td>" % (html.escape(str(rec.get("_v_" + key, val))), html.escape(str(val))))
            else:
                link = c.get("link")
                if link and rec.get(link):
                    tds.append("<td><a href='%s'>%s</a></td>" % (html.escape(rec[link]), html.escape(str(val))))
                else:
                    tds.append("<td>%s</td>" % html.escape(str(val)))
        status_val = rec.get(status_field, "")
        rows.append("<tr data-status='%s' data-commits='%s' data-updated='%s'>" % (html.escape(str(status_val)), html.escape(str(rec.get("_v_commits", rec.get("commits", 0)))), html.escape(str(rec.get("_v_last_updated", rec.get("last_updated", ""))))) + "".join(tds) + "</tr>")

    filter_ui = []
    if filters:
        opts = "".join("<option value='%s'>%s</option>" % (html.escape(str(f)), html.escape(str(f))) for f in filters)
        filter_ui.append(
            "<label class='list-filter'><span data-i18n='filter'>Filter status</span> "
            "<select id='f-status' data-filter='status'><option value='' data-i18n='all'>All</option>%s</select></label>" % opts
        )
    search_ui = (
        "<label class='list-filter'><span data-i18n='search'>Search</span> "
        "<input id='f-search' type='search' data-i18n-ph='searchPh' placeholder='title / author' /></label>"
    )
    toolbar = ("<div class='list-toolbar'>" + search_ui + "".join(filter_ui)
               + "<div class='list-count'></div></div>")

    table = "<div class='list-scroll'><table class='doc-table list-table'><thead>%s</thead><tbody>%s</tbody></table></div>" % (head, "\n".join(rows))
    return toolbar + table


def prep_record(rec, sortables):
    for s in sortables:
        rec["_v_" + s] = str(rec.get(s, ""))
    return rec


def build_i18n_map(cfg, page):
    """Build the flat zh/en string tables used by the client-side toggle."""
    strings = {
        "zh": {
            "brandSub": cfg.get("brand_sub_zh", "文档中心"),
            "navigate": "导航",
            "home": "首页",
            "langShort": "EN",
            "langLabel": cfg.get("lang_label_zh", "English"),
            "langTitle": cfg.get("lang_title_zh", "切换到 English"),
            "navOpen": "打开导航菜单",
            "navClose": "关闭导航菜单",
            "github": "GitHub",
            "theme": "切换主题",
            "filter": "状态筛选",
            "search": "搜索",
            "searchPh": cfg.get("search_placeholder_zh", "标题 / 作者"),
            "all": "全部",
            "results": "条结果",
            "fit": cfg.get("fit_zh", "适应屏幕"),
            "zoomIn": "放大",
            "zoomOut": "缩小",
            "close": cfg.get("close_zh", "关闭"),
            "diagram": "图表",
            "diagramZoom": "图表 — 点击放大",
        },
        "en": {
            "brandSub": cfg.get("brand_sub", "Documentation"),
            "navigate": "Navigate",
            "home": "Home",
            "langShort": "中",
            "langLabel": cfg.get("lang_label", "中文"),
            "langTitle": cfg.get("lang_title", "Switch to 中文"),
            "navOpen": "Open navigation menu",
            "navClose": "Close navigation menu",
            "github": "GitHub",
            "theme": "Toggle theme",
            "filter": "Filter status",
            "search": "Search",
            "searchPh": cfg.get("search_placeholder", "title / author"),
            "all": "All",
            "results": "results",
            "fit": cfg.get("fit", "Fit to screen"),
            "zoomIn": "Zoom in",
            "zoomOut": "Zoom out",
            "close": cfg.get("close", "Close"),
            "diagram": "Diagram",
            "diagramZoom": "Diagram — click to enlarge",
        },
    }
    for idx, item in enumerate(cfg.get("nav", [])):
        if item.get("group"):
            key = "group.%d" % idx
            strings["zh"][key] = item.get("group_zh", item.get("label_zh", item.get("label", item["group"])))
            strings["en"][key] = item.get("label", item["group"])
        else:
            slug = item.get("slug", "")
            key = "nav." + slug
            strings["zh"][key] = item.get("label_zh", item.get("label", slug))
            strings["en"][key] = item.get("label", slug)
        for child in item.get("items", []):
            slug = child.get("slug", "")
            key = "nav." + slug
            strings["zh"][key] = child.get("label_zh", child.get("label", slug))
            strings["en"][key] = child.get("label", slug)
    return strings


GITHUB_ICON = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56'
    ' 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7'
    ' -1.05-.72.08-.71.08-.71 1.16.08 1.77 1.2 1.77 1.2 1.03 1.77 2.7 1.26 3.36.96'
    ' .1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.09'
    ' -.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18.92-.26 1.91-.39 2.89-.4'
    ' .98.02 1.97.15 2.89.4 2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05'
    ' .74.8 1.19 1.83 1.19 3.09 0 4.42-2.7 5.4-5.27 5.68.41.35.78 1.05.78 2.12'
    ' 0 1.53-.01 2.77-.01 3.15 0 .31.2.67.8.56A11.51 11.51 0 0 0 23.5 12'
    'C23.5 5.73 18.27.5 12 .5Z"/></svg>'
)

CSS = """
:root{
  --bg:#0c0d0e;--surface:#141618;--surface-2:#1b1e21;--surface-3:#24282c;
  --ink:#f3f0e9;--muted:#9da3a7;--faint:#696f73;--line:#34393d;
  --accent:#6f9dff;--cyan:#53d6e7;--green:#72d29b;--yellow:#f2c14e;
  --red:#ff4f40;--purple:#b893ff;
  --radius:8px;--sidebar-w:300px;--header-h:56px;--top-break:{bp}px;
  --display:"Avenir Next Condensed","DIN Condensed","Avenir Next",sans-serif;
  --body:"Avenir Next","Helvetica Neue","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  --mono:"SFMono-Regular",Menlo,Monaco,Consolas,monospace;
}
[data-theme='light']{
  --bg:#f6f7f9;--surface:#fff;--surface-2:#f2f4f7;--surface-3:#e8ebef;
  --ink:#141414;--muted:#667085;--faint:#98a2b3;--line:#d0d5dd;
  --accent:#0b5fff;--cyan:#0891b2;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink);
  font-family:var(--body);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
::selection{background:rgba(111,157,255,.3)}
*{scrollbar-width:thin;scrollbar-color:var(--line) transparent}
*::-webkit-scrollbar{width:10px;height:10px}
*::-webkit-scrollbar-thumb{background:var(--line);border-radius:8px;border:2px solid var(--bg)}
/* shell: one viewport, sidebar fixed, only the content column scrolls */
.shell{display:grid;grid-template-columns:var(--sidebar-w) minmax(0,1fr);
  grid-template-rows:minmax(0,1fr);height:100vh;min-height:0;overflow:hidden}
/* sidebar: pinned head, scrolling nav, pinned footer */
.sidebar{position:relative;height:100%;max-height:100vh;min-height:0;overflow:hidden;
  display:flex;flex-direction:column;border-right:1px solid var(--line);background:var(--surface)}
.sidebar-head{flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:20px 16px 14px;border-bottom:1px solid var(--line);background:var(--surface)}
.brand{display:flex;align-items:center;gap:10px;min-width:0;color:var(--ink);text-decoration:none}
.brand:hover{text-decoration:none}
.brand-mark{width:30px;height:30px;border-radius:7px;flex:0 0 auto;
  background:linear-gradient(135deg,var(--accent),var(--cyan));
  display:grid;place-items:center;color:#0c0d0e;font-family:var(--display);
  font-weight:800;font-size:16px;line-height:1}
.brand-text,.site-header-text{display:flex;flex-direction:column;min-width:0}
.brand-name{font-family:var(--display);font-weight:700;font-size:17px;letter-spacing:.3px;line-height:1.2}
.brand-sub{font-size:11px;color:var(--faint);margin-top:1px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.sidebar-scroll{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:16px}
.sidebar-github{flex:0 0 auto;display:flex;align-items:center;gap:8px;
  padding:12px 16px;border-top:1px solid var(--line);background:var(--surface-2)}
/* matched-pair controls pinned at the sidebar bottom */
.sidebar-github a,.sidebar-github .lang-toggle{flex:1 1 0;min-width:0;display:flex;
  align-items:center;justify-content:center;gap:8px;height:36px;padding:0 12px;
  border:1px solid var(--line);border-radius:var(--radius);background:var(--surface-3);
  color:var(--ink);font-family:inherit;font-size:13px;font-weight:500;line-height:1;
  text-decoration:none;white-space:nowrap;cursor:pointer;
  transition:color .15s ease,border-color .15s ease}
.sidebar-github a:hover,.sidebar-github .lang-toggle:hover{border-color:var(--accent);
  color:var(--ink);text-decoration:none}
.sidebar-github svg{width:16px;height:16px;flex:0 0 auto}
.sidebar-github .ext-arrow{color:var(--faint)}
.lang-toggle{border:1px solid var(--line);background:var(--surface-2);color:var(--muted);
  font-size:11.5px;font-weight:600;padding:4px 9px;border-radius:999px;cursor:pointer;
  flex:0 0 auto;transition:color .15s ease,border-color .15s ease}
.lang-toggle:hover{color:var(--ink);border-color:var(--accent)}
/* nav */
.nav-group{margin-top:14px}
.nav-group:first-child{margin-top:0}
.nav-group-label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--faint);padding:0 8px 6px}
.nav-link{display:block;padding:7px 10px;border-radius:7px;color:var(--muted);
  font-size:13.5px;line-height:1.35;border:1px solid transparent}
.nav-link:hover{background:var(--surface-2);color:var(--ink);text-decoration:none}
.nav-link.is-active{background:var(--surface-3);color:var(--ink);border-color:var(--line);font-weight:600}
/* mobile header + backdrop are hidden on desktop */
.site-header{display:none}
.nav-backdrop{display:none}
.icon-btn{width:36px;height:36px;border-radius:var(--radius);border:1px solid var(--line);
  background:var(--surface-3);display:inline-flex;align-items:center;justify-content:center;
  cursor:pointer;color:var(--muted);font-size:15px;flex:0 0 auto;
  transition:color .15s ease,border-color .15s ease}
.icon-btn:hover{color:var(--ink);border-color:var(--accent)}
.icon-btn:focus-visible,.lang-toggle:focus-visible,.nav-toggle:focus-visible,
.header-github:focus-visible,.nav-link:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* content: owns its scrollbar, spans the available column */
.content{height:100%;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:0 0 80px}
.content-inner{padding:clamp(20px,3vw,56px);padding-top:32px}
.crumb{font-family:var(--mono);font-size:12px;color:var(--faint);margin-bottom:10px}
.page-title{font-size:clamp(26px,4vw,40px);line-height:1.1;margin:4px 0 10px;font-weight:750}
.page-desc{color:var(--muted);line-height:1.7;max-width:72ch}
/* document body */
.doc-body{max-width:72ch;line-height:1.75;overflow-wrap:break-word;min-width:0}
.doc-body :not(pre)>code{overflow-wrap:anywhere;background:rgba(100,116,139,.15);
  padding:2px 5px;border-radius:5px;font-size:.9em;font-family:var(--mono)}
pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:10px;
  overflow-x:auto;font-size:13.5px;font-family:var(--mono)}
.doc-body pre{margin:14px 0}
pre code{background:none;padding:0;color:inherit}
.doc-h1,.doc-h2,.doc-h3,.doc-h4{line-height:1.25;margin:24px 0 8px}
.doc-h1{font-size:28px}.doc-h2{font-size:22px}.doc-h3{font-size:18px}.doc-h4{font-size:16px}
.doc-list{line-height:1.7;padding-left:22px}
blockquote{border-left:3px solid var(--accent);margin:12px 0;padding:6px 14px;
  background:rgba(111,157,255,.08);border-radius:0 8px 8px 0;color:var(--muted)}
/* tables */
.doc-table{border-collapse:collapse;width:100%;font-size:14px;margin:14px 0}
.doc-table th,.doc-table td{border:1px solid var(--line);padding:9px 12px;text-align:left}
.doc-table th{background:var(--surface-2);font-weight:600}
.list-scroll{overflow-x:auto}
.list-table th{cursor:pointer;user-select:none;white-space:nowrap}
.list-table th[data-sortable]::after{content:' ⇅';opacity:.4;font-size:11px}
.list-table th.sort-asc::after{content:' ↑';opacity:1;color:var(--accent)}
.list-table th.sort-desc::after{content:' ↓';opacity:1;color:var(--accent)}
/* list toolbar */
.list-toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0}
.list-filter{font-size:13px;color:var(--muted);display:flex;gap:6px;align-items:center}
.list-filter input,.list-filter select{padding:7px 10px;border:1px solid var(--line);
  border-radius:8px;background:var(--surface-2);color:var(--ink);font-size:13px;
  font-family:inherit}
.list-filter input{width:220px}
.list-count{font-size:13px;color:var(--muted);margin-left:auto}
/* status badges */
.status-badge{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;
  font-weight:600;line-height:1.4}
.badge-open{background:rgba(114,210,155,.15);color:var(--green)}
.badge-merged,.badge-approve,.badge-approved{background:rgba(184,147,255,.15);color:var(--purple)}
.badge-closed{background:rgba(100,116,139,.15);color:var(--muted)}
.badge-draft{background:rgba(242,193,78,.15);color:var(--yellow)}
.badge-in-review,.badge-changes-requested{background:rgba(83,214,231,.15);color:var(--cyan)}
.badge-default{background:rgba(100,116,139,.15);color:var(--muted)}
/* figure / lightbox */
.doc-figure{margin:16px 0;background:var(--surface);border:1px solid var(--line);
  border-radius:12px;padding:14px;cursor:zoom-in;position:relative;max-width:72ch}
.doc-figure .expand-mark{position:absolute;top:10px;right:10px;width:32px;height:32px;
  display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--muted);
  border:1px solid var(--line);border-radius:8px}
.doc-figure figcaption{color:var(--muted);font-size:12px;margin-top:8px}
.lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(6,7,8,.92);padding:clamp(12px,3vw,40px)}
.lightbox.is-open{display:flex;flex-direction:column}
.lightbox-head{display:flex;align-items:center;gap:10px;color:#e2e8f0;margin-bottom:10px}
.lightbox-head .lb-title{flex:1;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lightbox-stage{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;transform-origin:center}
.lightbox pre{max-width:100%;max-height:100%;margin:0;transform-origin:center}
.lightbox .lb-btn{width:40px;height:40px;border-radius:9px;border:1px solid rgba(255,255,255,.25);
  background:rgba(255,255,255,.08);color:#fff;cursor:pointer;font-size:15px}
/* ===== MOBILE (≤ breakpoint) ===== */
@media (max-width:{bp}px){
  .shell{display:block;height:100vh;height:100dvh;min-height:0;overflow:hidden;padding-top:var(--header-h)}
  .content{height:100%;min-height:0;overflow-y:auto;overscroll-behavior:contain}
  body.nav-open .content{overflow:hidden}
  .site-header{position:fixed;top:0;left:0;right:0;z-index:60;display:flex;align-items:center;
    gap:10px;height:var(--header-h);padding:0 16px;background:var(--surface);
    border-bottom:1px solid var(--line)}
  .site-header-brand{display:flex;align-items:center;gap:10px;min-width:0;color:var(--ink);text-decoration:none}
  .site-header-brand:hover{text-decoration:none}
  .site-header-text .brand-name,.site-header-text .brand-sub{line-height:1.2}
  .site-header-actions{display:flex;align-items:center;gap:8px;margin-left:auto}
  /* square, equal-sized controls in the top bar */
  .site-header .lang-toggle,.header-github,.nav-toggle{width:36px;height:36px;padding:0;
    border:1px solid var(--line);border-radius:var(--radius);background:var(--surface-3);
    color:var(--ink);font-size:13px;font-weight:700;display:grid;place-items:center;
    cursor:pointer;transition:border-color .15s ease}
  .site-header .lang-toggle:hover,.header-github:hover,.nav-toggle:hover{border-color:var(--accent)}
  .header-github{color:var(--cyan);text-decoration:none}
  .header-github:hover{text-decoration:none}
  .header-github svg{width:18px;height:18px}
  .nav-toggle-bars{display:grid;gap:4px;width:16px}
  .nav-toggle-bars i{display:block;height:2px;border-radius:2px;background:currentColor;
    transition:transform .15s ease,opacity .15s ease}
  .nav-toggle.is-open .nav-toggle-bars i:nth-child(1){transform:translateY(6px) rotate(45deg)}
  .nav-toggle.is-open .nav-toggle-bars i:nth-child(2){opacity:0}
  .nav-toggle.is-open .nav-toggle-bars i:nth-child(3){transform:translateY(-6px) rotate(-45deg)}
  /* Only rendered while the panel is open — never dim a closed page. */
  body.nav-open .nav-backdrop{display:block;position:fixed;inset:var(--header-h) 0 0 0;
    z-index:54;background:rgba(0,0,0,.45)}
  body.nav-open{overflow:hidden}
  .sidebar{position:fixed;top:var(--header-h);left:0;right:0;bottom:0;height:auto;z-index:55;
    display:none;flex-direction:column;overflow:hidden;border-right:none;border-bottom:none;
    background:var(--surface)}
  body.nav-open .sidebar{display:flex;box-shadow:0 -12px 40px rgba(0,0,0,.45);
    animation:nav-slide .18s ease}
  .sidebar:focus{outline:none}
  .sidebar:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  @keyframes nav-slide{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:translateY(0)}}
  .sidebar-scroll{padding:12px}
  .sidebar-head,.sidebar-github{display:none}
  .content-inner{padding:24px 20px calc(24px + env(safe-area-inset-bottom))}
  .doc-body{max-width:none}
}
@media (max-width:600px){
  .list-filter input{width:100%}
  .list-toolbar{align-items:stretch}
  .list-filter{flex:1 1 100%}
  .list-count{margin-left:0}
}
@media (prefers-reduced-motion:reduce){
  *{animation-duration:.01ms!important;transition-duration:.01ms!important}
}
"""

LIST_JS = """
(function(){
  var table=document.querySelector('.list-table');
  if(!table)return;
  var headCells=table.querySelectorAll('th');
  var bodyRows=Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
  function rowVals(r){var tds=r.querySelectorAll('td');return Array.prototype.map.call(tds,function(td){
      return {td:td,i:td.cellIndex,raw:td.dataset.value!==undefined?td.dataset.value:td.textContent,
        value:td.dataset.value!==undefined?td.dataset.value:td.textContent};});}
  var sortKey=-1,sortDir='desc';
  headCells.forEach(function(th,idx){
    if(!th.hasAttribute('data-sortable'))return;
    th.addEventListener('click',function(){
      var dir=(sortKey===idx)?(sortDir==='asc'?'desc':'asc'):'desc';
      sortKey=idx;sortDir=dir;applySort();
    });
  });
  function applySort(){
    if(sortKey<0)return;
    bodyRows.forEach(function(r){var tds=r.querySelectorAll('td');
      if(tds[sortKey]&&tds[sortKey].dataset.value===undefined)tds[sortKey].dataset.value=tds[sortKey].textContent;});
    bodyRows.sort(function(a,b){
      var av=rowVals(a)[sortKey],bv=rowVals(b)[sortKey];
      if(!av||!bv)return 0;
      var an=parseFloat(av.raw),bn=parseFloat(bv.raw);
      var cmp=(!isNaN(an)&&!isNaN(bn))?an-bn:av.value.localeCompare(bv.value);
      return cmp*(sortDir==='asc'?1:-1);
    });
    var tb=table.tBodies[0];bodyRows.forEach(function(r){tb.appendChild(r);});
    headCells.forEach(function(th){th.classList.remove('sort-asc','sort-desc');});
    headCells[sortKey].classList.add(sortDir==='asc'?'sort-asc':'sort-desc');
    updateCount();
  }
  var search=document.getElementById('f-search');
  var statusF=document.getElementById('f-status');
  function updateCount(){
    var n=0;bodyRows.forEach(function(r){if(!r.hidden)n++;});
    var c=document.querySelector('.list-count');
    if(c&&window.docsT)c.textContent=n+' / '+bodyRows.length+' '+window.docsT('results');
  }
  function applyFilters(){
    var q=(search?search.value:'').toLowerCase();
    var st=statusF?statusF.value:'';
    bodyRows.forEach(function(r){
      var ok=true;
      if(st&&r.getAttribute('data-status')!==st)ok=false;
      if(q&&r.textContent.toLowerCase().indexOf(q)===-1)ok=false;
      r.hidden=!ok;
    });
    updateCount();
  }
  if(search)search.addEventListener('input',applyFilters);
  if(statusF)statusF.addEventListener('change',applyFilters);
  document.addEventListener('docs:lang',updateCount);
  applySort();
  updateCount();
})();
"""

I18N_JS = """
(function(){
  var I={i18n};
  var langs={langs};
  var lang={lang};
  var KEY='docs-site-lang';
  try{var saved=localStorage.getItem(KEY);if(saved&&I[saved])lang=saved;}catch(e){}
  function t(k){return (I[lang]&&I[lang][k]!==undefined)?I[lang][k]:k;}
  function apply(){
    document.documentElement.lang=(lang==='zh')?'zh-CN':'en';
    document.querySelectorAll('[data-i18n]').forEach(function(el){
      var v=t(el.getAttribute('data-i18n'));if(v!==undefined)el.textContent=v;});
    document.querySelectorAll('[data-i18n-title]').forEach(function(el){
      var v=t(el.getAttribute('data-i18n-title'));
      if(v!==undefined){el.setAttribute('title',v);el.setAttribute('aria-label',v);}});
    document.querySelectorAll('[data-i18n-ph]').forEach(function(el){
      var v=t(el.getAttribute('data-i18n-ph'));if(v!==undefined)el.setAttribute('placeholder',v);});
    document.querySelectorAll('[data-lang-toggle]').forEach(function(b){
      b.setAttribute('title',t('langTitle'));b.setAttribute('aria-label',t('langTitle'));});
    var tgl=document.querySelector('.nav-toggle');
    if(tgl)tgl.setAttribute('aria-label',t(document.body.classList.contains('nav-open')?'navClose':'navOpen'));
    if(typeof CustomEvent==='function')document.dispatchEvent(new CustomEvent('docs:lang'));
  }
  function setLang(next){
    if(!I[next])return;
    lang=next;
    try{localStorage.setItem(KEY,next);}catch(e){}
    apply();
  }
  document.querySelectorAll('[data-lang-toggle]').forEach(function(b){
    b.addEventListener('click',function(){var i=langs.indexOf(lang);setLang(langs[(i+1)%langs.length]);});
  });
  window.docsT=t;window.docsLang=function(){return lang;};
  apply();
})();
"""

THEME_JS = """
(function(){
  var root=document.documentElement;
  var mode={theme};
  try{mode=localStorage.getItem('docs-theme')||mode;}catch(e){}
  function apply(m){root.setAttribute('data-theme',m);}
  if(mode==='auto')apply(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  else apply(mode==='light'?'light':'dark');
  document.querySelectorAll('[data-theme-toggle]').forEach(function(b){
    b.addEventListener('click',function(){
      var next=root.getAttribute('data-theme')==='dark'?'light':'dark';
      apply(next);
      try{localStorage.setItem('docs-theme',next);}catch(e){}
    });
  });
})();
"""

NAV_JS = """
(function(){
  var shell=document.querySelector('.shell');
  var toggle=document.querySelector('.nav-toggle');
  var sidebar=document.getElementById('site-nav');
  var backdrop=document.querySelector('.nav-backdrop');
  if(!shell||!toggle||!sidebar)return;
  function setOpen(open,restoreFocus){
    shell.setAttribute('data-nav-open',open?'true':'false');
    document.body.classList.toggle('nav-open',open);
    toggle.classList.toggle('is-open',open);
    toggle.setAttribute('aria-expanded',open?'true':'false');
    if(window.docsT)toggle.setAttribute('aria-label',window.docsT(open?'navClose':'navOpen'));
    if(open){
      sidebar.focus();
      var active=sidebar.querySelector('.nav-link.is-active');
      if(active&&active.scrollIntoView)active.scrollIntoView({block:'nearest',behavior:'smooth'});
    }else if(restoreFocus){toggle.focus();}
  }
  toggle.addEventListener('click',function(){setOpen(!document.body.classList.contains('nav-open'));});
  if(backdrop)backdrop.addEventListener('click',function(){setOpen(false,true);});
  sidebar.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){setOpen(false);});});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'&&document.body.classList.contains('nav-open')){
      e.preventDefault();setOpen(false,true);}});
  var mq=window.matchMedia('(max-width:{bp}px)');
  function sync(){if(!mq.matches)setOpen(false);}
  if(mq.addEventListener)mq.addEventListener('change',sync);
  else if(mq.addListener)mq.addListener(sync);
})();
"""

LIGHTBOX_JS = """
(function(){
  var lb=document.querySelector('.lightbox');
  if(!lb)return;
  var stage=lb.querySelector('.lightbox-stage');
  var cur=1;
  function fit(){var pre=stage.querySelector('pre');if(!pre)return;pre.style.transform='scale('+cur+')';}
  function open(fig){lb.classList.add('is-open');cur=1;fit();document.body.style.overflow='hidden';}
  function closeLb(){lb.classList.remove('is-open');document.body.style.overflow='';}
  document.querySelectorAll('.doc-figure[data-lightbox]').forEach(function(f){
    f.addEventListener('click',function(){open(f);});
    f.addEventListener('keydown',function(e){if(e.key==='Enter')open(f);});
  });
  lb.querySelectorAll('[data-lb-close]').forEach(function(b){b.addEventListener('click',closeLb);});
  lb.querySelectorAll('[data-lb-fit]').forEach(function(b){b.addEventListener('click',function(){cur=1;fit();});});
  lb.querySelectorAll('[data-lb-plus]').forEach(function(b){b.addEventListener('click',function(){cur=Math.min(4,cur+0.25);fit();});});
  lb.querySelectorAll('[data-lb-minus]').forEach(function(b){b.addEventListener('click',function(){cur=Math.max(0.4,cur-0.25);fit();});});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&lb.classList.contains('is-open'))closeLb();});
  window.addEventListener('resize',fit);
})();
"""


def lightbox_html(page):
    if "data-lightbox" in page.get("body_html", ""):
        return (
            "<div class='lightbox' role='dialog' aria-modal='true' data-i18n-title='diagramZoom'>"
            "<div class='lightbox-head'><div class='lb-title' data-i18n='diagram'>Diagram</div>"
            "<button class='lb-btn' data-lb-fit data-i18n-title='fit' title='Fit'>⛶</button>"
            "<button class='lb-btn' data-lb-plus data-i18n-title='zoomIn' title='Zoom in'>+</button>"
            "<button class='lb-btn' data-lb-minus data-i18n-title='zoomOut' title='Zoom out'>−</button>"
            "<button class='lb-btn' data-lb-close data-i18n-title='close' aria-label='Close'>✕</button></div>"
            "<div class='lightbox-stage'></div></div>"
        )
    return ""


def move_figure_into_lightbox(page_body_html):
    """Re-stage the figure's pre into the lightbox so zooming shows it fullscreen."""
    m = re.search(r"<pre class='mermaid-src'>.*?</pre>", page_body_html, re.DOTALL)
    if m:
        return m.group(0)
    return ""


def render_page(cfg, page, out_dir, slug):
    try:
        bp = str(int(cfg.get("breakpoint", 860)))
    except (TypeError, ValueError):
        fail("'breakpoint' must be an integer")
    strings = build_i18n_map(cfg, page)
    initial = strings.get(cfg.get("lang", "zh"), strings["zh"])
    is_list = page.get("type") == "list"
    body_html = page.get("body_html", "")

    if is_list:
        for rec in page.get("data", []):
            prep_record(rec, page.get("sortable", ["last_updated", "commits"]))
        body_html = build_list_page(page)
    else:
        fig = build_figure_block(page.get("source_md", ""))
        if fig:
            body_html = fig + body_html

    lightbox = lightbox_html({"body_html": body_html, "type": page.get("type")})
    if lightbox:
        stage_content = move_figure_into_lightbox(body_html)
        lightbox = lightbox.replace(
            "<div class='lightbox-stage'></div>",
            "<div class='lightbox-stage'>" + stage_content + "</div>",
        )

    nav_html = build_nav_html(cfg, slug)
    home_file = cfg.get("_home_file", "index.html")
    # When the landing page is also a nav entry, that entry owns the active
    # state — marking the synthetic Home link too would leave two active links.
    nav_slugs = set()
    for item in cfg.get("nav", []):
        if item.get("slug"):
            nav_slugs.add(item["slug"])
        for child in item.get("items", []):
            if child.get("slug"):
                nav_slugs.add(child["slug"])
    home_active = " is-active" if (slug_filename(slug) == home_file and slug not in nav_slugs) else ""
    css = CSS.replace("{bp}", bp)
    theme = cfg.get("theme", "dark")
    theme_js = THEME_JS.replace("{theme}", js_literal(theme))
    nav_js = NAV_JS.replace("{bp}", bp)
    langs = [x for x in cfg.get("i18n", ["zh", "en"]) if x in strings] or ["zh", "en"]
    initial_lang = cfg.get("lang", "zh")
    if initial_lang not in strings:
        initial_lang = langs[0]
    i18n_js = (
        I18N_JS.replace("{i18n}", js_literal(strings))
        .replace("{langs}", js_literal(langs))
        .replace("{lang}", js_literal(initial_lang))
    )

    title = page.get("title", cfg.get("title", "Page"))
    desc = page.get("description", page.get("tagline", cfg.get("description", "")))
    brand = html.escape(cfg.get("title", "Docs"))
    brand_sub = html.escape(initial["brandSub"])
    repo_link = html.escape(repo_url(cfg))
    mark = html.escape(brand_mark(cfg))

    html_doc = """<!doctype html>
<html lang="{lang}" data-theme="{theme}">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<meta name="description" content="{meta_desc}"/>
<title>{title} · {site}</title>
<style>{css}</style>
</head>
<body>
<header class="site-header">
  <a class="site-header-brand" href="./{home}">
    <span class="brand-mark">{mark}</span>
    <span class="site-header-text">
      <span class="brand-name">{brand}</span>
      <span class="brand-sub" data-i18n="brandSub">{brand_sub}</span>
    </span>
  </a>
  <div class="site-header-actions">
    <a class="header-github" href="{repo_url}" target="_blank" rel="noreferrer" data-i18n-title="github" aria-label="GitHub">{github_icon}</a>
    <button type="button" class="lang-toggle" data-lang-toggle data-i18n="langShort">{lang_short}</button>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="site-nav" data-i18n-title="navOpen"><span class="nav-toggle-bars" aria-hidden="true"><i></i><i></i><i></i></span></button>
  </div>
</header>
<div class="shell" data-nav-open="false">
  <aside class="sidebar" id="site-nav" tabindex="-1">
    <div class="sidebar-head">
      <a class="brand" href="./{home}">
        <span class="brand-mark">{mark}</span>
        <span class="brand-text">
          <span class="brand-name">{brand}</span>
          <span class="brand-sub" data-i18n="brandSub">{brand_sub}</span>
        </span>
      </a>
      <button type="button" class="icon-btn" data-theme-toggle data-i18n-title="theme" aria-label="Toggle theme">◐</button>
    </div>
    <div class="sidebar-scroll">
      <div class="nav-group">
        <div class="nav-group-label" data-i18n="navigate">{nav_label}</div>
        <a class="nav-link{home_active}" href="./{home}" data-i18n="home">{home_label}</a>
      </div>
      {nav}
    </div>
    <div class="sidebar-github">
      <a href="{repo_url}" target="_blank" rel="noreferrer">{github_icon}<span>GitHub</span><span class="ext-arrow">↗</span></a>
      <button type="button" class="lang-toggle" data-lang-toggle data-i18n="langLabel">{lang_label}</button>
    </div>
  </aside>
  <div class="nav-backdrop" aria-hidden="true"></div>
  <main class="content">
    <div class="content-inner">
      <div class="crumb">{crumb}</div>
      <h1 class="page-title">{title}</h1>
      <p class="page-desc">{desc}</p>
      {body}
      {lightbox}
    </div>
  </main>
</div>
<script>{i18n_js}</script>
<script>{theme_js}</script>
<script>{nav_js}</script>
<script>{lb_js}</script>
<script>{list_js}</script>
</body>
</html>
""".format(
        lang=html.escape(cfg.get("lang", "zh")),
        theme=html.escape(cfg.get("theme", "dark")),
        meta_desc=html.escape(desc),
        title=html.escape(title),
        site=brand,
        css=css,
        home=html.escape(home_file),
        mark=mark,
        brand=brand,
        brand_sub=brand_sub,
        repo_url=repo_link,
        github_icon=GITHUB_ICON,
        lang_short=html.escape(initial["langShort"]),
        lang_label=html.escape(initial["langLabel"]),
        nav_label=html.escape(initial["navigate"]),
        home_label=html.escape(initial["home"]),
        home_active=home_active,
        nav=nav_html,
        crumb=html.escape(str(cfg.get("title", "Docs")) + " / " + title),
        desc=html.escape(desc),
        body=body_html,
        lightbox=lightbox,
        i18n_js=i18n_js,
        theme_js=theme_js,
        nav_js=nav_js,
        lb_js=LIGHTBOX_JS,
        list_js=(LIST_JS if is_list else ""),
    )

    safe_slug = re.sub(r"[^a-z0-9-]", "-", slug.lower())
    path = os.path.join(out_dir, safe_slug + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return path


def cmd_generate(args):
    cfg = read_config(args.config)
    content_dir = args.content or "."
    out_dir = args.out or "docs-site-out"
    os.makedirs(out_dir, exist_ok=True)
    cfg["_home_file"] = slug_filename(page_slug(cfg["pages"][0]))

    written = []
    for page in cfg["pages"]:
        slug = page_slug(page)
        page["slug"] = slug
        if page.get("type") == "list":
            page["body_html"] = ""
            if page.get("source_data"):
                base = os.path.join(content_dir, page["source_data"])
                page["data"] = json.loads(read_file(base))
        else:
            md_path = page.get("source")
            if not md_path:
                fail("page '" + slug + "' has no 'source' markdown file")
            raw = read_file(os.path.join(content_dir, md_path))
            meta, body_md = split_front_matter(raw)
            if meta.get("title"):
                page["title"] = meta["title"]
            if meta.get("description"):
                page["description"] = meta["description"]
            if meta.get("tagline"):
                page["tagline"] = meta["tagline"]
            page["source_md"] = raw
            page["body_html"] = md_to_html(body_md)
        written.append(render_page(cfg, page, out_dir, slug))
    print("Generated " + str(len(written)) + " pages into " + out_dir)
    for p in written:
        print("  " + p)


def cmd_check(args):
    out_dir = args.out or "docs-site-out"
    if not os.path.isdir(out_dir):
        fail("output dir not found: " + out_dir)
    files = sorted(f for f in os.listdir(out_dir) if f.endswith(".html"))
    print("Found " + str(len(files)) + " HTML page(s) in " + out_dir)
    problems = []
    for f in files:
        text = read_file(os.path.join(out_dir, f))
        checks = {
            "doctype": text.startswith("<!doctype html>"),
            "responsive-breakpoint": "max-width:" in text,
            "mobile-header": "site-header" in text and "nav-toggle-bars" in text,
            "nav-panel": "nav-backdrop" in text and 'id="site-nav"' in text,
            "lang-toggle": "data-lang-toggle" in text and "data-i18n" in text,
            "theme-switch": "data-theme-toggle" in text,
            "pinned-layout": "grid-template-columns:var(--sidebar-w)" in text,
        }
        if "list-table'" in text and "<table class='doc-table list-table'>" in text:
            checks["list-sortable"] = "data-sortable" in text
            checks["status-badge"] = "status-badge" in text
            checks["list-filter"] = "f-status" in text or "f-search" in text
        for k, v in checks.items():
            if not v:
                problems.append("%s: missing %s" % (f, k))
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  - " + p)
        raise SystemExit(1)
    print("All structural checks passed.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a responsive multi-page docs site.")
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--config", required=True)
    g.add_argument("--content")
    g.add_argument("--out")
    g.set_defaults(func=cmd_generate)
    c = sub.add_parser("check")
    c.add_argument("--out")
    c.set_defaults(func=cmd_check)
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_help()
        raise SystemExit(1)
    args.func(args)


if __name__ == "__main__":
    main()
