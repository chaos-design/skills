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
         * Leave URLs in code, terminal commands, config snippets, placeholders, and illustrative
         * examples as plain text. Keep trailing punctuation outside any generated link.
         */

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

When a deck mixes light and dark slides, set chrome on each slide so keyboard hints follow the
current slide instead of staying on a fixed deck-wide palette:

```html
<section class="slide" data-chrome="dark">...</section>
<section class="slide" data-chrome="light">...</section>
```

Use `data-chrome="dark"` for dark slide backgrounds and `data-chrome="light"` for bright slide
backgrounds. For custom palettes, override the active slide's chrome tokens with data attributes:

```html
<section
    class="slide"
    data-kbd-bar-bg="rgba(8, 12, 20, 0.84)"
    data-kbd-text="rgba(255, 255, 255, 0.92)"
    data-kbd-key-text="#ffffff"
>
    ...
</section>
```

Never leave the bottom controls on a fixed light or fixed dark palette when slides vary by theme.

---

## 3. Slide Layout Patterns

Pick the layout that fits the content. All are authored at 1920×1080.

- **Title** — `h1` (`--title-size`) + optional subtitle/source inside a centered `.title-block`. The first slide's main title must be related to the article's actual theme or central thesis, not a generic deck label, filename, or raw URL slug. If helpful, add a subtitle or concise grounded personal framing line, but keep it faithful to the source. Place the title block in the middle of the stage by default.
- **Bullet list** — `h2` heading + `<ul>` of `.reveal` items. Keep to density-mode limits (≤3 low, ≤8 high).
- **Statement / quote** — one large centered line; use for a punchy idea or pulled quote with attribution.
- **Two-column** — `display:grid; grid-template-columns: 1fr 1fr` for text + image, or compare/contrast.
- **Stat / hero number** — one giant number (`font-size: 240px`) + a short caption.
- **Card grid** — `display:grid; grid-template-columns: repeat(3, 1fr); gap` for 3–6 parallel items.
- **Corner radius** — use moderate radii (`12-28px`) for cards, panels, quote blocks, stat blocks, terminal blocks, and image frames when the style supports it. Keep `--module-radius: 0` or very small radii for Brutalist, Swiss, editorial-grid, table-rule, or intentionally hard-edged geometric presets.

Common pitfalls:
- Never use `display:none/block` to hide slides — only `.active`/`.visible` from viewport-base.css.
- `.slide-content` uses `display:flex`; that's why `display`-based slide switching breaks. Stick to visibility/opacity.
- Negate CSS functions with `calc(-1 * clamp(...))`, never `-clamp(...)`.
- Review visible `http://` and `https://` URLs before linking. Source credits, citations, references, and official docs should be anchors with matching `href`, `target="_blank"`, and `rel="noopener noreferrer"`; URLs inside code, terminal commands, config snippets, placeholders, or illustrative examples should remain plain text. Article/source credits should use exactly `原文：<a href="SOURCE_URL" target="_blank" rel="noopener">《SOURCE_TITLE》</a>`.
- Do not round everything mechanically. Round content modules where it improves the composition, but preserve sharp corners for square chrome buttons, ruled tables, grid lines, and presets whose identity depends on hard edges.

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
        this.hideControlsTimer = null;
        this.setupControlButtons();
        this.setupStageScale();
        this.setupKeyboardNav();
        this.setupControlsReveal();
        this.setupTouchNav();
        this.setupWheelNav();
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
            startX = e.changedTouches[0].clientX;
            startY = e.changedTouches[0].clientY;
        }, { passive: true });
        document.addEventListener('touchend', (e) => {
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
            if (lock) return;
            if (Math.abs(e.deltaY) < 20) return;
            lock = true;
            e.deltaY > 0 ? this.next() : this.prev();
            setTimeout(() => { lock = false; }, 700);
        }, { passive: true });
    }

    next() { this.showSlide(this.current + 1); }
    prev() { this.showSlide(this.current - 1); }

    syncChromeToSlide(slide) {
        if (!this.controlsBar || !slide) return;
        const presets = {
            dark: {
                '--control-accent': 'var(--accent)',
                '--chrome-border': 'rgba(255, 255, 255, 0.22)',
                '--kbd-bar-bg': 'rgba(8, 12, 20, 0.82)',
                '--kbd-text': 'rgba(255, 255, 255, 0.92)',
                '--kbd-bg': 'rgba(255, 255, 255, 0.16)',
                '--kbd-border': 'rgba(255, 255, 255, 0.28)',
                '--kbd-separator': 'rgba(255, 255, 255, 0.18)',
                '--kbd-key-text': '#ffffff'
            },
            light: {
                '--control-accent': 'var(--accent)',
                '--chrome-border': 'rgba(17, 24, 39, 0.16)',
                '--kbd-bar-bg': 'rgba(255, 255, 255, 0.88)',
                '--kbd-text': 'rgba(17, 24, 39, 0.82)',
                '--kbd-bg': 'rgba(17, 24, 39, 0.08)',
                '--kbd-border': 'rgba(17, 24, 39, 0.16)',
                '--kbd-separator': 'rgba(17, 24, 39, 0.14)',
                '--kbd-key-text': 'rgba(17, 24, 39, 0.9)'
            }
        };
        const mode = (slide.dataset.chrome || '').toLowerCase();
        const preset = presets[mode] || {};
        const attrs = {
            '--control-accent': slide.getAttribute('data-control-accent'),
            '--chrome-border': slide.getAttribute('data-chrome-border'),
            '--kbd-bar-bg': slide.getAttribute('data-kbd-bar-bg'),
            '--kbd-text': slide.getAttribute('data-kbd-text'),
            '--kbd-bg': slide.getAttribute('data-kbd-bg'),
            '--kbd-border': slide.getAttribute('data-kbd-border'),
            '--kbd-separator': slide.getAttribute('data-kbd-separator'),
            '--kbd-key-text': slide.getAttribute('data-kbd-key-text')
        };
        Object.keys(attrs).forEach((name) => {
            const value = attrs[name] || preset[name];
            if (value) this.controlsBar.style.setProperty(name, value);
            else this.controlsBar.style.removeProperty(name);
        });
    }

    showSlide(index) {
        this.current = Math.max(0, Math.min(index, this.slides.length - 1));
        this.slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === this.current);
            slide.classList.toggle('visible', i === this.current);
        });
        this.syncChromeToSlide(this.slides[this.current]);
        if (this.currentSlideLabel) this.currentSlideLabel.textContent = String(this.current + 1);
        if (this.prevButton) this.prevButton.disabled = this.current === 0;
        if (this.nextButton) this.nextButton.disabled = this.current === this.slides.length - 1;
    }
}

document.addEventListener('DOMContentLoaded', () => new SlidePresentation());
```

Required behaviors recap: keyboard (arrows/space/PageUp-Down/Home/End/R reset), touch swipe, mouse wheel (throttled), compact bottom previous/next buttons, current/total page status, a bottom control bar that reveals only from the bottom hover zone and hides after a short delay, and one-transform stage scaling that re-runs on resize. Keyboard hints must show `Space`, `↓`, `→` for next and `←`, `↑` for previous. The bottom controls and shortcut hints must synchronize to the currently active slide's theme through `data-chrome="dark|light"` or per-slide `data-kbd-*` overrides; verify both light and dark slides keep readable label text, key text, key backgrounds, separators, and borders. Do not add large floating previous/next buttons on the slide canvas, do not add top-right page numbers or separate right-bottom page indicators outside the control bar, and do not add right-side anchor dots or any other anchor/jump-dot information by default. Keep all chrome OUTSIDE `.deck-stage` so it stays crisp and isn't scaled with the slides. If the user explicitly requests side anchor navigation, add it as an opt-in extension and derive its colors from the active slide's chrome variables, not copied fixed template colors.

**On light-theme presets**, keep the same rule: derive chrome from that preset's palette. If the whole deck is light, define root chrome variables. If only some slides are light, prefer per-slide `data-chrome="light"` or `data-kbd-*` overrides so the controls, hints, and links stay visible against the active background, e.g.:
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

**Decide before you embed.** Only visuals selected by the Phase 2 visual asset decision in `SKILL.md` belong on a slide. Prefer reusing original source visuals whenever they carry information, context, or tone. Drop site chrome, generic stock photography, decorative filler, generated substitutes, duplicates/thumbnails, broken or unclear-licensed assets, and emoji-style icons. Keep charts, diagrams, dataflows, infographics, screenshots/UI captures, hero/cover art, portraits attached to quoted people, maps/timelines/scanned figures, existing legacy flowchart files, and Mermaid diagrams whose information is hard to retype. Preserve the original image content and the source's caption/alt text on the rendered figure.

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
    <figcaption>Source caption, credit, or a factual note grounded in visible image content</figcaption>
</figure>
```
```css
.slide-image { max-width: 100%; max-height: 600px; object-fit: contain; border-radius: 8px; }
.slide-image.screenshot { border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
                          box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
.slide-image.logo { max-height: 200px; }
.diagram-image { max-width: 100%; max-height: 760px; object-fit: contain; }
```

Fit every image or rendered diagram inside the 1920×1080 stage. If a slide is already full, move the visual to its own slide. Never reuse the same image on multiple slides (logos on title + closing are fine). Before delivery, view each visual at presentation size and confirm text labels are readable, the original information is complete, no generated replacement slipped in, and no frame, mask, crop, or background color makes the content hard to read. Any caption or explanation added around the image must be supported by visible image details, source-provided alt/caption text, or nearby source prose.
