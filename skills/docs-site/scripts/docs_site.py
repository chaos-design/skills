#!/usr/bin/env python3
"""docs_site.py — generate a responsive, multi-page static docs site.

Zero-dependency. The agent supplies content (Markdown) plus a small JSON
config; this script computes the HTML, navigation, themes, i18n and a
responsive, dependency-free layout:

- 860px mobile breakpoint with a full-screen navigation panel.
- Fluid content width that follows the viewport.
- Multi-page static output: one self-contained HTML file per page.
- Markdown integration with optional YAML front-matter.
- A "list" page type that renders a data table (e.g. pull requests) with
  client-side sorting (by any column, incl. commit count and last-updated),
  text filters and status badges.
- A light/dark theme switch and an EN/中 language toggle.

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
    "theme": "auto",
    "lang": "en",
    "i18n": ["en", "zh"],
    "nav": [],
    "pages": [],
    "breakpoint": 860,
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
        sep = table_rows and len(table_rows) > 1
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

        # table detection
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
            "<figcaption>Diagram — click to enlarge</figcaption></figure>"
        )
    return ""


def build_nav_html(cfg, active_slug, i18n):
    items = []
    for nav in cfg.get("nav", []):
        if "group" in nav:
            items.append('<div class="nav-group"><div class="nav-group-label">%s</div>' % html.escape(nav.get("label", nav["group"])))
            for child in nav.get("items", []):
                act = " is-active" if child.get("slug") == active_slug else ""
                items.append('<a class="nav-link%s" href="#%s">%s</a>' % (act, child.get("slug", ""), html.escape(child.get("label", ""))))
            items.append("</div>")
        else:
            act = " is-active" if nav.get("slug") == active_slug else ""
            label = nav.get("label", nav.get("slug", ""))
            t = i18n.get("nav." + nav.get("slug", ""), label)
            items.append('<a class="nav-link%s" href="#%s">%s</a>' % (act, nav.get("slug", ""), html.escape(t)))
    return "\n".join(items)


def status_badge(status):
    cls = "badge-" + status
    return "<span class='status-badge %s'>%s</span>" % (cls, html.escape(status))


def build_list_page(cfg_page, i18n):
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
            "<label class='list-filter'>Filter status: "
            "<select id='f-status' data-filter='status'><option value=''>All</option>%s</select></label>" % opts
        )
    search_ui = (
        "<label class='list-filter'>Search "
        "<input id='f-search' type='search' placeholder='title / author' /></label>"
    )
    toolbar = ("<div class='list-toolbar'>" + search_ui + "".join(filter_ui) + "</div>")

    table = "<div class='list-scroll'><table class='doc-table list-table'><thead>%s</thead><tbody>%s</tbody></table></div>" % (head, "\n".join(rows))
    return toolbar + table


def prep_record(rec, sortables):
    for s in sortables:
        rec["_v_" + s] = str(rec.get(s, ""))
    return rec


def language_strings(cfg, page):
    i18n = {}
    for item in cfg.get("nav", []):
        if item.get("slug") and item.get("label"):
            i18n["nav." + item["slug"]] = item.get("label_zh", item["label"])
    i18n["filter"] = page.get("filter_zh", "Filter status")
    i18n["search"] = page.get("search_zh", "Search")
    i18n["en"] = "EN"
    i18n["zh"] = "中"
    i18n["fit"] = page.get("fit_zh", "Fit to screen")
    i18n["close"] = page.get("close_zh", "Close")
    return i18n


CSS = """
:root{
  --bg:#f6f7f9;--card:#fff;--ink:#141414;--muted:#667085;--line:#d0d5dd;
  --accent:#0b5fff;--accent-2:#7a3cff;--radius:12px;
  --header-h:56px;--top-break:{bp}px;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
/* shell: two-col desktop */
.shell{display:grid;grid-template-columns:280px minmax(0,1fr);min-height:100dvh}
/* sidebar / header */
.sidebar{position:sticky;top:0;height:100dvh;border-right:1px solid var(--line);
  background:var(--card);display:flex;flex-direction:column;overflow:hidden}
.brand{position:relative}
.brand-row{display:flex;align-items:center;justify-content:space-between;gap:8px;
  min-height:var(--header-h);padding:12px 16px;border-bottom:1px solid var(--line)}
.brand a{font-weight:700;font-size:16px;color:var(--ink)}
.brand a:hover{text-decoration:none;color:var(--accent)}
.tagline{font-size:12px;color:var(--muted);padding:6px 16px}
.sidebar-scroll{flex:1;overflow-y:auto;padding:12px}
/* nav */
.nav-group{margin-bottom:14px}
.nav-group-label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;
  color:var(--muted);padding:4px 8px}
.nav-link{display:block;padding:8px 10px;border-radius:8px;color:var(--ink);font-size:14px}
.nav-link:hover{background:rgba(11,95,255,.08);text-decoration:none}
.nav-link.is-active{background:rgba(11,95,255,.12);color:var(--accent);font-weight:600}
/* top bar (mobile only, hidden desktop) */
.topbar{display:none}
.topbar-row{display:flex;align-items:center;justify-content:space-between;gap:8px;
  min-height:var(--header-h);padding:0 12px;background:var(--card);
  position:sticky;top:0;z-index:50;border-bottom:1px solid var(--line)}
.icon-btn{width:36px;height:36px;border-radius:9px;border:1px solid var(--line);
  background:var(--card);display:inline-flex;align-items:center;justify-content:center;
  cursor:pointer;color:var(--ink);font-size:15px}
.icon-btn:hover{border-color:var(--accent)}
.icon-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.nav-toggle{position:relative}
.nav-toggle span,.nav-toggle span::before,.nav-toggle span::after{content:'';
  display:block;width:18px;height:2px;background:currentColor;border-radius:2px;position:relative}
.nav-toggle span::before{position:absolute;top:-6px}
.nav-toggle span::after{position:absolute;top:6px}
/* content */
.content{min-width:0;padding:0}
.content-inner{padding:clamp(20px,3vw,56px)}
.page-title{font-size:clamp(26px,4vw,40px);line-height:1.1;margin:4px 0 10px;font-weight:750}
.page-desc{color:var(--muted);line-height:1.7;max-width:64ch}
/* doc body */
.doc-body{max-width:72ch;line-height:1.75;overflow-wrap:break-word;min-width:0}
.doc-body :not(pre)>code{overflow-wrap:anywhere;background:rgba(100,116,139,.12);
  padding:2px 5px;border-radius:5px;font-size:.9em}
pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:10px;overflow-x:auto;font-size:13.5px}
pre code{background:none;padding:0;color:inherit}
.doc-h1,.doc-h2,.doc-h3{line-height:1.25;margin:24px 0 8px}
.doc-h1{font-size:28px}.doc-h2{font-size:22px}.doc-h3{font-size:18px}
.doc-list{line-height:1.7;padding-left:22px}
blockquote{border-left:3px solid var(--accent);margin:12px 0;padding:6px 14px;
  background:rgba(11,95,255,.06);border-radius:0 8px 8px 0}
/* tables */
.doc-table{border-collapse:collapse;width:100%;font-size:14px;margin:14px 0}
.doc-table th,.doc-table td{border:1px solid var(--line);padding:9px 12px;text-align:left}
.doc-table th{background:rgba(100,116,139,.08);font-weight:600}
.list-scroll{overflow-x:auto}
.list-table th{cursor:pointer;user-select:none;white-space:nowrap}
.list-table th[data-sortable]::after{content:' ⇅';opacity:.4;font-size:11px}
.list-table th.sort-asc::after{content:' ↑';opacity:1;color:var(--accent)}
.list-table th.sort-desc::after{content:' ↓';opacity:1;color:var(--accent)}
/* list toolbar */
.list-toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0}
.list-filter{font-size:13px;color:var(--muted);display:flex;gap:6px;align-items:center}
.list-filter input,.list-filter select{padding:7px 10px;border:1px solid var(--line);
  border-radius:8px;background:var(--card);font-size:13px}
.list-filter input{width:220px}
.list-count{font-size:13px;color:var(--muted);margin-left:auto}
/* status badges */
.status-badge{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;
  font-weight:600;line-height:1.4}
.badge-open{background:rgba(22,163,74,.15);color:#15803d}
.badge-merged{background:rgba(109,40,217,.15);color:#6d28d9}
.badge-closed{background:rgba(100,116,139,.15);color:#475569}
.badge-draft{background:rgba(217,119,6,.15);color:#b45309}
.badge-in-review,.badge-changes-requested{background:rgba(234,179,8,.18);color:#854d0e}
.badge-merged,.badge-approve,.badge-approved{background:rgba(109,40,217,.15);color:#6d28d9}
.badge-default{background:rgba(100,116,139,.15);color:#475569}
/* figure / lightbox */
.doc-figure{margin:16px 0;background:var(--card);border:1px solid var(--line);
  border-radius:12px;padding:14px;cursor:zoom-in;position:relative}
.doc-figure .expand-mark{position:absolute;top:10px;right:10px;width:32px;height:32px;
  display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--muted);
  border:1px solid var(--line);border-radius:8px}
.doc-figure figcaption{color:var(--muted);font-size:12px;margin-top:8px}
.lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(15,23,42,.86);
  padding:clamp(12px,3vw,40px)}
.lightbox.is-open{display:flex;flex-direction:column}
.lightbox-head{display:flex;align-items:center;gap:10px;color:#e2e8f0;margin-bottom:10px}
.lightbox-head .lb-title{flex:1;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lightbox-stage{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;
  transform-origin:center}
.lightbox pre{max-width:100%;max-height:100%;margin:0;transform-origin:center}
.lightbox .lb-btn{width:40px;height:40px;border-radius:9px;border:1px solid rgba(255,255,255,.25);
  background:rgba(255,255,255,.08);color:#fff;cursor:pointer;font-size:15px}
/* footer */
.footer{border-top:1px solid var(--line);padding:18px 0;color:var(--muted);font-size:13px}
/* theme controls */
.theme-ctl,.lang-ctl{display:flex;gap:6px}
.theme-ctl button,.lang-ctl button{width:36px;height:30px;border-radius:8px;border:1px solid var(--line);
  background:var(--card);color:var(--ink);cursor:pointer;font-size:12px}
/* ===== MOBILE (≤ breakpoint) ===== */
@media (max-width:{bp}px){
  .shell{display:block}
  .sidebar{position:fixed;inset:0;top:var(--header-h);width:100%;height:calc(100dvh - var(--header-h));
    z-index:40;transform:translateY(-120%);transition:transform .18s ease;box-shadow:0 12px 30px rgba(0,0,0,.25)}
  body.nav-open .sidebar{transform:translateY(0)}
  .sidebar::after{content:'';position:fixed;inset:0;top:var(--header-h);background:rgba(15,23,42,.4);z-index:-1}
  .topbar{display:block}
  .topbar-row{position:sticky}
  .nav-toggle.is-open span{background:transparent}
  .nav-toggle.is-open span::before{top:0;transform:rotate(45deg)}
  .nav-toggle.is-open span::after{top:0;transform:rotate(-45deg)}
  .content-inner{padding:20px 16px calc(20px + env(safe-area-inset-bottom))}
}
/* dark theme */
[data-theme='dark']{--bg:#0b0d12;--card:#14171f;--ink:#e6e8ee;--muted:#9aa3b2;--line:#2a2f3a}
[data-theme='dark'] .list-table th{background:rgba(148,163,184,.1)}
"""


LIST_JS = """
(function(){
  var table=document.querySelector('.list-table');
  if(!table)return;
  var headCells=table.querySelectorAll('th');
  var bodyRows=Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
  function rowVals(r){var tds=r.querySelectorAll('td');return Array.prototype.map.call(tds,function(td,i){
      return {td:td,i:i,raw:td.dataset.value!==undefined?td.dataset.value:td.textContent,value:td.dataset.value!==undefined?td.dataset.value:td.textContent};});}
  var sortKey=-1,sortDir='desc';
  headCells.forEach(function(th,idx){
    if(!th.hasAttribute('data-sortable'))return;
    th.addEventListener('click',function(){
      var dir = (sortKey===idx)? (sortDir==='asc'?'desc':'asc') : 'desc';
      sortKey=idx;sortDir=dir;applySort();
    });
  });
  function applySort(){
    bodyRows.forEach(function(r){var tds=r.querySelectorAll('td');tds[sortKey].dataset.value=tds[sortKey].dataset.value||tds[sortKey].textContent;});
    var cols=rowCols();
    bodyRows.sort(function(a,b){
      var av=rowVals(a)[sortKey],bv=rowVals(b)[sortKey];
      var an=parseFloat(av.raw),bn=parseFloat(bv.raw);
      var cmp=(!isNaN(an)&&!isNaN(bn))?an-bn:(av.value.localeCompare(bv.value));
      return cmp*(sortDir==='asc'?1:-1);
    });
    var tb=table.tBodies[0];bodyRows.forEach(function(r){tb.appendChild(r);});
    headCells.forEach(function(th,i){th.classList.remove('sort-asc','sort-desc');});
    if(sortKey>=0)headCells[sortKey].classList.add(sortDir==='asc'?'sort-asc':'sort-desc');
    updateCount();
  }
  function rowCols(){return headCells.length;}
  var search=document.getElementById('f-search');
  var statusF=document.getElementById('f-status');
  function updateCount(){
    var n=0;bodyRows.forEach(function(r){if(!r.hidden)n++;});
    var c=document.querySelector('.list-count');if(c)c.textContent=n+' of '+bodyRows.length+' pull requests';
  }
  function applyFilters(){
    var q=(search?search.value:'').toLowerCase();
    var st=statusF?statusF.value:'';
    bodyRows.forEach(function(r){
      var ok=true;
      if(st&&r.getAttribute('data-status')!==st)ok=false;
      if(q){var hay=r.textContent.toLowerCase();if(hay.indexOf(q)===-1)ok=false;}
      r.hidden=!ok;
    });
    updateCount();
  }
  if(search)search.addEventListener('input',applyFilters);
  if(statusF)statusF.addEventListener('change',applyFilters);
  applySort();
  updateCount();
})();
"""


THEME_JS = """
(function(){
  var root=document.documentElement;
  var mode=localStorage.getItem('docs-theme')||'{theme}';
  function apply(m){root.setAttribute('data-theme',m);}
  if(mode==='auto'){apply(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}
  else{apply(mode);}
  var btns=document.querySelectorAll('[data-theme-toggle]');
  btns.forEach(function(b){b.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    var next=(cur==='dark')?'light':'dark';
    apply(next);localStorage.setItem('docs-theme',next);
  });});
})();
"""

NAV_JS = """
(function(){
  var toggle=document.querySelector('.nav-toggle');
  var body=document.body;
  if(!toggle)return;
  function close(){body.classList.remove('nav-open');toggle.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');}
  function open(){body.classList.add('nav-open');toggle.classList.add('is-open');toggle.setAttribute('aria-expanded','true');}
  toggle.addEventListener('click',function(){body.classList.contains('nav-open')?close():open();});
  document.querySelectorAll('.nav-link').forEach(function(a){
    a.addEventListener('click',function(){close();});
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&body.classList.contains('nav-open')){close();toggle.focus();}});
  var mq=window.matchMedia('screen and (max-width:{bp}px)');
  function sync(){if(!mq.matches)close();}
  if(mq.addEventListener)mq.addEventListener('change',sync);else mq.addListener(sync);
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
            "<div class='lightbox' role='dialog' aria-modal='true' aria-label='Diagram enlarged'>"
            "<div class='lightbox-head'><div class='lb-title'>Diagram</div>"
            "<button class='lb-btn' data-lb-fit title='Fit'>⛶</button>"
            "<button class='lb-btn' data-lb-plus title='Zoom in'>+</button>"
            "<button class='lb-btn' data-lb-minus title='Zoom out'>−</button>"
            "<button class='lb-btn' data-lb-close aria-label='Close'>✕</button></div>"
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
    bp = str(cfg.get("breakpoint", 860))
    i18n = language_strings(cfg, page)
    is_list = page.get("type") == "list"
    body_html = page.get("body_html", "")

    if is_list:
        for rec in page.get("data", []):
            prep_record(rec, page.get("sortable", ["last_updated", "commits"]))
        list_html = build_list_page(page, i18n)
        lb_stage_content = ""
        body_html = list_html
    else:
        fig = build_figure_block(page.get("source_md", ""))
        if fig:
            body_html = fig + body_html

    # inject figure into lightbox stage
    lightbox = lightbox_html({"body_html": body_html, "type": page.get("type")})
    if lightbox:
        stage_content = move_figure_into_lightbox(body_html)
        lightbox = lightbox.replace(
            "<div class='lightbox-stage'></div>",
            "<div class='lightbox-stage'>" + stage_content + "</div>",
        )

    nav_html = build_nav_html(cfg, slug, i18n)
    css = CSS.replace("{bp}", bp)
    theme_js = THEME_JS.replace("{theme}", cfg.get("theme", "auto"))
    nav_js = NAV_JS.replace("{bp}", bp)
    lb_js = LIGHTBOX_JS

    title = page.get("title", cfg.get("title", "Page"))
    desc = page.get("description", page.get("tagline", cfg.get("description", "")))

    html_doc = """<!doctype html>
<html lang="{lang}" data-theme="{theme}">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>{title} · {site}</title>
<style>{css}</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-row">
    <a class="brand-link" href="./{home}">{brand}</a>
    <div class="brand-meta">
      <div class="lang-ctl"><button data-i18n="lang">EN / 中</button></div>
      <button class="icon-btn nav-toggle" aria-expanded="false" aria-controls="site-nav" aria-label="Toggle navigation menu"><span></span></button>
    </div>
  </div>
</header>
<div class="shell">
  <aside class="sidebar" id="site-nav">
    <div class="brand"><div class="brand-row"><a href="./{home}">{brand}</a>
      <button class="icon-btn" data-theme-toggle aria-label="Toggle theme">◐</button></div></div>
    <div class="tagline">{tagline}</div>
    <div class="sidebar-scroll">{nav}</div>
    <div class="footer">{repo}</div>
  </aside>
  <main class="content">
    <div class="content-inner">
      <h1 class="page-title">{title}</h1>
      <p class="page-desc">{desc}</p>
      {count_html}{body}
      {lightbox}
    </div>
  </main>
</div>
<script>{theme_js}</script>
<script>{nav_js}</script>
<script>{lb_js}</script>
{list_js}
</body>
</html>
""".format(
        lang=cfg.get("lang", "en"),
        theme=cfg.get("theme", "auto"),
        title=html.escape(title),
        site=html.escape(cfg.get("title", "Docs")),
        css=css,
        home="index.html",
        brand=html.escape(cfg.get("title", "Docs")),
        tagline=html.escape(cfg.get("tagline", "")),
        nav=nav_html,
        repo=html.escape(cfg.get("repo", "")),
        desc=html.escape(desc),
        count_html=('<div class="list-count"></div>') if is_list else "",
        body=body_html,
        lightbox=lightbox,
        theme_js=theme_js,
        nav_js=nav_js,
        lb_js=lb_js,
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

    written = []
    for page in cfg["pages"]:
        slug = page.get("slug", page.get("title", "page").lower().replace(" ", "-"))
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
            page_meta = dict(page)
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
            "responsive-breakpoint": "max-width:860px" in text or "max-width:" in text,
            "mobile-topbar": "topbar" in text,
            "nav-panel": "nav-toggle" in text,
            "theme-switch": "data-theme-toggle" in text,
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
