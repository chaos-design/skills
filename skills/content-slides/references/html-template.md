# HTML Presentation Template

Reference architecture for generating the slide deck. Every deck uses a fixed 16:9 stage: slides are authored at 1920×1080 and the whole stage scales to fit the window. Copy this structure, then fill in slides and theme.

## Table of Contents
1. Base HTML structure
2. Theme variables (`:root`)
3. Slide layout patterns
4. The `SlidePresentation` controller (full, working code)
5. Inline editing (optional, on by default)
6. Image pipeline (skip if no images)

---

## 1. Base HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Title</title>

    <!-- Fonts: Fontshare or Google Fonts — never system fonts. Match the chosen preset. -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=...&display=swap">

    <style>
        /* === THEME VARIABLES (see section 2) === */
        :root { /* ... */ }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* === PASTE THE ENTIRE CONTENTS OF viewport-base.css HERE === */

        /* === SLIDE LAYOUT (see section 3) === */
        .slide-content {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: var(--slide-padding);
            gap: var(--content-gap);
        }
        .slide-content.is-thin {
            justify-content: center;
            align-items: stretch;
        }
        .slide-content[data-layout-density="dense"] {
            --content-gap: 24px;
        }
        .slide-content[data-layout-density="dense"] h2 {
            font-size: calc(var(--heading-size) * 0.86);
            line-height: 1.1;
        }
        .slide-content[data-layout-density="dense"] p,
        .slide-content[data-layout-density="dense"] li {
            font-size: calc(var(--body-size) * 0.9);
            line-height: 1.32;
        }
        .slide-layout {
            width: 100%;
            min-height: 0;
            display: grid;
            gap: var(--content-gap);
            align-items: center;
        }
        .slide-layout.split {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .slide-layout.split.is-reversed {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .module-grid {
            width: 100%;
            display: grid;
            gap: var(--content-gap);
            align-items: stretch;
        }
        .module-grid[data-count="2"],
        .module-grid[data-count="4"] {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .module-grid[data-count="3"],
        .module-grid[data-count="6"] {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .module-grid > * {
            min-width: 0;
            height: 100%;
        }
        .slide:nth-of-type(odd) .slide-layout.split[data-alternate="auto"] .visual-panel {
            order: 2;
        }
        .slide:nth-of-type(even) .slide-layout.split[data-alternate="auto"] .visual-panel {
            order: -1;
        }
        .bounded-panel,
        .visual-panel,
        .text-panel {
            min-width: 0;
            min-height: 0;
            max-height: calc(1080px - (var(--slide-padding) * 2));
            overflow: hidden;
        }
        .bounded-copy {
            max-width: 1160px;
            overflow-wrap: anywhere;
        }
        .visual-panel figure {
            display: grid;
            gap: 18px;
            max-height: 100%;
        }
        .visual-panel img,
        .visual-panel svg {
            width: 100%;
            max-height: 700px;
            object-fit: contain;
        }
        .visual-panel figcaption {
            font-size: calc(var(--body-size) * 0.72);
            line-height: 1.38;
            color: var(--text-secondary, rgba(255, 255, 255, 0.72));
        }
        .visual-panel .image-source {
            margin-top: -8px;
            font-size: calc(var(--body-size) * 0.52);
            line-height: 1.25;
            color: var(--text-tertiary, color-mix(in srgb, var(--text-secondary, rgba(255, 255, 255, 0.72)) 68%, transparent));
        }
        .title-slide {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: var(--slide-padding);
            text-align: center;
        }
        .title-block {
            width: min(1320px, 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 28px;
            margin-inline: auto;
        }
        .title-slide h1 {
            max-width: 1200px;
        }
        .title-slide .subtitle {
            max-width: 980px;
            font-size: var(--subtitle-size);
            line-height: 1.28;
            color: var(--text-secondary, rgba(255, 255, 255, 0.78));
            text-wrap: balance;
        }

        /* Headings need breathing room because the global reset removes margins.
           The small vertical padding prevents tall Latin/CJK glyphs from clipping
           while the negative top margin keeps visual alignment tight. */
        .slide h1,
        .slide h2,
        .slide h3 {
            line-height: 1.08;
            padding-block: 0.08em 0.12em;
            margin-block: -0.08em 0;
            text-wrap: balance;
            color: var(--text-primary, #111);
        }
        .slide h1 {
            padding-block: 0.3em 0.20em;
            margin-block: -0.10em 0;
        }

        /* Links should be visibly interactive but still inherit the deck theme. */
        .slide a {
            color: var(--link-color, var(--accent, #00ffcc));
            text-decoration-line: underline;
            text-decoration-thickness: 0.08em;
            text-underline-offset: 0.16em;
            text-decoration-color: var(--link-underline, color-mix(in srgb, currentColor 55%, transparent));
            padding-inline: 0.05em;
            margin-inline: -0.05em;
            border-radius: 0.12em;
            overflow-wrap: anywhere;
            transition: color 160ms ease, background 160ms ease, text-decoration-color 160ms ease;
        }
        .slide a:visited { color: var(--link-visited, var(--link-color, var(--accent, #00ffcc))); }
        .slide a:hover,
        .slide a:focus-visible {
            color: var(--link-hover, var(--link-color, var(--accent, #00ffcc)));
            background: var(--link-hover-bg, color-mix(in srgb, currentColor 14%, transparent));
            text-decoration-color: currentColor;
            outline: none;
            box-shadow: 0 0 0 0.12em var(--link-focus-ring, color-mix(in srgb, currentColor 22%, transparent));
        }

        /*
         * Link URLs only when the slide expects the viewer to open them, such as source credits,
         * citations, references, and official docs:
         * <a href="https://example.com" target="_blank" rel="noopener noreferrer">https://example.com</a>
         * Article/source credits use:
         * 原文：<a href="https://example.com" target="_blank" rel="noopener">《Source Title》</a>
         * Use the original English source title inside 《》 when available; do not translate it.
         * Leave URLs in code, terminal commands, config snippets, placeholders, and illustrative
         * examples as plain text. Keep trailing punctuation outside any generated link.
         */

        .slide img {
            cursor: zoom-in;
        }

        /* Global image lightbox lives outside .deck-stage so it is not affected by stage scaling. */
        .image-lightbox {
            position: fixed;
            inset: 0;
            z-index: 2000;
            display: grid;
            place-items: center;
            padding: min(6vw, 96px);
            background:
                radial-gradient(circle at 50% 42%, rgba(255, 255, 255, 0.16), transparent 36%),
                linear-gradient(135deg, rgba(6, 10, 18, 0.72), rgba(18, 24, 38, 0.48));
            -webkit-backdrop-filter: blur(18px) saturate(1.2);
            backdrop-filter: blur(18px) saturate(1.2);
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            transition: opacity 220ms ease, visibility 220ms ease;
        }
        .image-lightbox.is-open {
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
        }
        .image-lightbox[hidden] { display: none; }
        .image-lightbox__panel {
            position: relative;
            display: grid;
            max-width: min(82vw, 1280px);
            max-height: 82vh;
            transform: translateY(18px) scale(0.985);
            transition: transform 220ms ease;
        }
        .image-lightbox.is-open .image-lightbox__panel {
            transform: translateY(0) scale(1);
        }
        .image-lightbox__image {
            display: block;
            width: auto;
            height: auto;
            max-width: min(82vw, 1280px);
            max-height: 78vh;
            object-fit: contain;
            border-radius: 18px;
            box-shadow: 0 30px 100px rgba(0, 0, 0, 0.48);
            background: rgba(255, 255, 255, 0.06);
        }
        .image-lightbox__close {
            position: absolute;
            top: -18px;
            right: -18px;
            width: 44px;
            height: 44px;
            border: 1px solid rgba(255, 255, 255, 0.32);
            border-radius: 999px;
            background: rgba(10, 14, 24, 0.72);
            color: #fff;
            cursor: pointer;
            font-size: 26px;
            line-height: 1;
            -webkit-backdrop-filter: blur(10px);
            backdrop-filter: blur(10px);
        }

        /* === ANIMATIONS === */
        .reveal {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity var(--duration-normal) var(--ease-out-expo),
                        transform var(--duration-normal) var(--ease-out-expo);
        }
        .slide.visible .reveal { opacity: 1; transform: translateY(0); }
        .slide.visible .reveal:nth-child(1) { transition-delay: 0.10s; }
        .slide.visible .reveal:nth-child(2) { transition-delay: 0.20s; }
        .slide.visible .reveal:nth-child(3) { transition-delay: 0.30s; }
        .slide.visible .reveal:nth-child(4) { transition-delay: 0.40s; }
        .slide.visible .reveal:nth-child(5) { transition-delay: 0.50s; }
        .slide.visible .reveal:nth-child(6) { transition-delay: 0.60s; }

        /* === DECK CHROME === */
        /* === BOTTOM CONTROL BAR === */
        .deck-controls-zone {
            position: fixed; left: 0; right: 0; bottom: 0; height: 70px;
            z-index: 1000; pointer-events: auto;
        }
        .deck-controls {
            position: absolute; left: 50%; bottom: 10px;
            transform: translateX(-50%) translateY(24px);
            display: flex; align-items: center; justify-content: center; gap: 10px;
            min-height: 40px; padding: 5px 8px; border-radius: 999px;
            background: var(--kbd-bar-bg, rgba(12, 16, 24, 0.74));
            border: 1px solid var(--chrome-border, rgba(255,255,255,0.18));
            box-shadow: 0 12px 30px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.08);
            -webkit-backdrop-filter: blur(14px);
            backdrop-filter: blur(14px);
            font: 700 13px var(--font-body); color: var(--kbd-text, rgba(255,255,255,0.88));
            opacity: 0;
            filter: blur(5px);
            transition: opacity 0.42s var(--ease-out-expo), transform 0.48s var(--ease-out-expo), filter 0.42s var(--ease-out-expo),
                        background 0.22s ease, border-color 0.22s ease, color 0.22s ease;
            width: max-content; max-width: min(92vw, 720px);
            will-change: opacity, transform, filter;
        }
        .deck-controls-zone:hover .deck-controls {
            opacity: 0.96;
            transform: translateX(-50%) translateY(0);
            filter: blur(0);
        }
        .deck-controls-zone.show-controls .deck-controls {
            opacity: 0.96;
            transform: translateX(-50%) translateY(0);
            filter: blur(0);
        }
        .deck-controls-zone:focus-within .deck-controls {
            opacity: 0.96;
            transform: translateX(-50%) translateY(0);
            filter: blur(0);
        }
        .deck-controls:focus {
            opacity: 0.96;
            transform: translateX(-50%) translateY(0);
            filter: blur(0);
        }
        .deck-page-controls,
        .deck-shortcuts { display: inline-flex; align-items: center; gap: 8px; white-space: nowrap; }
        .deck-page-btn {
            width: 28px; height: 28px; padding: 0; border: 0; border-radius: 0; cursor: pointer;
            display: inline-flex; align-items: center; justify-content: center;
            background: transparent; color: var(--kbd-key-text, #fff);
            transition: color 0.18s ease, opacity 0.18s ease, transform 0.18s ease;
        }
        .deck-page-btn svg { width: 20px; height: 20px; display: block; }
        .deck-page-btn:hover { color: var(--control-accent, var(--accent)); transform: scale(1.08); }
        .deck-page-btn:disabled { opacity: 0.38; cursor: default; }
        .deck-page-btn:disabled:hover { color: var(--kbd-key-text, #fff); transform: none; }
        .deck-page-status {
            min-width: 44px; text-align: center; font-variant-numeric: tabular-nums;
            color: var(--kbd-text, rgba(255,255,255,0.88));
        }
        .deck-control-separator {
            width: 1px; height: 22px; margin: 0 4px; background: var(--kbd-separator, rgba(255,255,255,0.18));
        }
        .shortcut-chip {
            display: inline-flex; align-items: center; gap: 8px; padding: 4px 6px 4px 12px;
            border-radius: 999px; background: transparent;
            color: var(--kbd-text, rgba(255,255,255,0.88));
            font-weight: 500;
            transition: background 0.18s ease, color 0.18s ease;
        }
        .shortcut-chip:hover { background: var(--kbd-bg, rgba(255,255,255,0.16)); }
        .shortcut-label { font-weight: 500; }
        .shortcut-keys { display: inline-flex; align-items: center; gap: 4px; }
        .deck-shortcuts kbd {
            font: 500 11px var(--font-body);
            min-width: 24px; padding: 4px 7px; text-align: center;
            border-radius: 7px; background: var(--kbd-bg, rgba(255,255,255,0.16));
            border: 1px solid var(--kbd-border, rgba(255,255,255,0.28));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 1px 3px rgba(0,0,0,0.16);
            color: var(--kbd-key-text, #fff); line-height: 1;
        }
        .shortcut-chip:hover kbd { background: color-mix(in srgb, var(--kbd-bg, rgba(255,255,255,0.16)) 72%, #fff); }
    </style>
</head>
<body>
    <div class="deck-viewport">
        <main class="deck-stage" id="deckStage">

            <!-- Title slide -->
            <section class="slide title-slide active" data-chrome="dark">
                <div class="title-block">
                    <h1 class="reveal">Article-theme main title</h1>
                    <p class="subtitle reveal">Optional subtitle or grounded personal framing · Source / author</p>
                </div>
            </section>

            <!-- Content slide -->
            <section class="slide" data-chrome="light">
                <div class="slide-content">
                    <h2 class="reveal">Slide Title</h2>
                    <ul>
                        <li class="reveal">Point one</li>
                        <li class="reveal">Point two</li>
                        <li class="reveal">Point three</li>
                    </ul>
                </div>
            </section>

            <!-- More slides... -->

        </main>
    </div>

    <!-- Bottom control bar: revealed only when hovering near the bottom edge -->
    <div class="deck-controls-zone">
        <div class="deck-controls" tabindex="0" aria-label="Slide controls">
            <div class="deck-page-controls" aria-label="Slide pagination">
                <button class="deck-page-btn" id="prevSlide" type="button" aria-label="Previous slide">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.5 4.5 8 12l7.5 7.5" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <span class="deck-page-status"><span id="currentSlide">1</span>/<span id="totalSlides">1</span></span>
                <button class="deck-page-btn" id="nextSlide" type="button" aria-label="Next slide">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 4.5 16 12l-7.5 7.5" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
            </div>
            <span class="deck-control-separator" aria-hidden="true"></span>
            <div class="deck-shortcuts" aria-label="Keyboard shortcuts">
                <span class="shortcut-chip"><span class="shortcut-label">下一页</span><span class="shortcut-keys"><kbd>Space</kbd><kbd>↓</kbd><kbd>→</kbd></span></span>
                <span class="shortcut-chip"><span class="shortcut-label">上一页</span><span class="shortcut-keys"><kbd>←</kbd><kbd>↑</kbd></span></span>
                <span class="shortcut-chip"><span class="shortcut-label">重置</span><span class="shortcut-keys"><kbd>R</kbd></span></span>
            </div>
        </div>
    </div>

    <div class="image-lightbox" id="imageLightbox" aria-modal="true" role="dialog" aria-label="图片放大视图" hidden>
        <div class="image-lightbox__panel">
            <button class="image-lightbox__close" id="imageLightboxClose" type="button" aria-label="关闭图片放大视图">×</button>
            <img class="image-lightbox__image" id="imageLightboxImage" alt="">
        </div>
    </div>

    <script>
        /* === SlidePresentation controller (see section 4) === */
    </script>
</body>
</html>
```

---

## 2. Theme Variables

Put everything stylistic in `:root` so the look changes in one place. Sizes are authored at the 1920×1080 stage scale (do NOT use clamp/responsive breakpoints inside slides — the stage scaling handles all screens).

```css
:root {
    /* Colors — from the chosen style preset */
    --bg-primary: #0a0f1c;
    --bg-secondary: #111827;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --accent: #00ffcc;
    --accent-glow: rgba(0, 255, 204, 0.3);
    --slide-bg: var(--bg-primary);   /* what fills each .slide */
    --stage-bg: #000;                /* letterbox color around the stage */

    /* Deck chrome (bottom controls + keyboard hints) — generated from the chosen theme */
    --control-accent: var(--accent);
    --chrome-border: color-mix(in srgb, var(--text-primary) 18%, transparent);
    --kbd-bar-bg: rgba(12, 16, 24, 0.74);    /* keyboard hint bar fill */
    --kbd-text: rgba(255, 255, 255, 0.88);   /* keyboard hint label text */
    --kbd-bg: rgba(255, 255, 255, 0.16);     /* keyboard hint key fill */
    --kbd-border: rgba(255, 255, 255, 0.28); /* keyboard hint key border */
    --kbd-separator: rgba(255, 255, 255, 0.18);
    --kbd-key-text: #ffffff;
    --link-color: var(--accent);
    --link-visited: var(--link-color);
    --link-hover: var(--link-color);
    --link-hover-bg: color-mix(in srgb, var(--link-color) 14%, transparent);
    --link-underline: color-mix(in srgb, var(--link-color) 55%, transparent);
    --link-focus-ring: color-mix(in srgb, var(--link-color) 22%, transparent);
    --module-radius: 20px;          /* cards/panels; adjust per preset, 0 for intentionally sharp styles */

    /* Typography — authored at 1920×1080 */
    --font-display: 'Clash Display', sans-serif;
    --font-body: 'Satoshi', sans-serif;
    --title-size: 112px;
    --heading-size: 64px;
    --subtitle-size: 34px;
    --body-size: 28px;

    /* Spacing — authored at 1920×1080 */
    --slide-padding: 96px;
    --content-gap: 32px;

    /* Animation */
    --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
    --duration-normal: 0.6s;
}
```

The bottom controls use one fixed chrome palette for the whole deck. Define that palette in
`:root` from the chosen deck theme and keep it stable while slides change:

Do not update `--kbd-*`, `--chrome-border`, or `--control-accent` from individual slide
`data-chrome` attributes. If a deck mixes light and dark slides, choose a single bar palette with
enough contrast over the stage and keep the controls visually consistent across navigation.

---

## 3. Slide Layout Patterns

Pick the layout that fits the content. All are authored at 1920×1080.

- **Title** — `h1` (`--title-size`) + optional subtitle/source inside a centered `.title-block`. The first slide's main title must be related to the article's actual theme or central thesis, not a generic deck label, filename, or raw URL slug. If helpful, add a subtitle or concise grounded personal framing line, but keep it faithful to the source. Place the title block in the middle of the stage by default.
- **Bullet list** — `h2` heading + `<ul>` of `.reveal` items. Keep to density-mode limits (≤3 low, ≤8 high).
- **Statement / quote** — one large centered line; use for a punchy idea or pulled quote with attribution.
- **Two-column** — `display:grid; grid-template-columns: repeat(2, minmax(0, 1fr))` for text + image, or compare/contrast. When two peer modules appear on one slide, both columns must take equal width and align to the same top/bottom rhythm; do not leave one side empty.
- **Alternating split layout** — use `.slide-layout.split` with `data-alternate="auto"` when several adjacent slides repeat text + visual modules. Odd/even slides may mirror the visual panel to create rhythm, but override with `.is-reversed` or explicit order when source reading order or image legibility matters more. Alternation changes order only; it must not make one column wider than the other or create a blank right side.
- **Stat / hero number** — one giant number (`font-size: 240px`) + a short caption.
- **Equal module grid** — when a slide has multiple peer modules, divide the available width evenly. Use `.module-grid[data-count="2"]`, `[data-count="3"]`, `[data-count="4"]`, or `[data-count="6"]` where practical. Two modules use 1×2, three use 1×3, four use 2×2, and six use 3×2. For five modules, use a balanced 3+2 composition with the second row centered, or split into two slides if equal alignment would be awkward.
- **Card grid** — use a centered grid for 3–6 parallel items. Avoid a fixed `repeat(3, 1fr)` when the item count is even: 2 and 4 cards must be centered as balanced two-column groups, and 6 cards may use a balanced 3×2 grid. For 4 cards, prefer `grid-template-columns: repeat(2, minmax(0, 1fr)); max-width: <comfortable width>; margin-inline: auto;` so the layout becomes 2×2 instead of 3+1 with a left-aligned orphan. Never allow an even number of modules to leave the final row half-empty or left-biased.
- **Thin content slide** — when a slide has only a title plus one short paragraph, one quote, one image with a short caption, or no more than three concise bullets, add `is-thin` to `.slide-content` and compose the content around the vertical center of the canvas. Use centered or balanced internal modules as appropriate, but keep body text readable and avoid excess top whitespace.
- **Image with optional caption** — do not add a standalone description block for generated slides. Pair meaningful images with a concise, professional caption only when it improves comprehension or source attribution. The visual must match the slide's title/body topic directly; otherwise make the slide text-only or move the visual to a better slide. Use editorial phrasing such as “图示展示了……的结构关系”, “该截图用于说明……的界面状态”, or “图中标注强调……”. Do not use casual formulas like “对应来源图 / 来源图如下 / 相关配图 / 这张图说什么 / 做什么 / 对应什么”, and do not anthropomorphize images as if they are speaking or acting.
- **Complete content slide** — a slide must not consist of a single word, bare acronym, orphan section label, or unfinished fragment. Fold isolated terms into an explanatory slide. If a source section is too large, split it into multiple complete slides with specific part titles rather than ending with “...”, “etc.”, “continued”, or an unfinished bullet.
- **Overflow prevention** — keep text modules in `.bounded-panel` / `.bounded-copy` and images in `.visual-panel`. Use `data-layout-density="dense"` only for moderate compression; if meaningful content still exceeds the visible area, split the slide. Do not use scroll containers, hidden overflow as a content strategy, unreadably small type, or cropped screenshots/diagrams.
- **Professional composition** — choose the layout that makes the slide's argument easiest to read: align text/image baselines, keep consistent gutters, avoid accidental top-heavy placement, keep captions visually secondary, and leave deliberate whitespace around dense diagrams or screenshots.
- **Corner radius** — use moderate radii (`12-28px`) for cards, panels, quote blocks, stat blocks, terminal blocks, and image frames when the style supports it. Keep `--module-radius: 0` or very small radii for Brutalist, Swiss, editorial-grid, table-rule, or intentionally hard-edged geometric presets.

Common pitfalls:
- Never use `display:none/block` to hide slides — only `.active`/`.visible` from viewport-base.css.
- `.slide-content` uses `display:flex`; that's why `display`-based slide switching breaks. Stick to visibility/opacity.
- Negate CSS functions with `calc(-1 * clamp(...))`, never `-clamp(...)`.
- Review visible `http://` and `https://` URLs before linking. Source credits, citations, references, and official docs should be anchors with matching `href`, `target="_blank"`, and `rel="noopener noreferrer"`; URLs inside code, terminal commands, config snippets, placeholders, or illustrative examples should remain plain text. Article/source credits should use exactly `原文：<a href="SOURCE_URL" target="_blank" rel="noopener">《SOURCE_TITLE》</a>`, with the original English source title inside `《》` when available. Image source credits are optional; when shown, render them as low-emphasis microcopy rather than normal captions.
- Do not render visible `Description`, `描述`, generated-by text, or skill-name explanations in the final deck unless that wording is part of the source material.
- Do not render visible generic image bridge text such as “对应来源图”, “来源图如下”, “相关配图”, “配图说明”, “图片对应内容”, or equivalent filler. Replace it with a source-grounded analytical caption or remove the image.
- Do not create asymmetric peer-module layouts where content occupies the left side while the right side is blank, shorter without reason, or visually unaligned. If modules are peers, equalize their width and align their edges; if one module needs emphasis, make it a deliberate hero layout rather than pretending it is a peer grid.
- Do not round everything mechanically. Round content modules where it improves the composition, but preserve sharp corners for square chrome buttons, ruled tables, grid lines, and presets whose identity depends on hard edges.
- Before finalizing HTML, inspect every `.slide` at the fixed 1920×1080 stage size. Any slide with clipped text, clipped labels, overlapping cards, content entering the bottom control zone, a meaningful visual crop, an unrelated visual, a weak caption, or a generic image bridge must be repaired by splitting, repositioning, rewriting, or removing content.

---

## 4. The `SlidePresentation` Controller

Drop this into the `<script>`. It is complete and self-contained — keyboard, touch, wheel, buttons, and stage scaling.

```javascript
class SlidePresentation {
    constructor() {
        this.slides = Array.from(document.querySelectorAll('.slide'));
        this.current = 0;
        this.stage = document.getElementById('deckStage');
        this.controlsZone = document.querySelector('.deck-controls-zone');
        this.controlsBar = document.querySelector('.deck-controls');
        this.prevButton = document.getElementById('prevSlide');
        this.nextButton = document.getElementById('nextSlide');
        this.currentSlideLabel = document.getElementById('currentSlide');
        this.totalSlidesLabel = document.getElementById('totalSlides');
        this.lightbox = document.getElementById('imageLightbox');
        this.lightboxImage = document.getElementById('imageLightboxImage');
        this.lightboxClose = document.getElementById('imageLightboxClose');
        this.lightboxOpen = false;
        this.hideControlsTimer = null;
        this.setupControlButtons();
        this.setupStageScale();
        this.setupKeyboardNav();
        this.setupControlsReveal();
        this.setupTouchNav();
        this.setupWheelNav();
        this.setupImageLightbox();
        this.showSlide(0);
    }

    setupControlButtons() {
        if (this.prevButton) this.prevButton.addEventListener('click', () => this.prev());
        if (this.nextButton) this.nextButton.addEventListener('click', () => this.next());
        if (this.totalSlidesLabel) this.totalSlidesLabel.textContent = String(this.slides.length);
    }

    /* Scale the whole 1920×1080 stage to fit the window, centered (letterbox/pillarbox). */
    setupStageScale() {
        const scale = () => {
            const factor = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
            const x = (window.innerWidth - 1920 * factor) / 2;
            const y = (window.innerHeight - 1080 * factor) / 2;
            this.stage.style.transform = `translate(${x}px, ${y}px) scale(${factor})`;
        };
        scale();
        window.addEventListener('resize', scale);
    }

    setupKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            if (e.target.isContentEditable) return; // don't navigate while editing text
            if (this.lightboxOpen) {
                if (e.key === 'Escape') this.closeImageLightbox();
                e.preventDefault();
                return;
            }
            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                case ' ':
                case 'PageDown':
                    e.preventDefault(); this.next(); break;
                case 'ArrowLeft':
                case 'ArrowUp':
                case 'PageUp':
                    e.preventDefault(); this.prev(); break;
                case 'Home': e.preventDefault(); this.showSlide(0); break;
                case 'r':
                case 'R': e.preventDefault(); this.showSlide(0); break;
                case 'End': e.preventDefault(); this.showSlide(this.slides.length - 1); break;
            }
        });
    }

    setupControlsReveal() {
        if (!this.controlsZone || !this.controlsBar) return;
        const show = () => {
            window.clearTimeout(this.hideControlsTimer);
            this.controlsZone.classList.add('show-controls');
            this.controlsBar.style.opacity = '0.96';
            this.controlsBar.style.transform = 'translateX(-50%) translateY(0)';
            this.controlsBar.style.filter = 'blur(0)';
        };
        const hide = () => {
            window.clearTimeout(this.hideControlsTimer);
            this.hideControlsTimer = window.setTimeout(() => {
                this.controlsZone.classList.remove('show-controls');
                this.controlsBar.style.opacity = '';
                this.controlsBar.style.transform = '';
                this.controlsBar.style.filter = '';
            }, 3000);
        };
        this.controlsZone.addEventListener('mouseenter', show);
        this.controlsZone.addEventListener('mouseleave', hide);
        this.controlsZone.addEventListener('focusin', show);
        this.controlsZone.addEventListener('focusout', hide);
    }

    setupTouchNav() {
        let startX = 0, startY = 0;
        document.addEventListener('touchstart', (e) => {
            if (this.lightboxOpen) return;
            startX = e.changedTouches[0].clientX;
            startY = e.changedTouches[0].clientY;
        }, { passive: true });
        document.addEventListener('touchend', (e) => {
            if (this.lightboxOpen) return;
            const dx = e.changedTouches[0].clientX - startX;
            const dy = e.changedTouches[0].clientY - startY;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
                dx < 0 ? this.next() : this.prev();
            }
        }, { passive: true });
    }

    setupWheelNav() {
        let lock = false;
        window.addEventListener('wheel', (e) => {
            if (this.lightboxOpen) return;
            if (lock) return;
            if (Math.abs(e.deltaY) < 20) return;
            lock = true;
            e.deltaY > 0 ? this.next() : this.prev();
            setTimeout(() => { lock = false; }, 700);
        }, { passive: true });
    }

    setupImageLightbox() {
        if (!this.lightbox || !this.lightboxImage || !this.stage) return;
        this.stage.addEventListener('click', (event) => {
            const image = event.target.closest('.slide img');
            if (!image) return;
            event.preventDefault();
            this.openImageLightbox(image);
        });
        this.lightbox.addEventListener('click', (event) => {
            if (event.target === this.lightbox) this.closeImageLightbox();
        });
        if (this.lightboxClose) {
            this.lightboxClose.addEventListener('click', () => this.closeImageLightbox());
        }
    }

    openImageLightbox(image) {
        const src = image.currentSrc || image.src;
        if (!src) return;
        this.lightboxOpen = true;
        this.lightboxImage.src = src;
        this.lightboxImage.alt = image.alt || '';
        this.lightbox.hidden = false;
        window.requestAnimationFrame(() => this.lightbox.classList.add('is-open'));
    }

    closeImageLightbox() {
        if (!this.lightboxOpen || !this.lightbox) return;
        this.lightboxOpen = false;
        this.lightbox.classList.remove('is-open');
        window.setTimeout(() => {
            if (!this.lightboxOpen) {
                this.lightbox.hidden = true;
                this.lightboxImage.removeAttribute('src');
            }
        }, 220);
    }

    next() { this.showSlide(this.current + 1); }
    prev() { this.showSlide(this.current - 1); }

    showSlide(index) {
        this.current = Math.max(0, Math.min(index, this.slides.length - 1));
        this.slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === this.current);
            slide.classList.toggle('visible', i === this.current);
        });
        if (this.currentSlideLabel) this.currentSlideLabel.textContent = String(this.current + 1);
        if (this.prevButton) this.prevButton.disabled = this.current === 0;
        if (this.nextButton) this.nextButton.disabled = this.current === this.slides.length - 1;
    }
}

document.addEventListener('DOMContentLoaded', () => new SlidePresentation());
```

Required behaviors recap: keyboard (arrows/space/PageUp-Down/Home/End/R reset), touch swipe, mouse wheel (throttled), compact bottom previous/next buttons, current/total page status, a bottom control bar that reveals only from the bottom hover zone and hides after a short delay, and one-transform stage scaling that re-runs on resize. Keyboard hints must show `Space`, `↓`, `→` for next and `←`, `↑` for previous. The bottom controls and shortcut hints must keep one stable deck-wide chrome palette derived from the overall slide theme; verify the fixed palette remains readable across representative light and dark slides. Do not add large floating previous/next buttons on the slide canvas, do not add top-right page numbers or separate right-bottom page indicators outside the control bar, and do not add right-side anchor dots or any other anchor/jump-dot information by default. Keep all chrome OUTSIDE `.deck-stage` so it stays crisp and isn't scaled with the slides. If the user explicitly requests side anchor navigation, add it as an opt-in extension and derive its colors from the deck-wide chrome variables, not per-slide copied colors.

**On light-theme presets**, keep the same rule: derive the fixed chrome from that preset's palette. Define root chrome variables once, e.g.:
```css
:root {
    --control-accent: var(--accent);
    --chrome-border: color-mix(in srgb, var(--text-primary) 14%, transparent);
    --kbd-bar-bg: rgba(255, 255, 255, 0.88);
    --kbd-text: color-mix(in srgb, var(--text-primary) 78%, transparent);
    --kbd-bg: color-mix(in srgb, var(--text-primary) 6%, transparent);
    --kbd-border: color-mix(in srgb, var(--text-primary) 14%, transparent);
    --kbd-separator: color-mix(in srgb, var(--text-primary) 18%, transparent);
    --kbd-key-text: var(--text-primary);
    --link-color: var(--accent);
    --link-hover-bg: color-mix(in srgb, var(--link-color) 12%, transparent);
    --link-focus-ring: color-mix(in srgb, var(--link-color) 18%, transparent);
}
```

---

## 5. Inline Editing (optional, included by default)

A lightweight affordance so the user can tweak text in the browser. Include it unless the user asks for a locked/export-only file. Do NOT use the CSS `~` sibling selector for the hover reveal — `pointer-events:none` breaks the hover chain. Use JS with a 400ms grace timeout.

```html
<div class="edit-hotzone"></div>
<button class="edit-toggle" id="editToggle" title="Edit mode (E)">✏️</button>
```

```css
.edit-hotzone { position: fixed; top: 0; left: 0; width: 80px; height: 80px; z-index: 10000; cursor: pointer; }
.edit-toggle  { position: fixed; top: 16px; left: 16px; opacity: 0; pointer-events: none;
                transition: opacity 0.3s ease; z-index: 10001; border: none; border-radius: 999px;
                width: 44px; height: 44px; cursor: pointer; }
.edit-toggle.show, .edit-toggle.active { opacity: 1; pointer-events: auto; }
```

```javascript
const editToggle = document.getElementById('editToggle');
const hotzone = document.querySelector('.edit-hotzone');
let editing = false, hideTimer = null;

function setEditing(on) {
    editing = on;
    editToggle.classList.toggle('active', on);
    document.querySelectorAll('.slide h1, .slide h2, .slide p, .slide li, .slide span')
        .forEach(el => el.setAttribute('contenteditable', on));
}
editToggle.addEventListener('click', () => setEditing(!editing));
hotzone.addEventListener('click', () => setEditing(!editing));
hotzone.addEventListener('mouseenter', () => { clearTimeout(hideTimer); editToggle.classList.add('show'); });
hotzone.addEventListener('mouseleave', () => { hideTimer = setTimeout(() => { if (!editing) editToggle.classList.remove('show'); }, 400); });
editToggle.addEventListener('mouseenter', () => clearTimeout(hideTimer));
editToggle.addEventListener('mouseleave', () => { hideTimer = setTimeout(() => { if (!editing) editToggle.classList.remove('show'); }, 400); });
document.addEventListener('keydown', (e) => {
    if ((e.key === 'e' || e.key === 'E') && !e.target.isContentEditable) setEditing(!editing);
});
```

---

## 6. Visual Asset Pipeline (skip if no images or diagrams)

Process images and diagrams before embedding. The final deliverable is a **single HTML file**, so every kept visual must be embedded directly as a data URL or inline SVG. Do not depend on external companion files. Use original source visuals only; do not create AI-generated, stock, decorative, or placeholder images to fill empty space or replace missing source assets.

**Decide before you embed.** Only visuals selected by the Phase 2 visual asset decision in `SKILL.md` belong on a slide. Prefer reusing original source visuals whenever they carry information, context, or tone and reinforce that slide's content. Drop site chrome, generic stock photography, decorative filler, generated substitutes, duplicates/thumbnails, broken or unclear-licensed assets, and emoji-style icons. Keep charts, diagrams, dataflows, infographics, screenshots/UI captures, hero/cover art, portraits attached to quoted people, maps/timelines/scanned figures, existing legacy flowchart files, and Mermaid diagrams whose information is hard to retype. Preserve the original image content and the source's caption/alt text on the rendered figure.

Image source credits are optional. Use them only when they materially clarify provenance, licensing, or evidence. When included, separate the explanatory caption from the source credit and render the credit with `.image-source` or an equivalent very small, low-contrast style.

Legacy flowcharts:
- Existing flowchart image/vector files may be used directly; do not redraw them just to match the deck style.
- Do not restyle a source image into a different scene, generate a visually similar replacement, or invent missing labels, legends, people, products, screenshots, chart values, or backgrounds.
- Embed raster flowcharts as data URLs and vector flowcharts as inline SVG when possible.
- Preserve the original aspect ratio and all labels, legends, arrows, and grouping boundaries.

Mermaid diagrams:
- Render every fenced `mermaid` code block into embeddable SVG or a data URL before placing it on a slide.
- Prefer inline SVG for crisp text and scalable lines. Use high-resolution PNG data URLs only if SVG rendering is unavailable or visually broken.
- Use any available reliable renderer: local `mmdc`/Mermaid CLI, a browser-based Mermaid render, or another project-approved renderer. Do not leave raw Mermaid code as the visible slide content unless the slide is explicitly teaching Mermaid syntax.
- If styling the rendered diagram, improve contrast and readability without changing node labels, edges, direction, or semantics.
- Keep the Mermaid source in a non-visible HTML comment only when it helps maintainability.

Optional helpers (needs `pip install Pillow`):

```python
from PIL import Image, ImageDraw

def crop_circle(src, dst):
    img = Image.open(src).convert('RGBA')
    w, h = img.size; size = min(w, h)
    img = img.crop(((w-size)//2, (h-size)//2, (w-size)//2+size, (h-size)//2+size))
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    img.putalpha(mask); img.save(dst, 'PNG')

def resize_max(src, dst, max_dim=1200):
    img = Image.open(src); img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img.save(dst, quality=85)
```

Placement:
```html
<figure class="visual-card">
    <img src="data:image/png;base64,..."
         alt="Source caption or concise factual description grounded in the image"
         class="slide-image screenshot">
    <figcaption>Optional concise caption grounded in visible image content</figcaption>
    <p class="image-source">Source: optional image provenance in very small type</p>
</figure>
```
```css
.slide-image { max-width: 100%; max-height: 600px; object-fit: contain; border-radius: 8px; }
.slide-image.screenshot { border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
                          box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
.slide-image.logo { max-height: 200px; }
.diagram-image { max-width: 100%; max-height: 760px; object-fit: contain; }
```

Every generated deck that contains `<img>` elements must include the global image lightbox from the base template. Users should be able to click any slide image to inspect the original embedded source at a larger size. The lightbox must stay outside `.deck-stage`, use the image's `currentSrc || src`, preserve original aspect ratio with `object-fit: contain`, and close on backdrop click, close-button click, or `Escape`.

Fit every image or rendered diagram inside the 1920×1080 stage. If a slide is already full, move the visual to its own slide. Never reuse the same image on multiple slides (logos on title + closing are fine). Before delivery, view each visual at presentation size and confirm text labels are readable, the original information is complete, the image's subject matches the slide title/body copy, no generated replacement slipped in, and no frame, mask, crop, or background color makes the content hard to read. Captions are optional; any caption or explanation added around the image must be necessary for comprehension and supported by visible image details, source-provided alt/caption text, or nearby source prose. If the image can only be justified with generic text such as “对应来源图” or “相关配图”, remove it.
