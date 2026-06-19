/* Keyboard shortcut bar runtime for Frontend Slides. */
(function (global) {
  "use strict";

  const runtime = global.DocPageSlidesRuntime || (global.DocPageSlidesRuntime = {});

  function injectRuntimeStyle(id, css) {
    if (document.getElementById(id)) return;
    const style = document.createElement("style");
    style.id = id;
    style.textContent = css;
    (document.head || document.documentElement).appendChild(style);
  }

  injectRuntimeStyle("frontend-slides-shortcut-style", ".shortcut-bar {\n  position: fixed;\n  left: 0;\n  right: 0;\n  bottom: 0;\n  z-index: 30;\n  width: 100%;\n  max-width: 100%;\n  padding: 8px 22px;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  gap: 18px;\n  overflow-x: auto;\n  border: none;\n  border-top: 1px solid rgba(20, 24, 32, 0.08);\n  border-radius: 0;\n  background: rgba(255, 255, 255, 0.86);\n  box-shadow: 0 -4px 18px rgba(20, 24, 32, 0.08);\n  color: #151515;\n  -webkit-backdrop-filter: blur(16px);\n  backdrop-filter: blur(16px);\n  opacity: 0.9;\n  transition: opacity 220ms ease, background 220ms ease;\n}\n\n.shortcut-bar:hover,\n.shortcut-bar:focus-within {\n  opacity: 1;\n  background: rgba(255, 255, 255, 0.94);\n}\n\n.shortcut {\n  display: inline-flex;\n  align-items: center;\n  gap: 7px;\n  color: rgba(21, 21, 21, 0.64);\n  font-size: 11px;\n  font-weight: 650;\n  white-space: nowrap;\n}\n\nkbd {\n  min-width: 20px;\n  height: 18px;\n  padding: 0 7px;\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  border: 1px solid rgba(20, 24, 32, 0.1);\n  border-bottom-color: rgba(20, 24, 32, 0.16);\n  border-radius: 6px;\n  background: rgba(248, 249, 251, 0.95);\n  box-shadow: 0 1px 4px rgba(20, 24, 32, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.96);\n  color: #151515;\n  font: 700 10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;\n  line-height: 1;\n  text-align: center;\n}\n\n.plus {\n  margin: 0 -2px;\n  color: rgba(21, 21, 21, 0.42);\n  font-size: 10px;\n  font-weight: 800;\n}\n\n.or {\n  width: 3px;\n}");

  const SHORTCUT_LABELS = {
    en: {
      next: "Next slide",
      prev: "Previous",
      home: "First",
      end: "Last",
    },
    zh: {
      next: "下一页",
      prev: "上一页",
      home: "首页",
      end: "末页",
    },
  };

  function htmlEscape(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function asList(value) {
    return Array.isArray(value) ? value : [];
  }

  function isObject(value) {
    return value != null && typeof value === "object" && !Array.isArray(value);
  }

  function resolveLanguage(data) {
    const requested = String((data && (data.language || data.locale)) || document.documentElement.lang || "zh-CN").toLowerCase();
    return requested.indexOf("en") === 0 ? "en" : "zh";
  }

  function resolveShortcutLabels(data, language) {
    const fallback = SHORTCUT_LABELS[language] || SHORTCUT_LABELS.zh;
    const custom = isObject(data && data.shortcutLabels) ? data.shortcutLabels : {};
    const customKeys = Object.keys(custom);
    const hasDirectLabels = ["next", "prev", "home", "end"].some((key) => typeof custom[key] === "string");
    const firstLabelSet = customKeys.map((key) => custom[key]).find(isObject);
    const customLabels = isObject(custom[language]) ? custom[language] : hasDirectLabels ? custom : firstLabelSet || custom;
    return Object.assign({}, fallback, customLabels);
  }

  function shortcutLabel(action, labels) {
    return labels[action] || action;
  }

  function normalizeShortcutLabel(label, action, labels) {
    const text = String(label || "");
    return text || shortcutLabel(action, labels);
  }

  function defaultShortcuts(labels) {
    return [
      { keys: ["Space", "ArrowDown", "ArrowRight"], label: shortcutLabel("next", labels), action: "next" },
      { keys: ["ArrowLeft", "ArrowUp"], label: shortcutLabel("prev", labels), action: "prev" },
      { keys: ["Option+ArrowLeft"], label: shortcutLabel("home", labels), action: "home" },
      { keys: ["Option+ArrowRight"], label: shortcutLabel("end", labels), action: "end" },
    ];
  }

  function normalizeShortcuts(data) {
    const language = resolveLanguage(data);
    const labels = resolveShortcutLabels(data, language);
    const source = asList(data && data.shortcuts).length ? data.shortcuts : data;
    const shortcuts = asList(source)
      .filter(isObject)
      .map((item) => ({
        keys: asList(item.keys).map(String),
        label: normalizeShortcutLabel(item.label, String(item.action || ""), labels),
        action: String(item.action || ""),
      }))
      .filter((item) => item.keys.length && item.label && item.action);
    return shortcuts.length ? shortcuts : defaultShortcuts(labels);
  }

  function findShortcut(shortcuts, key) {
    return shortcuts.find((item) => item.keys.indexOf(key) !== -1);
  }

  function eventKey(event) {
    const key = event.key === " " ? "Space" : event.key === "Escape" ? "Esc" : event.key;
    const modifiers = [];
    if (event.metaKey && key !== "Meta") modifiers.push("Meta");
    if (event.ctrlKey && key !== "Control") modifiers.push("Control");
    if (event.altKey && key !== "Alt" && key !== "Option") modifiers.push("Option");
    if (event.shiftKey && key !== "Shift") modifiers.push("Shift");
    return modifiers.concat(key).join("+");
  }

  function displayKey(key) {
    const symbols = {
      " ": "Space",
      Alt: "⌥",
      ArrowUp: "↑",
      ArrowDown: "↓",
      ArrowLeft: "←",
      ArrowRight: "→",
      Backspace: "⌫",
      CapsLock: "⇪",
      Cmd: "⌘",
      Command: "⌘",
      Control: "⌃",
      Ctrl: "⌃",
      Delete: "⌦",
      Enter: "↩",
      Esc: "Esc",
      Escape: "Esc",
      Home: "Home",
      End: "End",
      Meta: "⌘",
      Option: "⌥",
      PageUp: "⇞",
      PageDown: "⇟",
      Shift: "⇧",
      Tab: "⇥",
    };
    return symbols[key] || key;
  }

  function displayKeyGroup(key, escape) {
    return key
      .split("+")
      .map((part) => '<kbd title="' + escape(part) + '">' + escape(displayKey(part)) + "</kbd>")
      .join('<span class="plus">+</span>');
  }

  function buildShortcutBar(data, options) {
    const settings = options || {};
    const escape = settings.htmlEscape || htmlEscape;
    const shortcuts = normalizeShortcuts(data);
    const bar = document.createElement("aside");
    bar.className = "shortcut-bar";
    bar.setAttribute("aria-label", "Keyboard shortcuts");
    bar.innerHTML = shortcuts
      .map((shortcut) => {
        const keys = shortcut.keys.map((key) => displayKeyGroup(key, escape)).join('<span class="or"></span>');
        return '<span class="shortcut">' + keys + "<span>" + escape(shortcut.label) + "</span></span>";
      })
      .join("\n");

    document.addEventListener("keydown", (event) => {
      const shortcut = findShortcut(shortcuts, eventKey(event));
      if (!shortcut) return;
      event.preventDefault();
      if (typeof settings.onAction === "function") settings.onAction(shortcut.action, shortcut, event);
    });

    return bar;
  }

  runtime.buildShortcutBar = buildShortcutBar;
})(window);
