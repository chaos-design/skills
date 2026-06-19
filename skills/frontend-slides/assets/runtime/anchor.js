/* Anchor navigation runtime for Frontend Slides. */
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

  injectRuntimeStyle("frontend-slides-anchor-style", ".anchor-nav {\n  position: fixed;\n  right: 10px;\n  top: 50%;\n  z-index: 20;\n  transform: translateY(-50%);\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  gap: 12px;\n  padding: 16px 0;\n  width: 40px;\n  border-radius: 20px;\n  background: rgba(0, 0, 0, 0.5);\n  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22), inset 0 0 0 1px rgba(255, 255, 255, 0.08);\n  -webkit-backdrop-filter: blur(12px);\n  backdrop-filter: blur(12px);\n  opacity: 0.86;\n  transition: background 220ms ease, box-shadow 220ms ease, opacity 220ms ease, transform 220ms ease;\n}\n\n.anchor-nav:hover,\n.anchor-nav:focus-within {\n  transform: translateY(-50%) translateX(-2px);\n  background: rgba(0, 0, 0, 0.66);\n  box-shadow: 0 14px 38px rgba(0, 0, 0, 0.32), inset 0 0 0 1px rgba(255, 255, 255, 0.14);\n  opacity: 1;\n}\n\n.anchor-item {\n  position: relative;\n  z-index: 1;\n  min-height: 24px;\n  --anchor-dot-color: var(--accent);\n  --anchor-dot-rgb: var(--accent-rgb);\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  width: 100%;\n  color: rgba(255, 255, 255, 0.7);\n  text-decoration: none;\n  cursor: pointer;\n}\n\n.anchor-dot {\n  position: relative;\n  width: 10px;\n  height: 10px;\n  border-radius: 999px;\n  background: var(--anchor-dot-color);\n  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12), 0 5px 14px rgba(var(--anchor-dot-rgb), 0.28);\n  transition: width 180ms ease, height 180ms ease, background 180ms ease, box-shadow 180ms ease, transform 180ms ease;\n}\n\n.anchor-dot::after {\n  content: \"\";\n  position: absolute;\n  inset: -4px;\n  border-radius: inherit;\n  border: 1px solid rgba(var(--anchor-dot-rgb), 0);\n  opacity: 0;\n  pointer-events: none;\n}\n\n.anchor-item:hover .anchor-dot {\n  transform: scale(1.3);\n  box-shadow: 0 0 0 4px rgba(var(--anchor-dot-rgb), 0.14), 0 7px 18px rgba(var(--anchor-dot-rgb), 0.34);\n}\n\n.anchor-item:not(.active) {\n  --anchor-dot-color: #f4a63a;\n  --anchor-dot-rgb: 244, 166, 58;\n}\n\n.anchor-item.active .anchor-dot {\n  width: 12px;\n  height: 28px;\n  background: var(--anchor-dot-color);\n  box-shadow: 0 0 0 6px rgba(var(--accent-rgb), 0.24), 0 10px 24px rgba(var(--accent-rgb), 0.38), inset 0 1px 4px rgba(255, 255, 255, 0.45);\n  animation: anchor-breathe 2.6s ease-in-out infinite;\n}\n\n.anchor-item.active .anchor-dot::after {\n  inset: -6px;\n  border-color: rgba(var(--accent-rgb), 0.26);\n  animation: anchor-edge-spread 2.6s ease-out infinite;\n}\n\n.anchor-label {\n  position: absolute;\n  right: 45px;\n  top: 50%;\n  transform: translateY(-50%);\n  max-width: 0;\n  padding: 0;\n  overflow: hidden;\n  white-space: normal;\n  line-height: 1.35;\n  opacity: 0;\n  pointer-events: none;\n  border-radius: 12px;\n  background: rgba(18, 20, 28, 0.82);\n  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);\n  color: rgba(255, 255, 255, 0.92);\n  font-size: 12px;\n  font-weight: 760;\n  -webkit-backdrop-filter: blur(12px);\n  backdrop-filter: blur(12px);\n  transition: opacity 160ms ease, max-width 160ms ease, padding 160ms ease;\n}\n\n.anchor-item:hover .anchor-label,\n.anchor-item:focus-visible .anchor-label {\n  width: max-content;\n  max-width: min(420px, calc(100vw - 120px));\n  padding: 9px 14px;\n  opacity: 1;\n}\n\n@keyframes anchor-breathe {\n  0%,\n  100% {\n    box-shadow: 0 0 0 5px rgba(var(--accent-rgb), 0.18), 0 10px 24px rgba(var(--accent-rgb), 0.32), inset 0 1px 4px rgba(255, 255, 255, 0.42);\n    opacity: 0.94;\n  }\n  50% {\n    box-shadow: 0 0 0 11px rgba(var(--accent-rgb), 0.28), 0 13px 32px rgba(var(--accent-rgb), 0.46), inset 0 1px 5px rgba(255, 255, 255, 0.5);\n    opacity: 1;\n  }\n}\n\n@keyframes anchor-edge-spread {\n  0% {\n    opacity: 0.32;\n    transform: scale(0.82);\n  }\n  60%,\n  100% {\n    opacity: 0;\n    transform: scale(1.72);\n  }\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .anchor-item.active .anchor-dot,\n  .anchor-item.active .anchor-dot::after {\n    animation: none;\n  }\n}\n\n@media (max-width: 820px) {\n  .anchor-nav {\n    right: 8px;\n  }\n}");

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

  function pad(index) {
    return String(index).padStart(2, "0");
  }

  function normalizeAnchors(data) {
    const slides = asList(data && data.slides);
    if (slides.length) {
      return slides.map((slide, position) => ({
        href: "#" + String(slide.id || "slide-" + (position + 1)),
        label: pad(position + 1) + " " + String(slide.title || "Slide " + (position + 1)),
      }));
    }
    return asList(data).map((anchor) => ({
      href: String(anchor.href || "#"),
      label: String(anchor.label || ""),
    }));
  }

  function buildAnchorNav(data, options) {
    const settings = options || {};
    const escape = settings.htmlEscape || htmlEscape;
    const anchors = normalizeAnchors(data);
    const nav = document.createElement("nav");
    nav.className = "anchor-nav";
    nav.setAttribute("aria-label", "Slide anchors");
    nav.innerHTML = anchors
      .map((anchor, position) => {
        const label = escape(anchor.label);
        return (
          '<a class="anchor-item" href="' + escape(anchor.href) + '" aria-label="' + label + '" data-anchor-index="' + position + '">' +
          '<span class="anchor-dot"></span><span class="anchor-label">' + label + "</span></a>"
        );
      })
      .join("\n");

    const items = Array.prototype.slice.call(nav.querySelectorAll(".anchor-item"));
    nav.setActiveIndex = function (activeIndex) {
      items.forEach((item, position) => item.classList.toggle("active", position === activeIndex));
    };

    items.forEach((item, position) => {
      item.addEventListener("click", (event) => {
        event.preventDefault();
        nav.setActiveIndex(position);
        if (typeof settings.onSelect === "function") settings.onSelect(position, anchors[position], event);
      });
    });

    return nav;
  }

  runtime.buildAnchorNav = buildAnchorNav;
})(window);
