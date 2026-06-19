/* Frontend Slides browser runtime.
 *
 * Reads deck data embedded as JSON in <script type="application/json" id="deck-data">,
 * renders one of the structural templates entirely in the browser, and wires up:
 *   - left-side anchor navigation where every anchor is an independent full page;
 *   - title tooltips that stay hidden until an anchor is hovered or focused;
 *   - a configurable bottom keyboard shortcut bar.
 */
(function () {
  "use strict";

  const runtime = window.DocPageSlidesRuntime || (window.DocPageSlidesRuntime = {});

  function injectRuntimeStyle(id, css) {
    if (document.getElementById(id)) return;
    const style = document.createElement("style");
    style.id = id;
    style.textContent = css;
    (document.head || document.documentElement).appendChild(style);
  }

  injectRuntimeStyle("frontend-slides-deck-style", ":root {\n  color-scheme: light;\n  --bg: #f7f3ed;\n  --paper: rgba(255, 252, 246, 0.92);\n  --ink: #171717;\n  --muted: #746f66;\n  --accent: #16a085;\n  --accent-rgb: 22, 160, 133;\n  --line: rgba(23, 23, 23, 0.1);\n  --shadow: 0 18px 50px rgba(54, 44, 32, 0.12);\n}\n* {\n  box-sizing: border-box;\n}\nhtml {\n  scroll-behavior: smooth;\n  overscroll-behavior: none;\n}\nbody {\n  margin: 0;\n  background: radial-gradient(circle at 20% 10%, #fffaf0 0, var(--bg) 36%, #efeae1 100%);\n  color: var(--ink);\n  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;\n  overflow: hidden;\n  overscroll-behavior: none;\n}\n.deck {\n  --scroll-drag: 0px;\n  width: min(980px, calc(100vw - 96px));\n  margin: 0 auto;\n  padding: 0 0 110px;\n  transform: translate3d(0, var(--scroll-drag), 0);\n  transition: transform 220ms cubic-bezier(0.22, 1, 0.36, 1);\n}\n\n/* Each anchor maps to one independent full-height page.\n   Only the active page is shown; the rest are detached from view\n   so their content never interferes with the current page. */\n.slide {\n  min-height: 100vh;\n  padding: 48px 56px;\n  display: none;\n  flex-direction: column;\n  justify-content: center;\n}\n.slide.active {\n  display: flex;\n  animation: slide-enter-up 420ms cubic-bezier(0.22, 1, 0.36, 1);\n}\n.deck[data-transition=\"prev\"] .slide.active {\n  animation-name: slide-enter-down;\n}\n@keyframes slide-enter-up {\n  from {\n    opacity: 0;\n    transform: translate3d(0, 34px, 0) scale(0.985);\n    filter: blur(6px);\n  }\n  to {\n    opacity: 1;\n    transform: translate3d(0, 0, 0) scale(1);\n    filter: blur(0);\n  }\n}\n@keyframes slide-enter-down {\n  from {\n    opacity: 0;\n    transform: translate3d(0, -34px, 0) scale(0.985);\n    filter: blur(6px);\n  }\n  to {\n    opacity: 1;\n    transform: translate3d(0, 0, 0) scale(1);\n    filter: blur(0);\n  }\n}\n.slide h1 {\n  margin: 0 0 22px;\n  font-size: clamp(42px, 7vw, 86px);\n  line-height: 0.92;\n  letter-spacing: -0.07em;\n}\n.slide-kicker,\n.eyebrow {\n  color: var(--accent);\n  font-size: 12px;\n  font-weight: 750;\n  letter-spacing: 0.12em;\n  text-transform: uppercase;\n}\n.slide-body {\n  font-size: 20px;\n  line-height: 1.72;\n}\n.lede {\n  max-width: 760px;\n  color: var(--muted);\n  font-size: clamp(24px, 3vw, 38px);\n  line-height: 1.28;\n}\nblockquote {\n  margin: 0 0 24px;\n  padding-left: 22px;\n  border-left: 5px solid var(--accent);\n  font-size: 30px;\n  line-height: 1.3;\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .slide.active {\n    animation: none;\n  }\n}\n\n.card-grid,\n.process-grid,\n.metric-grid,\n.source-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));\n  gap: 18px;\n}\n.card,\n.metric,\n.source-card,\n.statement,\n.split aside {\n  padding: 22px;\n  border: 1px solid var(--line);\n  border-radius: 22px;\n  background: var(--paper);\n  box-shadow: var(--shadow);\n}\n.metric strong {\n  display: block;\n  font-size: 42px;\n  letter-spacing: -0.05em;\n}\n.split {\n  display: grid;\n  grid-template-columns: minmax(0, 1.35fr) minmax(240px, 0.65fr);\n  gap: 24px;\n  align-items: start;\n}\n.timeline,\n.agenda-list {\n  font-size: 24px;\n  line-height: 1.6;\n}\n.timeline li {\n  display: grid;\n  grid-template-columns: 130px 1fr;\n  gap: 20px;\n  margin: 18px 0;\n}\n.image-frame img,\n.source-image img {\n  width: 100%;\n  max-height: 62vh;\n  object-fit: cover;\n  border-radius: 28px;\n  box-shadow: var(--shadow);\n}\n.tag-row {\n  display: flex;\n  gap: 10px;\n  flex-wrap: wrap;\n}\n.tag-row span {\n  padding: 7px 12px;\n  border-radius: 999px;\n  background: #e7f5f1;\n  color: #087865;\n  font-size: 13px;\n  font-weight: 700;\n}\n.tag-row span:nth-child(5n + 1) {\n  background: #e7f5f1;\n  color: #087865;\n}\n.tag-row span:nth-child(5n + 2) {\n  background: #eef0ff;\n  color: #4f46e5;\n}\n.tag-row span:nth-child(5n + 3) {\n  background: #fff1e8;\n  color: #c05621;\n}\n.tag-row span:nth-child(5n + 4) {\n  background: #f7eefe;\n  color: #9333ea;\n}\n.tag-row span:nth-child(5n + 5) {\n  background: #eef7ff;\n  color: #0369a1;\n}\n\n.deck[data-visual-template=\"true\"] {\n  width: min(1180px, calc(100vw - 96px));\n}\n.slide.visual-slide {\n  --visual-bg: #f2eadb;\n  --visual-paper: rgba(255, 251, 241, 0.88);\n  --visual-ink: #171717;\n  --visual-muted: rgba(23, 23, 23, 0.68);\n  --visual-accent: #1f2be0;\n  --visual-line: rgba(23, 23, 23, 0.16);\n  position: relative;\n  padding: 64px 72px;\n  background:\n    linear-gradient(90deg, var(--visual-line) 1px, transparent 1px),\n    linear-gradient(var(--visual-line) 1px, transparent 1px),\n    var(--visual-bg);\n  background-size: 44px 44px;\n  color: var(--visual-ink);\n  overflow: hidden;\n}\n.slide.visual-slide::before,\n.slide.visual-slide::after {\n  content: \"\";\n  position: absolute;\n  pointer-events: none;\n  z-index: 0;\n}\n.slide.visual-slide::before {\n  inset: 28px;\n  border: 1px solid color-mix(in srgb, var(--visual-accent) 64%, transparent);\n}\n.slide.visual-slide::after {\n  right: 34px;\n  top: 62px;\n  width: 180px;\n  height: 180px;\n  border-radius: 999px;\n  background: var(--visual-accent);\n  opacity: 0.14;\n}\n.visual-slide > * {\n  position: relative;\n  z-index: 1;\n}\n.visual-slide .slide-kicker,\n.visual-slide .eyebrow {\n  color: var(--visual-accent);\n}\n.visual-slide h1 {\n  color: var(--visual-ink);\n  max-width: 920px;\n  text-transform: none;\n}\n.visual-slide .lede,\n.visual-slide .slide-body {\n  color: var(--visual-muted);\n}\n.visual-slide .visual-accent,\n.visual-slide .visual-attribution {\n  margin-top: 22px;\n  color: var(--visual-accent);\n  font-size: 13px;\n  font-weight: 800;\n  letter-spacing: 0.14em;\n  text-transform: uppercase;\n}\n.visual-card,\n.visual-slide .metric,\n.visual-slide .statement,\n.visual-placeholder {\n  border-color: color-mix(in srgb, var(--visual-accent) 46%, transparent);\n  background: var(--visual-paper);\n  color: var(--visual-ink);\n}\n.visual-slide .statement {\n  font-size: clamp(34px, 4.4vw, 68px);\n  line-height: 1.06;\n  letter-spacing: -0.04em;\n}\n.visual-slide .metric strong {\n  color: var(--visual-accent);\n}\n.visual-grid {\n  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));\n}\n.visual-placeholder {\n  min-height: 420px;\n  display: grid;\n  place-items: center;\n  border: 1px solid var(--visual-line);\n  border-radius: 28px;\n  font-size: clamp(26px, 4vw, 52px);\n  text-align: center;\n}\n\n.template-soft-editorial,\n.template-editorial-forest {\n  --visual-bg: #efe7d4;\n  --visual-paper: rgba(255, 246, 229, 0.84);\n  --visual-ink: #243a21;\n  --visual-muted: #5e6a52;\n  --visual-accent: #d27e96;\n  font-family: Georgia, \"Times New Roman\", serif;\n  background-image: radial-gradient(circle at 78% 16%, rgba(232, 156, 177, 0.42), transparent 22%), none;\n}\n.template-pin-and-paper,\n.template-daisy-days {\n  --visual-bg: #fae58f;\n  --visual-paper: rgba(255, 248, 201, 0.9);\n  --visual-ink: #12315f;\n  --visual-muted: #5c4a2a;\n  --visual-accent: #f05f42;\n  background-image: radial-gradient(circle at 12px 12px, rgba(18, 49, 95, 0.12) 2px, transparent 2px);\n  background-size: 22px 22px;\n}\n.template-sakura-chroma,\n.template-creative-mode {\n  --visual-bg: #f1e6cb;\n  --visual-paper: rgba(255, 247, 221, 0.86);\n  --visual-ink: #3a2516;\n  --visual-muted: #735b43;\n  --visual-accent: #e54489;\n  background:\n    linear-gradient(135deg, transparent 0 55%, rgba(229, 68, 137, 0.32) 55% 60%, rgba(240, 145, 49, 0.32) 60% 65%, rgba(61, 159, 71, 0.28) 65% 70%, transparent 70%),\n    var(--visual-bg);\n}\n.template-stencil-tablet,\n.template-cartesian {\n  --visual-bg: #e9dfc8;\n  --visual-paper: rgba(251, 244, 228, 0.88);\n  --visual-ink: #392f24;\n  --visual-muted: #6a5f50;\n  --visual-accent: #8a4d2f;\n  font-family: Georgia, \"Times New Roman\", serif;\n}\n.template-cobalt-grid,\n.template-blue-professional {\n  --visual-bg: #f0ebde;\n  --visual-paper: rgba(255, 252, 246, 0.9);\n  --visual-ink: #1f2be0;\n  --visual-muted: #5560e5;\n  --visual-accent: #1f2be0;\n  background-size: 32px 32px;\n}\n.template-vellum,\n.template-pink-script,\n.template-broadside {\n  --visual-bg: #101832;\n  --visual-paper: rgba(251, 241, 209, 0.08);\n  --visual-ink: #f5e4a8;\n  --visual-muted: rgba(245, 228, 168, 0.72);\n  --visual-accent: #ff5a8f;\n  background:\n    radial-gradient(circle at 82% 18%, rgba(255, 90, 143, 0.18), transparent 24%),\n    #101832;\n}\n.template-emerald-editorial {\n  --visual-bg: #e9dfc8;\n  --visual-paper: rgba(255, 249, 230, 0.9);\n  --visual-ink: #092c2b;\n  --visual-muted: #315756;\n  --visual-accent: #007a4d;\n}\n.template-neo-grid-bold,\n.template-block-frame {\n  --visual-bg: #ecece8;\n  --visual-paper: #f5f4ef;\n  --visual-ink: #0a0a0a;\n  --visual-muted: #4d4d49;\n  --visual-accent: #d7f934;\n  font-family: \"Arial Black\", Impact, sans-serif;\n}\n.template-neo-grid-bold::before,\n.template-block-frame::before {\n  border-width: 4px;\n}\n.template-editorial-tri-tone {\n  --visual-bg: #f2d3cf;\n  --visual-paper: rgba(255, 241, 211, 0.84);\n  --visual-ink: #4b1724;\n  --visual-muted: #7c4750;\n  --visual-accent: #c18a1d;\n}\n.template-monochrome {\n  --visual-bg: #f2ecd9;\n  --visual-paper: rgba(255, 252, 244, 0.9);\n  --visual-ink: #101010;\n  --visual-muted: #55514a;\n  --visual-accent: #101010;\n  filter: grayscale(1);\n}\n.template-peoples-platform,\n.template-bold-poster {\n  --visual-bg: #f6e8c8;\n  --visual-paper: rgba(255, 244, 218, 0.88);\n  --visual-ink: #142b6f;\n  --visual-muted: #613a2f;\n  --visual-accent: #df4b2f;\n  font-family: Impact, \"Arial Black\", sans-serif;\n}\n.template-8-bit-orbit {\n  --visual-bg: #09132b;\n  --visual-paper: rgba(35, 236, 255, 0.08);\n  --visual-ink: #8ffcff;\n  --visual-muted: rgba(143, 252, 255, 0.7);\n  --visual-accent: #ffdf4d;\n  background-image:\n    linear-gradient(90deg, rgba(143, 252, 255, 0.13) 2px, transparent 2px),\n    linear-gradient(rgba(143, 252, 255, 0.13) 2px, transparent 2px);\n  background-size: 28px 28px;\n  image-rendering: pixelated;\n}\n.template-biennale-yellow {\n  --visual-bg: #efe3bd;\n  --visual-paper: rgba(255, 246, 210, 0.9);\n  --visual-ink: #18245a;\n  --visual-muted: #596083;\n  --visual-accent: #f4c82f;\n}\n.template-capsule {\n  --visual-bg: #f6ead8;\n  --visual-paper: rgba(255, 250, 239, 0.92);\n  --visual-ink: #252525;\n  --visual-muted: #74706a;\n  --visual-accent: #79c6ff;\n}\n.template-capsule .card,\n.template-capsule .metric,\n.template-capsule .statement {\n  border-radius: 999px;\n}\n.template-coral {\n  --visual-bg: #171313;\n  --visual-paper: rgba(255, 235, 213, 0.1);\n  --visual-ink: #ffe9d1;\n  --visual-muted: rgba(255, 233, 209, 0.72);\n  --visual-accent: #ff735c;\n  font-family: Impact, \"Arial Narrow\", sans-serif;\n}\n.template-ink-wash-scroll {\n  --visual-bg: #f4efe3;\n  --visual-paper: rgba(255, 252, 244, 0.72);\n  --visual-ink: #1f2522;\n  --visual-muted: #60665d;\n  --visual-accent: #b23a2e;\n  font-family: \"Noto Serif SC\", \"Songti SC\", Georgia, serif;\n  background:\n    radial-gradient(ellipse at 78% 18%, rgba(31, 37, 34, 0.18), transparent 28%),\n    radial-gradient(ellipse at 22% 72%, rgba(178, 58, 46, 0.14), transparent 20%),\n    linear-gradient(90deg, rgba(31, 37, 34, 0.08) 1px, transparent 1px),\n    #f4efe3;\n}\n.template-lunar-terminal {\n  --visual-bg: #07111f;\n  --visual-paper: rgba(134, 239, 255, 0.08);\n  --visual-ink: #d9fbff;\n  --visual-muted: rgba(217, 251, 255, 0.68);\n  --visual-accent: #7dd3fc;\n  font-family: \"DM Mono\", ui-monospace, SFMono-Regular, Menlo, monospace;\n  background:\n    radial-gradient(circle at 78% 22%, rgba(125, 211, 252, 0.24), transparent 22%),\n    linear-gradient(90deg, rgba(125, 211, 252, 0.12) 1px, transparent 1px),\n    linear-gradient(rgba(125, 211, 252, 0.12) 1px, transparent 1px),\n    #07111f;\n  background-size: auto, 36px 36px, 36px 36px, auto;\n}\n.template-glass-atelier {\n  --visual-bg: #e9e7f6;\n  --visual-paper: rgba(255, 255, 255, 0.48);\n  --visual-ink: #241b3d;\n  --visual-muted: #665d82;\n  --visual-accent: #7c3aed;\n  background:\n    radial-gradient(circle at 16% 20%, rgba(124, 58, 237, 0.22), transparent 24%),\n    radial-gradient(circle at 84% 70%, rgba(45, 212, 191, 0.22), transparent 28%),\n    #e9e7f6;\n  backdrop-filter: blur(10px);\n}\n.template-clay-diagram {\n  --visual-bg: #ead3bd;\n  --visual-paper: rgba(255, 244, 231, 0.86);\n  --visual-ink: #3c2a20;\n  --visual-muted: #765e4f;\n  --visual-accent: #b75f38;\n  background:\n    linear-gradient(120deg, rgba(183, 95, 56, 0.16), transparent 38%),\n    linear-gradient(90deg, rgba(60, 42, 32, 0.1) 1px, transparent 1px),\n    linear-gradient(rgba(60, 42, 32, 0.1) 1px, transparent 1px),\n    #ead3bd;\n  background-size: auto, 52px 52px, 52px 52px, auto;\n}\n.template-signal-noir {\n  --visual-bg: #0d0d0f;\n  --visual-paper: rgba(255, 184, 77, 0.08);\n  --visual-ink: #f7efe2;\n  --visual-muted: rgba(247, 239, 226, 0.68);\n  --visual-accent: #ffb84d;\n  background:\n    linear-gradient(135deg, rgba(255, 184, 77, 0.2), transparent 32%),\n    linear-gradient(90deg, rgba(247, 239, 226, 0.08) 1px, transparent 1px),\n    #0d0d0f;\n  font-family: Georgia, \"Times New Roman\", serif;\n}\n\n.deck-error {\n  margin: 80px auto;\n  max-width: 640px;\n  padding: 28px 32px;\n  border: 1px solid var(--line);\n  border-radius: 18px;\n  background: var(--paper);\n  box-shadow: var(--shadow);\n  font-size: 18px;\n  line-height: 1.6;\n}\n\n@media (max-width: 820px) {\n  .deck {\n    width: min(100vw, 100%);\n    padding-left: 34px;\n  }\n  .slide {\n    padding: 48px 24px 120px;\n  }\n}\n\n/* ---- runtime chrome: anchor navigation ---- */\n\n.anchor-nav {\n  position: fixed;\n  right: 10px;\n  top: 50%;\n  z-index: 20;\n  transform: translateY(-50%);\n  display: flex;\n  flex-direction: column;\n  align-items: center;\n  gap: 12px;\n  padding: 16px 0;\n  width: 40px;\n  border-radius: 20px;\n  background: rgba(0, 0, 0, 0.5);\n  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22), inset 0 0 0 1px rgba(255, 255, 255, 0.08);\n  -webkit-backdrop-filter: blur(12px);\n  backdrop-filter: blur(12px);\n  opacity: 0.86;\n  transition: background 220ms ease, box-shadow 220ms ease, opacity 220ms ease, transform 220ms ease;\n}\n\n.anchor-nav:hover,\n.anchor-nav:focus-within {\n  transform: translateY(-50%) translateX(-2px);\n  background: rgba(0, 0, 0, 0.66);\n  box-shadow: 0 14px 38px rgba(0, 0, 0, 0.32), inset 0 0 0 1px rgba(255, 255, 255, 0.14);\n  opacity: 1;\n}\n\n.anchor-item {\n  position: relative;\n  z-index: 1;\n  min-height: 24px;\n  --anchor-dot-color: var(--accent);\n  --anchor-dot-rgb: var(--accent-rgb);\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  width: 100%;\n  color: rgba(255, 255, 255, 0.7);\n  text-decoration: none;\n  cursor: pointer;\n}\n\n.anchor-dot {\n  position: relative;\n  width: 10px;\n  height: 10px;\n  border-radius: 999px;\n  background: var(--anchor-dot-color);\n  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12), 0 5px 14px rgba(var(--anchor-dot-rgb), 0.28);\n  transition: width 180ms ease, height 180ms ease, background 180ms ease, box-shadow 180ms ease, transform 180ms ease;\n}\n\n.anchor-dot::after {\n  content: \"\";\n  position: absolute;\n  inset: -4px;\n  border-radius: inherit;\n  border: 1px solid rgba(var(--anchor-dot-rgb), 0);\n  opacity: 0;\n  pointer-events: none;\n}\n\n.anchor-item:hover .anchor-dot {\n  transform: scale(1.3);\n  box-shadow: 0 0 0 4px rgba(var(--anchor-dot-rgb), 0.14), 0 7px 18px rgba(var(--anchor-dot-rgb), 0.34);\n}\n\n.anchor-item:not(.active) {\n  --anchor-dot-color: #f4a63a;\n  --anchor-dot-rgb: 244, 166, 58;\n}\n\n.anchor-item.active .anchor-dot {\n  width: 12px;\n  height: 28px;\n  background: var(--anchor-dot-color);\n  box-shadow: 0 0 0 6px rgba(var(--accent-rgb), 0.24), 0 10px 24px rgba(var(--accent-rgb), 0.38), inset 0 1px 4px rgba(255, 255, 255, 0.45);\n  animation: anchor-breathe 2.6s ease-in-out infinite;\n}\n\n.anchor-item.active .anchor-dot::after {\n  inset: -6px;\n  border-color: rgba(var(--accent-rgb), 0.26);\n  animation: anchor-edge-spread 2.6s ease-out infinite;\n}\n\n.anchor-label {\n  position: absolute;\n  right: 45px;\n  top: 50%;\n  transform: translateY(-50%);\n  max-width: 0;\n  padding: 0;\n  overflow: hidden;\n  white-space: normal;\n  line-height: 1.35;\n  opacity: 0;\n  pointer-events: none;\n  border-radius: 12px;\n  background: rgba(18, 20, 28, 0.82);\n  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);\n  color: rgba(255, 255, 255, 0.92);\n  font-size: 12px;\n  font-weight: 760;\n  -webkit-backdrop-filter: blur(12px);\n  backdrop-filter: blur(12px);\n  transition: opacity 160ms ease, max-width 160ms ease, padding 160ms ease;\n}\n\n.anchor-item:hover .anchor-label,\n.anchor-item:focus-visible .anchor-label {\n  width: max-content;\n  max-width: min(420px, calc(100vw - 120px));\n  padding: 9px 14px;\n  opacity: 1;\n}\n\n@keyframes anchor-breathe {\n  0%,\n  100% {\n    box-shadow: 0 0 0 5px rgba(var(--accent-rgb), 0.18), 0 10px 24px rgba(var(--accent-rgb), 0.32), inset 0 1px 4px rgba(255, 255, 255, 0.42);\n    opacity: 0.94;\n  }\n  50% {\n    box-shadow: 0 0 0 11px rgba(var(--accent-rgb), 0.28), 0 13px 32px rgba(var(--accent-rgb), 0.46), inset 0 1px 5px rgba(255, 255, 255, 0.5);\n    opacity: 1;\n  }\n}\n\n@keyframes anchor-edge-spread {\n  0% {\n    opacity: 0.32;\n    transform: scale(0.82);\n  }\n  60%,\n  100% {\n    opacity: 0;\n    transform: scale(1.72);\n  }\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .anchor-item.active .anchor-dot,\n  .anchor-item.active .anchor-dot::after {\n    animation: none;\n  }\n}\n\n@media (max-width: 820px) {\n  .anchor-nav {\n    right: 8px;\n  }\n}\n\n/* ---- runtime chrome: keyboard shortcut bar ---- */\n\n.shortcut-bar {\n  position: fixed;\n  left: 0;\n  right: 0;\n  bottom: 0;\n  z-index: 30;\n  width: 100%;\n  max-width: 100%;\n  padding: 8px 22px;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  gap: 18px;\n  overflow-x: auto;\n  border: none;\n  border-top: 1px solid rgba(20, 24, 32, 0.08);\n  border-radius: 0;\n  background: rgba(255, 255, 255, 0.86);\n  box-shadow: 0 -4px 18px rgba(20, 24, 32, 0.08);\n  color: #151515;\n  -webkit-backdrop-filter: blur(16px);\n  backdrop-filter: blur(16px);\n  opacity: 0.9;\n  transition: opacity 220ms ease, background 220ms ease;\n}\n\n.shortcut-bar:hover,\n.shortcut-bar:focus-within {\n  opacity: 1;\n  background: rgba(255, 255, 255, 0.94);\n}\n\n.shortcut {\n  display: inline-flex;\n  align-items: center;\n  gap: 7px;\n  color: rgba(21, 21, 21, 0.64);\n  font-size: 11px;\n  font-weight: 650;\n  white-space: nowrap;\n}\n\nkbd {\n  min-width: 20px;\n  height: 18px;\n  padding: 0 7px;\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  border: 1px solid rgba(20, 24, 32, 0.1);\n  border-bottom-color: rgba(20, 24, 32, 0.16);\n  border-radius: 6px;\n  background: rgba(248, 249, 251, 0.95);\n  box-shadow: 0 1px 4px rgba(20, 24, 32, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.96);\n  color: #151515;\n  font: 700 10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;\n  line-height: 1;\n  text-align: center;\n}\n\n.plus {\n  margin: 0 -2px;\n  color: rgba(21, 21, 21, 0.42);\n  font-size: 10px;\n  font-weight: 800;\n}\n\n.or {\n  width: 3px;\n}");

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

  function requireObject(data, key) {
    const value = data[key];
    if (!isObject(value)) {
      throw new Error("'" + key + "' must be an object");
    }
    return value;
  }

  function slugify(value, fallback) {
    const text = String(value == null ? "" : value)
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return text || fallback;
  }

  function joinHtml(parts) {
    return parts.filter(Boolean).join("\n");
  }

  function pad(index) {
    return String(index).padStart(2, "0");
  }

  /* ---- shared content fragments ---- */

  function listHtml(items) {
    return "<ul>" + asList(items).map((item) => "<li>" + htmlEscape(item) + "</li>").join("") + "</ul>";
  }

  function tagRow(tags) {
    const chips = asList(tags).map((tag) => "<span>" + htmlEscape(tag) + "</span>");
    return chips.length ? '<div class="tag-row">' + chips.join("\n") + "</div>" : "";
  }

  function cardHtml(item) {
    return '<article class="card"><h3>' + htmlEscape(item.title) + "</h3><p>" + htmlEscape(item.body) + "</p></article>";
  }

  function metricHtml(metric) {
    return '<article class="metric"><strong>' + htmlEscape(metric.value) + "</strong><span>" + htmlEscape(metric.label) + "</span></article>";
  }

  function visualCardHtml(item) {
    const label = item.label ? '<span class="eyebrow">' + htmlEscape(item.label) + "</span>" : "";
    return '<article class="card visual-card">' + label + "<h3>" + htmlEscape(item.title) + "</h3><p>" + htmlEscape(item.body) + "</p></article>";
  }

  function visualFigureHtml(item) {
    if (item && item.src) {
      return (
        '<figure class="image-frame"><img src="' + htmlEscape(item.src) + '" alt="' +
        htmlEscape(item.alt || item.title || "Template image") + '"><figcaption>' + htmlEscape(item.caption || item.title || "") + "</figcaption></figure>"
      );
    }
    return '<div class="visual-placeholder">' + htmlEscape((item && (item.caption || item.title)) || "Image / media frame") + "</div>";
  }

  /* ---- source material ---- */

  function trim(value, limit) {
    const text = String(value).split(/\s+/).join(" ").trim();
    const max = limit || 280;
    return text.length <= max ? text : text.slice(0, max - 1) + "...";
  }

  function renderImageSource(source) {
    return (
      '<figure class="source-card source-image">' +
      '<img src="' + htmlEscape(source.src) + '" alt="' + htmlEscape(source.alt || "Slide source image") + '">' +
      "<figcaption>" + htmlEscape(source.caption || "Image source") + "</figcaption>" +
      "</figure>"
    );
  }

  function renderArticleSource(source) {
    return (
      '<article class="source-card">' +
      '<span class="eyebrow">Article</span>' +
      '<h3><a href="' + htmlEscape(source.url || "#") + '" target="_blank" rel="noreferrer">' +
      htmlEscape(source.title || "Article") + "</a></h3>" +
      "<p>" + htmlEscape(source.summary) + "</p>" +
      "</article>"
    );
  }

  function renderDocumentSource(source) {
    const body = typeof source.body === "string" && source.body.trim() ? trim(source.body) : "";
    return (
      '<article class="source-card">' +
      '<span class="eyebrow">Document</span>' +
      "<h3>" + htmlEscape(source.title || "Document") + "</h3>" +
      "<p>" + htmlEscape(body) + "</p>" +
      "</article>"
    );
  }

  function renderSource(source) {
    if (source.type === "image") return renderImageSource(source);
    if (source.type === "article") return renderArticleSource(source);
    return renderDocumentSource(source);
  }

  function renderSources(data) {
    const sources = asList(data.sources).filter(isObject);
    if (!sources.length) return "";
    return '<div class="source-grid">' + sources.map(renderSource).join("\n") + "</div>";
  }

  /* ---- template renderers (one independent page per slide) ---- */

  function renderNarrativeArticle(data) {
    const article = requireObject(data, "article");
    const slides = [
      {
        id: "opening",
        title: String(article.title || "Untitled article"),
        kicker: "Overview",
        body: joinHtml(['<p class="lede">' + htmlEscape(article.summary) + "</p>", tagRow(article.tags)]),
      },
    ];
    asList(article.sections).forEach((section, position) => {
      if (!isObject(section)) return;
      const index = position + 1;
      const title = String(section.heading || "Section " + index);
      const quote = section.quote ? "<blockquote>" + htmlEscape(section.quote) + "</blockquote>" : "";
      const paragraphs = asList(section.paragraphs).map((text) => "<p>" + htmlEscape(text) + "</p>");
      slides.push({
        id: slugify(title, "section-" + index),
        title: title,
        kicker: pad(index),
        body: joinHtml([quote].concat(paragraphs)),
      });
    });
    const sourcesHtml = renderSources(data);
    if (sourcesHtml) {
      slides.push({ id: "sources", title: "Source material", kicker: "Appendix", body: sourcesHtml });
    }
    return slides;
  }

  function renderResearchReport(data) {
    const report = requireObject(data, "report");
    const metricCards = asList(report.metrics).filter(isObject).map(metricHtml);
    const slides = [
      {
        id: "summary",
        title: String(report.title || "Research report"),
        kicker: "Brief",
        body: joinHtml(['<p class="lede">' + htmlEscape(report.summary) + "</p>", '<div class="metric-grid">' + joinHtml(metricCards) + "</div>"]),
      },
    ];
    asList(report.findings).forEach((finding, position) => {
      if (!isObject(finding)) return;
      const index = position + 1;
      const title = String(finding.title || "Finding " + index);
      const body =
        '<div class="split"><div>' + listHtml(finding.evidence) + "</div><aside>" + htmlEscape(finding.recommendation) + "</aside></div>";
      slides.push({ id: slugify(title, "finding-" + index), title: title, kicker: "Finding " + index, body: body });
    });
    const timeline = asList(report.timeline).filter(isObject);
    if (timeline.length) {
      const rows = timeline.map(
        (item) => "<li><strong>" + htmlEscape(item.date) + "</strong><span>" + htmlEscape(item.event) + "</span></li>",
      );
      slides.push({ id: "timeline", title: "Research timeline", kicker: "Method", body: '<ol class="timeline">' + rows.join("\n") + "</ol>" });
    }
    const sourcesHtml = renderSources(data);
    if (sourcesHtml) {
      slides.push({ id: "references", title: "References", kicker: "Source", body: sourcesHtml });
    }
    return slides;
  }

  function renderProductLaunch(data) {
    const product = requireObject(data, "product");
    const market = requireObject(data, "market");
    const launch = requireObject(data, "launch");
    const pillars = asList(product.pillars).filter(isObject).map(cardHtml);
    const phases = asList(launch.phases).filter(isObject).map(cardHtml);
    return [
      {
        id: "product",
        title: String(product.name || "Product launch"),
        kicker: "Launch",
        body: joinHtml(['<p class="lede">' + htmlEscape(product.tagline) + "</p>", '<div class="statement">' + htmlEscape(product.positioning) + "</div>"]),
      },
      {
        id: "market",
        title: "Market position",
        kicker: "Context",
        body: '<div class="split"><div>' + listHtml(market.signals) + "</div><aside>" + htmlEscape(market.opportunity) + "</aside></div>",
      },
      { id: "features", title: "Product pillars", kicker: "Value", body: '<div class="card-grid">' + joinHtml(pillars) + "</div>" },
      { id: "launch-plan", title: "Launch plan", kicker: "Execution", body: '<div class="process-grid">' + joinHtml(phases) + "</div>" },
    ];
  }

  function renderImageGallery(data) {
    const gallery = requireObject(data, "gallery");
    const slides = [
      {
        id: "gallery-intro",
        title: String(gallery.title || "Gallery"),
        kicker: "Gallery",
        body: '<p class="lede">' + htmlEscape(gallery.description) + "</p>",
      },
    ];
    asList(gallery.images).forEach((image, position) => {
      if (!isObject(image)) return;
      const index = position + 1;
      const title = String(image.title || "Image " + index);
      const body =
        '<figure class="image-frame"><img src="' + htmlEscape(image.src) + '" alt="' +
        htmlEscape(image.alt || image.title || "Gallery image") + '"><figcaption>' + htmlEscape(image.caption) + "</figcaption></figure>";
      slides.push({ id: slugify(title, "image-" + index), title: title, kicker: "Frame " + index, body: body });
    });
    return slides;
  }

  function renderWorkshop(data) {
    const workshop = requireObject(data, "workshop");
    const slides = [
      {
        id: "workshop",
        title: String(workshop.title || "Workshop"),
        kicker: "Session",
        body:
          '<p class="lede">' + htmlEscape(workshop.goal) + "</p>" +
          '<div class="statement">' + htmlEscape(workshop.audience) + " · " + htmlEscape(workshop.duration) + "</div>",
      },
    ];
    const agenda = asList(workshop.agenda);
    if (agenda.length) {
      const rows = agenda.map((item) => "<li>" + htmlEscape(item) + "</li>");
      slides.push({ id: "agenda", title: "Agenda", kicker: "Plan", body: '<ol class="agenda-list">' + rows.join("\n") + "</ol>" });
    }
    asList(workshop.exercises).forEach((exercise, position) => {
      if (!isObject(exercise)) return;
      const index = position + 1;
      const title = String(exercise.title || "Exercise " + index);
      const body = '<div class="split"><div>' + listHtml(exercise.steps) + "</div><aside>" + htmlEscape(exercise.outcome) + "</aside></div>";
      slides.push({ id: slugify(title, "exercise-" + index), title: title, kicker: "Exercise " + index, body: body });
    });
    return slides;
  }

  /* ---- visual template pack inspired by beautiful-html-templates ---- */

  const VISUAL_TEMPLATE_DEFINITIONS = {
    "soft-editorial": {
      name: "Soft Editorial",
      family: "editorial",
      kicker: "Soft Editorial",
      accent: "sage, blush, and lemon",
    },
    "editorial-forest": {
      name: "Editorial Forest",
      family: "editorial",
      kicker: "Forest Review",
      accent: "forest green and dusty pink",
    },
    "pin-and-paper": {
      name: "Pin & Paper",
      family: "paper",
      kicker: "Pinned Notes",
      accent: "paper texture and handwritten marks",
    },
    "sakura-chroma": {
      name: "Sakura Chroma",
      family: "chroma",
      kicker: "Chroma Package",
      accent: "diagonal ribbons and spec checks",
    },
    "stencil-tablet": {
      name: "Stencil & Tablet",
      family: "artifact",
      kicker: "Field Artifact",
      accent: "stencil forms and earth palette",
    },
    "cobalt-grid": {
      name: "Cobalt Grid",
      family: "grid",
      kicker: "Cobalt Bulletin",
      accent: "graph paper and cobalt rules",
    },
    vellum: {
      name: "Vellum",
      family: "dark-editorial",
      kicker: "Vellum Notes",
      accent: "navy canvas and warm serif",
    },
    "emerald-editorial": {
      name: "Emerald Editorial",
      family: "magazine",
      kicker: "Emerald Masthead",
      accent: "emerald, navy, and double rules",
    },
    "neo-grid-bold": {
      name: "Neo-Grid Bold",
      family: "brutalist",
      kicker: "Neo Grid",
      accent: "neon yellow blocks and strict grid",
    },
    "editorial-tri-tone": {
      name: "Editorial Tri-Tone",
      family: "tri-tone",
      kicker: "Tri-Tone",
      accent: "dusty pink, mustard, and burgundy",
    },
    "creative-mode": {
      name: "Creative Mode",
      family: "creative",
      kicker: "Creative Mode",
      accent: "multi-color art direction",
    },
    monochrome: {
      name: "Monochrome",
      family: "mono",
      kicker: "Monochrome",
      accent: "ivory ledger and black type",
    },
    "peoples-platform": {
      name: "People's Platform",
      family: "poster",
      kicker: "Block & Bold",
      accent: "activist poster blocks",
    },
    "pink-script": {
      name: "Pink Script",
      family: "night",
      kicker: "After Hours",
      accent: "black canvas and hot pink",
    },
    "8-bit-orbit": {
      name: "8-Bit Orbit",
      family: "pixel",
      kicker: "Orbit Console",
      accent: "pixel neon arcade",
    },
    "block-frame": {
      name: "BlockFrame",
      family: "frame",
      kicker: "BlockFrame",
      accent: "chunky borders and pastel blocks",
    },
    "biennale-yellow": {
      name: "Biennale Yellow",
      family: "biennale",
      kicker: "Biennale",
      accent: "solar yellow and parchment",
    },
    "blue-professional": {
      name: "Blue Professional",
      family: "professional",
      kicker: "Professional",
      accent: "cream paper and electric blue",
    },
    "bold-poster": {
      name: "Bold Poster",
      family: "bold",
      kicker: "Poster",
      accent: "massive display type and red mark",
    },
    broadside: {
      name: "Broadside",
      family: "broadside",
      kicker: "Broadside",
      accent: "dark newspaper and fire orange",
    },
    capsule: {
      name: "Capsule",
      family: "capsule",
      kicker: "Capsule",
      accent: "pill cards and pastel pop",
    },
    cartesian: {
      name: "Cartesian",
      family: "cartesian",
      kicker: "Cartesian",
      accent: "warm-neutral classical grid",
    },
    coral: {
      name: "Coral",
      family: "coral",
      kicker: "Coral",
      accent: "cream, coral, and near-black",
    },
    "daisy-days": {
      name: "Daisy Days",
      family: "daisy",
      kicker: "Daisy Days",
      accent: "pastel education cards",
    },
    "ink-wash-scroll": {
      name: "Ink Wash Scroll",
      family: "ink",
      kicker: "Ink Scroll",
      accent: "rice paper, ink wash gradients, and cinnabar seals",
    },
    "lunar-terminal": {
      name: "Lunar Terminal",
      family: "terminal",
      kicker: "Lunar Console",
      accent: "moonlit terminal panels and cyan orbital traces",
    },
    "glass-atelier": {
      name: "Glass Atelier",
      family: "glass",
      kicker: "Atelier",
      accent: "translucent glass cards, lavender light, and precise studio grids",
    },
    "clay-diagram": {
      name: "Clay Diagram",
      family: "diagram",
      kicker: "Clay Map",
      accent: "warm clay surfaces, blueprint marks, and structured diagram blocks",
    },
    "signal-noir": {
      name: "Signal Noir",
      family: "noir",
      kicker: "Signal Desk",
      accent: "black newsroom canvas, amber signals, and sharp editorial contrast",
    },
  };

  function defaultVisualPages(definition) {
    return [
      {
        kind: "cover",
        title: definition.name,
        kicker: definition.kicker,
        body: "A deck-driven template inspired by " + definition.accent + ".",
      },
      {
        kind: "contents",
        title: "Template structure",
        kicker: "Index",
        cards: [
          { label: "01", title: "Single deck", body: "The HTML owns one deck container and embedded JSON data." },
          { label: "02", title: "Runtime chrome", body: "Anchor navigation and keyboard shortcuts are built by the shared runtime." },
          { label: "03", title: "Visual system", body: "The renderer maps content into a template-specific structure and theme." },
        ],
      },
      {
        kind: "statement",
        title: "Structure first, theme second.",
        kicker: "Principle",
        body: "The template changes layout hierarchy, visual rhythm, and decorative language without forking navigation behavior.",
      },
      {
        kind: "metrics",
        title: "Verification targets",
        kicker: "Quality",
        metrics: [
          { value: "1", label: "deck container" },
          { value: "0", label: "custom nav copies" },
          { value: "20+", label: "visual templates" },
        ],
      },
    ];
  }

  function visualSlideClass(template, kind) {
    return "visual-slide template-" + slugify(template, "visual") + " visual-" + slugify(kind, "page");
  }

  function renderVisualBody(page, definition) {
    const kind = String(page.kind || "content");
    const cards = asList(page.cards || page.items).filter(isObject);
    const metrics = asList(page.metrics).filter(isObject);
    const steps = asList(page.steps || page.timeline).filter(isObject);
    const image = isObject(page.image) ? page.image : page;

    if (kind === "cover") {
      return joinHtml([
        '<p class="lede">' + htmlEscape(page.body || page.subtitle || "") + "</p>",
        '<div class="visual-accent">' + htmlEscape(definition.accent) + "</div>",
      ]);
    }
    if (kind === "contents" || kind === "cards") {
      return '<div class="card-grid visual-grid">' + joinHtml(cards.map(visualCardHtml)) + "</div>";
    }
    if (kind === "statement" || kind === "quote") {
      return joinHtml([
        '<div class="statement">' + htmlEscape(page.body || page.quote || page.title) + "</div>",
        page.attribution ? '<p class="visual-attribution">' + htmlEscape(page.attribution) + "</p>" : "",
      ]);
    }
    if (kind === "metrics") {
      return '<div class="metric-grid visual-metrics">' + joinHtml(metrics.map(metricHtml)) + "</div>";
    }
    if (kind === "process") {
      return '<div class="process-grid visual-process">' + joinHtml(cards.map(visualCardHtml)) + "</div>";
    }
    if (kind === "image") {
      return visualFigureHtml(image);
    }
    if (kind === "timeline") {
      const rows = steps.map((item) => "<li><strong>" + htmlEscape(item.date || item.label) + "</strong><span>" + htmlEscape(item.event || item.body) + "</span></li>");
      return '<ol class="timeline visual-timeline">' + rows.join("\n") + "</ol>";
    }
    return joinHtml(['<p class="lede">' + htmlEscape(page.body || "") + "</p>", cards.length ? '<div class="card-grid visual-grid">' + joinHtml(cards.map(visualCardHtml)) + "</div>" : ""]);
  }

  function renderVisualTemplate(data, template) {
    const definition = VISUAL_TEMPLATE_DEFINITIONS[template];
    const deckData = isObject(data.deck) ? data.deck : {};
    const pages = asList(deckData.pages || deckData.slides).filter(isObject);
    const sourcePages = pages.length ? pages : defaultVisualPages(definition);
    return sourcePages.map((page, position) => {
      const index = position + 1;
      const title = String(page.title || definition.name + " " + index);
      const kind = String(page.kind || "content");
      return {
        id: slugify(page.id || title, "visual-" + index),
        title: title,
        kicker: String(page.kicker || definition.kicker || pad(index)),
        body: renderVisualBody(page, definition),
        className: visualSlideClass(template, kind),
      };
    });
  }

  const TEMPLATE_REGISTRY = {
    "narrative-article": renderNarrativeArticle,
    "research-report": renderResearchReport,
    "product-launch": renderProductLaunch,
    "image-gallery": renderImageGallery,
    workshop: renderWorkshop,
  };

  Object.keys(VISUAL_TEMPLATE_DEFINITIONS).forEach((template) => {
    TEMPLATE_REGISTRY[template] = (data) => renderVisualTemplate(data, template);
  });

  function inferTemplateFromPath() {
    const path = String((window.location && window.location.pathname) || "");
    const parts = path.split("/").filter(Boolean);
    const index = parts.lastIndexOf("templates");
    return index >= 0 && parts[index + 1] ? parts[index + 1] : "";
  }

  function resolveTemplateName(data) {
    return String(data.template || inferTemplateFromPath()).trim();
  }

  function isVisualTemplate(template) {
    return Boolean(VISUAL_TEMPLATE_DEFINITIONS[template]);
  }

  function renderTemplate(data, template) {
    const renderer = TEMPLATE_REGISTRY[template];
    if (!renderer) {
      const choices = Object.keys(TEMPLATE_REGISTRY).sort().join(", ");
      throw new Error("Unknown template '" + template + "'. Available templates: " + choices);
    }
    const slides = renderer(data);
    if (!slides.length) {
      throw new Error("Template '" + template + "' produced no slides");
    }
    return slides;
  }

  function resolveLanguage(data) {
    const requested = String(data.language || data.locale || document.documentElement.lang || "zh-CN").toLowerCase();
    return requested.indexOf("en") === 0 ? "en" : "zh";
  }

  function applyDocumentLanguage(data, language) {
    const requested = String(data.language || data.locale || "").trim();
    document.documentElement.lang = requested || (language === "en" ? "en" : "zh-CN");
  }

  /* ---- DOM construction ---- */

  function buildSlides(deck, slides) {
    slides.forEach((slide, position) => {
      const section = document.createElement("section");
      section.className = ["slide", slide.className].filter(Boolean).join(" ");
      section.id = slide.id;
      section.setAttribute("data-slide-index", String(position + 1));
      section.innerHTML =
        '<div class="slide-kicker">' + htmlEscape(slide.kicker) + "</div>" +
        "<h1>" + htmlEscape(slide.title) + "</h1>" +
        '<div class="slide-body">' + slide.body + "</div>";
      deck.appendChild(section);
    });
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function showError(message) {
    const main = document.querySelector(".deck") || document.body;
    main.innerHTML = '<div class="deck-error"><strong>Unable to render deck.</strong><br>' + htmlEscape(message) + "</div>";
  }

  /* ---- built-in runtime chrome ---- */

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

  runtime.buildAnchorNav = buildAnchorNav;
  runtime.buildShortcutBar = buildShortcutBar;

  /* ---- bootstrap ---- */

  function init() {

    const dataScript = document.getElementById("deck-data");
    if (!dataScript) {
      showError("Missing deck data script (#deck-data).");
      return;
    }

    let data;
    try {
      data = JSON.parse(dataScript.textContent);
    } catch (error) {
      showError("Invalid deck JSON: " + error.message);
      return;
    }

    let slides;
    const template = resolveTemplateName(data);
    try {
      slides = renderTemplate(data, template);
    } catch (error) {
      showError(error.message);
      return;
    }

    const language = resolveLanguage(data);
    applyDocumentLanguage(data, language);

    const title = String(data.title || slides[0].title);
    document.title = title;

    const deck = document.querySelector(".deck");
    deck.setAttribute("aria-label", title);
    deck.setAttribute("data-template", template);
    deck.setAttribute("data-visual-template", isVisualTemplate(template) ? "true" : "false");
    buildSlides(deck, slides);

    const sections = Array.prototype.slice.call(deck.querySelectorAll(".slide"));

    const scrollSwitchThreshold = 260;
    const scrollMaxDrag = 26;
    const scrollReleaseMs = 140;
    const scrollLockMs = 520;
    let activeIndex = 0;
    let scrollDelta = 0;
    let scrollReleaseTimer = 0;
    let scrollLockUntil = 0;

    function resetScrollDrag() {
      scrollDelta = 0;
      window.clearTimeout(scrollReleaseTimer);
      deck.style.setProperty("--scroll-drag", "0px");
    }

    function setScrollDrag(delta) {
      const progress = Math.min(Math.abs(delta) / scrollSwitchThreshold, 1);
      const eased = 1 - Math.pow(1 - progress, 2);
      const offset = -Math.sign(delta) * scrollMaxDrag * eased;
      deck.style.setProperty("--scroll-drag", offset.toFixed(2) + "px");
    }

    function scheduleScrollRelease() {
      window.clearTimeout(scrollReleaseTimer);
      scrollReleaseTimer = window.setTimeout(resetScrollDrag, scrollReleaseMs);
    }

    function canMove(direction) {
      return direction > 0 ? activeIndex < sections.length - 1 : activeIndex > 0;
    }

    function show(index) {
      const nextIndex = clamp(index, 0, sections.length - 1);
      deck.setAttribute("data-transition", nextIndex < activeIndex ? "prev" : "next");
      activeIndex = nextIndex;
      sections.forEach((section, position) => section.classList.toggle("active", position === activeIndex));
      nav.setActiveIndex(activeIndex);
      window.scrollTo(0, 0);
      const id = sections[activeIndex].id;
      if (("#" + id) !== window.location.hash) {
        history.replaceState(null, "", "#" + id);
      }
    }

    function handleWheel(event) {
      if (event.ctrlKey) return;
      event.preventDefault();
      if (Date.now() < scrollLockUntil) return;
      const rawDelta = event.deltaY || -event.wheelDelta || 0;
      if (!rawDelta) return;

      const direction = rawDelta > 0 ? 1 : -1;
      if (scrollDelta && Math.sign(scrollDelta) !== direction) scrollDelta = 0;
      scrollDelta = clamp(scrollDelta + rawDelta, -scrollSwitchThreshold, scrollSwitchThreshold);
      setScrollDrag(scrollDelta);

      if (Math.abs(scrollDelta) < scrollSwitchThreshold) {
        scheduleScrollRelease();
        return;
      }

      resetScrollDrag();
      scrollLockUntil = Date.now() + scrollLockMs;
      if (canMove(direction)) {
        show(activeIndex + direction);
      }
    }

    function indexFromHash() {
      const id = window.location.hash.replace(/^#/, "");
      const found = sections.findIndex((section) => section.id === id);
      return found >= 0 ? found : 0;
    }

    function runAction(action) {
      if (action === "next") show(activeIndex + 1);
      else if (action === "prev") show(activeIndex - 1);
      else if (action === "home") show(0);
      else if (action === "end") show(sections.length - 1);
    }

    const nav = buildAnchorNav({ slides: slides }, {
      htmlEscape: htmlEscape,
      onSelect: (index) => show(index),
    });
    document.body.insertBefore(nav, deck);

    const shortcutBar = buildShortcutBar({
      language: data.language,
      locale: data.locale,
      shortcuts: data.shortcuts,
    }, {
      htmlEscape: htmlEscape,
      onAction: runAction,
    });
    document.body.appendChild(shortcutBar);

    window.addEventListener("wheel", handleWheel, { passive: false });
    window.addEventListener("hashchange", () => show(indexFromHash()));

    show(indexFromHash());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
