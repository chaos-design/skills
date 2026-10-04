"""CSS for generated briefs.

Two themes share one variable system:

- `document` reads like an editorial memo: serif headings, flat panels.
- `blueprint` reads like an engineering sheet: squared panels, a ruled grid,
  monospaced uppercase panel heads and a title block.

Each theme works in light and dark mode, so every brief ships four looks without
any extra markup. No web fonts, no external requests.
"""
from __future__ import annotations

LIGHT = {
    "bg": "#f7f8fa",
    "panel": "#ffffff",
    "panel-2": "#f2f4f7",
    "ink": "#14181f",
    "muted": "#5b6675",
    "line": "#dfe3e8",
    "line-strong": "#bfc6d0",
    "accent": "#1d4ed8",
    "accent-soft": "#e8effd",
    "ok": "#127a45",
    "warn": "#8a5a06",
    "bad": "#b4232c",
    "code-bg": "#f4f6f8",
    "node": "#ffffff",
    "node-line": "#98a2b0",
    "grid-line": "#e9edf2",
}

DARK = {
    "bg": "#0e1319",
    "panel": "#151b23",
    "panel-2": "#1b222c",
    "ink": "#e6edf3",
    "muted": "#96a3b3",
    "line": "#26303d",
    "line-strong": "#3a4759",
    "accent": "#7aa9ff",
    "accent-soft": "#1b2740",
    "ok": "#4cc38a",
    "warn": "#d9a441",
    "bad": "#f87171",
    "code-bg": "#10161d",
    "node": "#1b222c",
    "node-line": "#415067",
    "grid-line": "#182029",
}

BASE = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Roboto,sans-serif;
  --serif:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Songti SC','Noto Serif CJK SC',serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;
  --radius:10px;
}
:root{__LIGHT__}
@media (prefers-color-scheme:dark){:root:not([data-mode='light']){__DARK__}}
:root[data-mode='dark']{__DARK__}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.62;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:underline;text-decoration-color:var(--line-strong);text-underline-offset:2px}
a:hover{text-decoration-color:var(--accent)}
code,kbd{font-family:var(--mono);font-size:.9em}
.doc{max-width:1180px;margin:0 auto;padding:30px 22px 76px}
.masthead{display:flex;gap:24px;align-items:flex-end;justify-content:space-between;
  flex-wrap:wrap;border-bottom:2px solid var(--line-strong);padding-bottom:16px;margin-bottom:20px}
.eyebrow{margin:0 0 6px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--muted);font-family:var(--mono)}
h1{margin:0;font-size:clamp(24px,3.4vw,34px);line-height:1.2;font-weight:700;letter-spacing:-.01em}
.masthead-text{min-width:0;flex:1 1 320px}
.subtitle{margin:8px 0 0;color:var(--muted);font-size:16px;max-width:70ch;overflow-wrap:anywhere}
.stamp{margin:10px 0 0;color:var(--muted);font-size:12px;font-family:var(--mono);overflow-wrap:anywhere}
.toolbar{display:flex;gap:8px;flex-wrap:wrap}
.toolbar button{font:inherit;font-size:12px;padding:6px 11px;border-radius:999px;
  border:1px solid var(--line-strong);background:var(--panel);color:var(--ink);cursor:pointer}
.toolbar button:hover{border-color:var(--accent);color:var(--accent)}
.toolbar button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.panels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;align-items:start}
.panel{min-width:0;background:var(--panel);border:1px solid var(--line);
  border-radius:var(--radius);padding:16px 18px 18px;overflow-wrap:break-word}
.panel.span-2{grid-column:1/-1}
.panel-head{margin:0 0 12px;font-size:19px;line-height:1.3;font-weight:700}
.panel-body>:first-child{margin-top:0}
.panel-body>:last-child{margin-bottom:0}
.panel p{margin:0 0 10px}
h3.sub,h4.sub,h5.sub,h6.sub{margin:16px 0 8px;font-size:15px;font-weight:700}
h4.sub{font-size:14px}
h5.sub,h6.sub{font-size:13px;color:var(--muted)}
ul.list,ol.list{margin:0 0 12px;padding-left:20px}
ul.list li,ol.list li{margin:0 0 4px}
blockquote.quote{margin:0 0 12px;padding:2px 0 2px 14px;border-left:3px solid var(--line-strong);
  color:var(--muted)}
pre.code{position:relative;margin:0 0 12px;padding:12px 14px;background:var(--code-bg);
  border:1px solid var(--line);border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.55}
pre.code code{white-space:pre}
.code-lang{position:absolute;top:6px;right:10px;font-size:10px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted)}
.table-wrap{overflow-x:auto;margin:0 0 12px}
table.table{width:100%;border-collapse:collapse;font-size:14px}
table.table th,table.table td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
table.table th{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);
  font-weight:600;border-bottom:1px solid var(--line-strong)}
table.table tr:last-child td{border-bottom:none}
.mark{font-weight:700}
.mark-ok{color:var(--ok)}
.mark-no{color:var(--bad)}
.mark-warn{color:var(--warn)}
.callout{display:flex;gap:12px;margin:0 0 12px;padding:12px 14px;border-radius:8px;
  border:1px solid var(--line);background:var(--panel-2)}
.callout-tag{flex:0 0 auto;font-family:var(--mono);font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;padding:2px 8px;border-radius:999px;align-self:flex-start;
  border:1px solid currentColor;color:var(--muted)}
.callout-body{min-width:0}
.callout-body>:first-child{margin-top:0}
.callout-body>:last-child{margin-bottom:0}
.callout-title{display:block;margin-bottom:2px}
.callout-warn{border-left:3px solid var(--warn)}
.callout-warn .callout-tag{color:var(--warn)}
.callout-danger{border-left:3px solid var(--bad)}
.callout-danger .callout-tag{color:var(--bad)}
.callout-tip,.callout-key{border-left:3px solid var(--ok)}
.callout-tip .callout-tag,.callout-key .callout-tag{color:var(--ok)}
.callout-key{background:var(--accent-soft)}
.callout-note .callout-tag{color:var(--accent)}
.limits{display:grid;gap:14px}
.limit-name{font-size:14px}
.limit-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}
.limit-value{font-family:var(--mono);font-size:13px;color:var(--muted)}
.limit-track{height:8px;margin:6px 0 4px;background:var(--panel-2);border-radius:999px;
  border:1px solid var(--line);overflow:hidden}
.limit-fill{display:block;height:100%;background:var(--accent)}
.limit-fill.limit-warn{background:var(--warn)}
.limit-fill.limit-bad{background:var(--bad)}
.limit-foot{display:flex;gap:10px;font-size:12px;color:var(--muted)}
.limit-pct{font-family:var(--mono);font-weight:700;color:var(--accent)}
.limit-pct.limit-warn{color:var(--warn)}
.limit-pct.limit-bad{color:var(--bad)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}
.stat{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:var(--panel-2);
  display:flex;flex-direction:column;gap:2px}
.stat-name{font-size:12px;color:var(--muted)}
.stat-value{font-size:22px;font-weight:700;letter-spacing:-.01em}
.stat-delta{font-size:12px;font-family:var(--mono);color:var(--muted)}
.stat-delta.stat-ok{color:var(--ok)}
.stat-delta.stat-warn{color:var(--warn)}
.stat-delta.stat-no{color:var(--bad)}
dl.kv{display:grid;gap:0;margin:0}
.kv-row{display:grid;grid-template-columns:minmax(90px,32%) 1fr;gap:10px;padding:7px 0;
  border-bottom:1px solid var(--line)}
.kv-row:last-child{border-bottom:none}
.kv dt{color:var(--muted);font-size:13px}
.kv dd{margin:0;font-size:14px}
.annot-block{margin:0 0 12px}
.annot-sentence{margin:0;font-size:16px;line-height:2}
.annot{border-bottom:2px solid currentColor;padding-bottom:1px}
.annot-mark{font-size:9px;margin-left:2px;vertical-align:super;font-family:var(--mono)}
.annot-bad{color:var(--bad)}
.annot-warn{color:var(--warn)}
.annot-good{color:var(--ok)}
.annot-fix{color:var(--accent)}
.annot-legend{margin:10px 0 0;padding-left:20px;font-size:13px;color:var(--muted)}
.annot-legend li{margin:0 0 4px}
.annot-legend span{display:inline-block;min-width:16px;font-family:var(--mono);font-size:10px;
  color:var(--muted)}
.diagram{margin:0 0 12px;padding:6px 0;overflow-x:auto}
.diagram svg{max-width:100%;height:auto;display:block}
.diagram .node{fill:var(--node);stroke:var(--node-line);stroke-width:1.2}
.diagram .node-emph{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.6}
.diagram .node-tree-root{stroke:var(--accent)}
.diagram .node-label{fill:var(--ink)}
.diagram .edge{fill:none;stroke:var(--node-line);stroke-width:1.4}
.diagram .edge-dashed{stroke-dasharray:5 4}
.diagram .edge-bold{stroke-width:2.4}
.diagram .edge-head{fill:var(--node-line);stroke:none}
.diagram .edge-label{fill:var(--muted);font-family:var(--sans)}
.diagram .edge-label-bg{fill:var(--panel);stroke:none}
.diagram .lifeline{stroke:var(--line-strong);stroke-width:1.2;stroke-dasharray:4 4;fill:none}
.diagram .participant{fill:var(--node);stroke:var(--accent);stroke-width:1.2}
.diagram .note-box{fill:var(--panel-2);stroke:var(--line-strong);stroke-width:1;stroke-dasharray:3 3}
.diagram .activation{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1}
.diagram .frag{fill:none;stroke:var(--muted);stroke-width:1;stroke-dasharray:4 4}
.diagram .frag-tab{fill:var(--panel-2);stroke:var(--muted);stroke-width:1}
.diagram .frag-label{fill:var(--ink)}
.diagram .frag-divider{stroke:var(--line-strong);stroke-width:1;fill:none}
.diagram .flow-group rect{fill:none;stroke:var(--line-strong);stroke-width:1;stroke-dasharray:5 4}
.diagram .group-label{fill:var(--muted);font-family:var(--mono);letter-spacing:.06em}
.diagram .tl-spine{stroke:var(--line-strong);stroke-width:1.5;fill:none}
.diagram .tl-card{fill:var(--panel-2);stroke:var(--line);stroke-width:1}
.diagram .tl-card-hl{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4}
.diagram .tl-dot{fill:var(--panel);stroke:var(--node-line);stroke-width:1.6}
.diagram .tl-dot-hl{fill:var(--accent);stroke:var(--accent)}
.diagram .tl-date{fill:var(--muted);font-family:var(--mono)}
.diagram .tl-desc{fill:var(--muted)}
.colophon{margin-top:26px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);
  font-size:12px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.colophon code{font-size:11px}
@media (max-width:880px){
  .panels{grid-template-columns:minmax(0,1fr)}
  .panel.span-2{grid-column:auto}
  .doc{padding:20px 14px 56px}
  .masthead{align-items:flex-start}
  .kv-row{grid-template-columns:minmax(0,1fr)}
  /* Keep diagrams at their natural size and let the figure scroll. */
  .diagram{margin-left:-18px;margin-right:-18px;padding:6px 18px}
  .diagram svg{max-width:none}
}
@media (prefers-reduced-motion:no-preference){
  .panel{transition:border-color .15s ease}
}
@media print{
  body{background:#fff}
  .doc{max-width:none;padding:0}
  .toolbar{display:none}
  .panel{break-inside:avoid;border-color:#ccc}
  .diagram{break-inside:avoid}
}
"""

BLUEPRINT = """
:root[data-theme='blueprint']{
  --radius:0;
}
/* Blueprint keeps prose proportional and reserves the mono face for chrome.
   Diagram labels stay proportional too, because their box geometry is
   computed from a proportional width estimate. */
:root[data-theme='blueprint'] .eyebrow,
:root[data-theme='blueprint'] .panel-head,
:root[data-theme='blueprint'] h3.sub,
:root[data-theme='blueprint'] h4.sub,
:root[data-theme='blueprint'] h5.sub,
:root[data-theme='blueprint'] h6.sub,
:root[data-theme='blueprint'] .stamp,
:root[data-theme='blueprint'] .toolbar button,
:root[data-theme='blueprint'] .callout-tag,
:root[data-theme='blueprint'] .kv dt,
:root[data-theme='blueprint'] .code-lang,
:root[data-theme='blueprint'] .stat-value,
:root[data-theme='blueprint'] .stat-delta,
:root[data-theme='blueprint'] .limit-value,
:root[data-theme='blueprint'] .limit-pct{
  font-family:var(--mono);
}
:root[data-theme='blueprint'] body{
  background-color:var(--bg);
  background-image:linear-gradient(var(--grid-line) 1px,transparent 1px),
    linear-gradient(90deg,var(--grid-line) 1px,transparent 1px);
  background-size:26px 26px,26px 26px;
}
:root[data-theme='blueprint'] .doc{
  max-width:1220px;background:var(--panel);border:1px solid var(--line-strong);
  padding:0 22px 26px;box-shadow:none;
}
:root[data-theme='blueprint'] .masthead{
  margin:0 -22px 20px;padding:18px 22px 14px;background:var(--panel-2);
  border-bottom:2px solid var(--line-strong);align-items:center;
}
:root[data-theme='blueprint'] h1{font-size:clamp(20px,2.6vw,27px);letter-spacing:.02em}
:root[data-theme='blueprint'] .subtitle{font-family:var(--sans);font-size:14px}
:root[data-theme='blueprint'] .panel{background:transparent;border-color:var(--line-strong)}
:root[data-theme='blueprint'] .panel-head{font-size:12px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:6px}
:root[data-theme='blueprint'] h3.sub,h4.sub,h5.sub,h6.sub{font-size:12px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
:root[data-theme='blueprint'] .toolbar button{border-radius:0}
:root[data-theme='blueprint'] .stats .stat{border-radius:0;background:transparent}
:root[data-theme='blueprint'] .limit-track{border-radius:0}
:root[data-theme='blueprint'] .limit-fill{border-radius:0}
:root[data-theme='blueprint'] .diagram .node{rx:2px}
"""


def _tokens(mapping: dict[str, str]) -> str:
    return "\n".join(f"  --{name}:{value};" for name, value in mapping.items())


def build_css(theme: str) -> str:
    light = _tokens(LIGHT)
    dark = _tokens(DARK)
    css = BASE.replace("__LIGHT__", light).replace("__DARK__", dark)
    if theme == "blueprint":
        css += BLUEPRINT
    return css
