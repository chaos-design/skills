"""Page assembly: panel grid, masthead, toolbar and inline behaviour."""
from __future__ import annotations

from .blocks import plain, render_blocks, set_locale
from .parser import Document, Panel
from .textutil import HTML_LANG, UI_TEXT, esc, esc_attr, detect_lang

THEMES = ("blueprint", "document")
MODES = ("auto", "light", "dark")

PANEL_TEMPLATE = """  <section class="panel{span}"{id}>
{heading}    <div class="panel-body">{body}</div>
  </section>"""


def pack_panels(panels: list[Panel], columns: int) -> list[int]:
    """Choose each panel's column span without leaving holes in the grid.

    Panels keep their authored order. A trailing narrow panel is widened: a
    half-width cell at the end of the grid reads as a missing panel, and the
    grid has no way to back-fill it without reordering the brief.
    """
    if columns < 2:
        return [columns] * len(panels)
    spans = [panel.span for panel in panels]
    if spans and spans[-1] == 1:
        spans[-1] = 2
    return spans


def _toolbar(ui: dict[str, str], theme: str, mode: str) -> str:
    blueprint_label = f"{ui['theme']} · Blueprint"
    document_label = f"{ui['theme']} · Document"
    mode_labels = {
        "auto": f"{ui['mode']} · {ui['auto']}",
        "light": f"{ui['mode']} · {ui['light']}",
        "dark": f"{ui['mode']} · {ui['dark']}",
    }
    return (
        '<div class="toolbar" role="group">'
        f'<button type="button" data-act="theme" data-label-bp="{esc_attr(blueprint_label)}" '
        f'data-label-doc="{esc_attr(document_label)}">'
        f"{esc(blueprint_label if theme == 'blueprint' else document_label)}</button>"
        f'<button type="button" data-act="mode" data-label-auto="{esc_attr(mode_labels["auto"])}" '
        f'data-label-light="{esc_attr(mode_labels["light"])}" '
        f'data-label-dark="{esc_attr(mode_labels["dark"])}">{esc(mode_labels[mode])}</button>'
        f'<button type="button" data-act="copy" data-label-on="{esc_attr(ui["copy"])}" '
        f'data-label-off="{esc_attr(ui["copied"])}" '
        f'data-label-error="{esc_attr(ui["copy_failed"])}">{esc(ui["copy"])}</button>'
        "</div>"
    )


SCRIPT = """
(function () {
  var root = document.documentElement;
  var store = 'html-brief:view';
  var modes = ['auto', 'light', 'dark'];
  var themes = ['blueprint', 'document'];
  try {
    var saved = JSON.parse(localStorage.getItem(store) || '{}');
    if (themes.indexOf(saved.theme) > -1) root.setAttribute('data-theme', saved.theme);
    if (modes.indexOf(saved.mode) > -1) root.setAttribute('data-mode', saved.mode);
  } catch (error) {}
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.toolbar button'));
  function persist() {
    try {
      localStorage.setItem(
        store,
        JSON.stringify({ theme: root.getAttribute('data-theme'), mode: root.getAttribute('data-mode') })
      );
    } catch (error) {}
  }
  function relabel(button, text) {
    if (text) button.textContent = text;
  }
  function cycle(list, current) {
    var index = list.indexOf(current);
    return list[(index + 1) % list.length];
  }
  function copySource(button) {
    var node = document.getElementById('html-brief-source');
    var text = node ? node.textContent : '';
    function done(ok) {
      relabel(button, ok ? button.getAttribute('data-label-off') : button.getAttribute('data-label-error'));
      window.setTimeout(function () {
        relabel(button, button.getAttribute('data-label-on'));
      }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { done(true); },
        function () { done(false); }
      );
      return;
    }
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (error) { ok = false; }
    document.body.removeChild(area);
    done(ok);
  }
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var act = button.getAttribute('data-act');
      if (act === 'theme') {
        var next = cycle(themes, root.getAttribute('data-theme'));
        root.setAttribute('data-theme', next);
        relabel(
          button,
          next === 'blueprint'
            ? button.getAttribute('data-label-bp')
            : button.getAttribute('data-label-doc')
        );
        persist();
        return;
      }
      if (act === 'mode') {
        var mode = cycle(modes, root.getAttribute('data-mode'));
        root.setAttribute('data-mode', mode);
        relabel(button, button.getAttribute('data-label-' + mode));
        persist();
        return;
      }
      if (act === 'copy') copySource(button);
    });
  });
})();
"""


def render_page(
    document: Document,
    *,
    source_text: str,
    theme: str = "document",
    mode: str = "auto",
    lang: str = "auto",
    columns: int = 2,
    stamp: str = "",
    source_label: str = "",
    note: str = "",
) -> str:
    if lang not in HTML_LANG:
        lang = detect_lang(document.title + " " + source_text[:2000])
    ui = UI_TEXT.get(lang, UI_TEXT["en"])
    set_locale(lang)
    spans = pack_panels(document.panels, columns)

    panels: list[str] = []
    for index, (panel, span) in enumerate(zip(document.panels, spans), start=1):
        title = plain(panel.title) or f"Panel {index}"
        body = render_blocks(panel.blocks, title)
        span_class = " span-2" if span == 2 else ""
        anchor = f' id="panel-{index}"' if panel.title else ""
        heading = f'<h2 class="panel-head">{esc(title)}</h2>\n' if panel.title else ""
        panels.append(
            PANEL_TEMPLATE.format(span=span_class, id=anchor, heading=heading, body=body)
        )

    subtitle = plain(document.meta.get("subtitle", ""))
    parts = [
        "<!doctype html>",
        f'<html lang="{HTML_LANG.get(lang, "en")}" data-theme="{esc_attr(theme)}" data-mode="{esc_attr(mode)}">',
        "<head>",
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width,initial-scale=1" />',
        '<meta name="generator" content="html-brief" />',
        f'<meta name="description" content="{esc_attr(subtitle or document.title)}" />',
        f"<title>{esc(document.title)}</title>",
        "<style>",
        _css(theme),
        "</style>",
        "</head>",
        "<body>",
        '<div class="doc">',
        '<header class="masthead">',
        '<div class="masthead-text">',
        '<p class="eyebrow">HTML Brief</p>',
        f"<h1>{esc(document.title)}</h1>",
        f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else "",
        f'<p class="stamp">{esc(stamp)}</p>' if stamp else "",
        "</div>",
        _toolbar(ui, theme, mode),
        "</header>",
        '<main class="panels">',
        *panels,
        "</main>",
        '<footer class="colophon">',
        f"<span>{esc(note)}</span>" if note else "",
        "<span>Built with the <code>html-brief</code> skill.</span>",
        "</footer>",
        "</div>",
        '<script type="text/markdown" id="html-brief-source">',
        source_text.replace("</script", "<\\/script"),
        "</script>",
        "<script>",
        SCRIPT,
        "</script>",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(part for part in parts if part != "")


_CSS_CACHE: dict[str, str] = {}


def _css(theme: str) -> str:
    if theme not in _CSS_CACHE:
        from .theme import build_css

        _CSS_CACHE[theme] = build_css(theme)
    return _CSS_CACHE[theme]