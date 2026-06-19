# Style Presets Reference

Curated visual styles for the deck. Each is inspired by real design references — no generic "AI slop". **Abstract shapes only — no realistic illustrations.** Pick ONE preset and commit to it across the whole deck, or adapt one toward the source's brand colors.

Always include the full [viewport-base.css](viewport-base.css) in every deck.

## Readability Guardrail

Every preset must define readable text for its actual slide background. Dark themes use light `--text-primary` and lighter-than-background `--text-secondary`; light themes use dark `--text-primary`. Do not rely on browser default heading colors. If a module introduces a contrasting card/badge surface, define a paired text token such as `--text-on-card` and apply it explicitly only inside that surface.

---

## Dark Themes

### 1. Bold Signal
**Vibe:** Confident, bold, modern, high-impact.
**Layout:** Colored card on dark gradient. Section number top-left, nav top-right, title bottom-left.
**Type:** Display `Archivo Black` (900); Body `Space Grotesk` (400/500).
```css
:root {
    --bg-primary: #1a1a1a;
    --bg-gradient: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
    --card-bg: #FF5722;
    --text-primary: #ffffff;
    --text-on-card: #1a1a1a;
}
```
**Signature:** Bold colored focal card (orange/coral), large section numbers (01, 02), nav breadcrumbs, strict grid.

### 2. Electric Studio
**Vibe:** Bold, clean, professional, high contrast.
**Type:** Display & Body `Manrope` (800 / 400-500).
```css
:root { --bg-dark:#0a0a0a; --bg-white:#ffffff; --accent-blue:#4361ee; --text-dark:#0a0a0a; --text-light:#ffffff; }
```
**Signature:** Two-panel vertical split, accent edge bar, quote as hero, confident spacing.

### 3. Creative Voltage
**Vibe:** Bold, creative, energetic, retro-modern.
**Type:** Display `Syne` (700/800); Mono `Space Mono` (400/700).
```css
:root { --bg-primary:#0066ff; --bg-dark:#1a1a2e; --accent-neon:#d4ff00; --text-light:#ffffff; }
```
**Signature:** Electric blue + neon yellow, halftone texture, neon badges, script accents.

### 4. Dark Botanical
**Vibe:** Elegant, sophisticated, artistic, premium.
**Type:** Display `Cormorant` (400/600) serif; Body `IBM Plex Sans` (300/400).
```css
:root { --bg-primary:#0f0f0f; --text-primary:#e8e4df; --text-secondary:#9a9590;
        --accent-warm:#d4a574; --accent-pink:#e8b4b8; --accent-gold:#c9b896; }
```
**Signature:** Blurred overlapping gradient circles, warm accents, thin vertical lines, italic signature. Abstract CSS shapes only.

---

## Light Themes

### 5. Notebook Tabs
**Vibe:** Editorial, organized, tactile.
**Type:** Display `Bodoni Moda` (400/700); Body `DM Sans` (400/500).
```css
:root { --bg-outer:#2d2d2d; --bg-page:#f8f6f1; --text-primary:#1a1a1a;
        --tab-1:#98d4bb; --tab-2:#c7b8ea; --tab-3:#f4b8c5; --tab-4:#a8d8ea; --tab-5:#ffe6a7; }
```
**Signature:** Cream paper card on dark, colorful section tabs on right edge, binder-hole decorations.

### 6. Pastel Geometry
**Vibe:** Friendly, organized, approachable.
**Type:** Display & Body `Plus Jakarta Sans` (700/800 / 400-500).
```css
:root { --bg-primary:#c8d9e6; --card-bg:#faf9f7; --pill-pink:#f0b4d4; --pill-mint:#a8d4c4;
        --pill-sage:#5a7c6a; --pill-lavender:#9b8dc4; --pill-violet:#7c6aad; }
```
**Signature:** Rounded card with soft shadow, vertical pills of varying heights on right edge.

### 7. Split Pastel
**Vibe:** Playful, modern, friendly.
**Type:** Display & Body `Outfit` (700/800 / 400-500).
```css
:root { --bg-peach:#f5e6dc; --bg-lavender:#e4dff0; --text-dark:#1a1a1a;
        --badge-mint:#c8f0d8; --badge-yellow:#f0f0c8; --badge-pink:#f0d4e0; }
```
**Signature:** Two-color vertical split, playful badge pills with icons, grid overlay, rounded CTAs.

### 8. Vintage Editorial
**Vibe:** Witty, confident, personality-driven.
**Type:** Display `Fraunces` (700/900) serif; Body `Work Sans` (400/500).
```css
:root { --bg-cream:#f5f3ee; --text-primary:#1a1a1a; --text-secondary:#555; --accent-warm:#e8d4c0; }
```
**Signature:** Abstract geometric shapes (circle outline + line + dot), bold bordered CTA boxes, conversational copy. Geometric CSS shapes only.

---

## Specialty Themes

### 9. Neon Cyber
**Vibe:** Futuristic, techy. **Type:** `Clash Display` + `Satoshi` (Fontshare).
**Colors:** Deep navy `#0a0f1c`, cyan `#00ffcc`, magenta `#ff00aa`. **Signature:** Particle bg, neon glow, grid patterns.

### 10. Terminal Green
**Vibe:** Developer/hacker. **Type:** `JetBrains Mono` only.
**Colors:** GitHub dark `#0d1117`, terminal green `#39d353`. **Signature:** Scan lines, blinking cursor, code syntax styling.

### 11. Swiss Modern
**Vibe:** Clean, precise, Bauhaus. **Type:** `Archivo` (800) + `Nunito` (400).
**Colors:** Pure white, pure black, red accent `#ff3300`. **Signature:** Visible grid, asymmetric layouts, geometric shapes.

### 12. Paper & Ink
**Vibe:** Editorial, literary. **Type:** `Cormorant Garamond` + `Source Serif 4`.
**Colors:** Warm cream `#faf9f7`, charcoal `#1a1a1a`, crimson `#c41e3a`. **Signature:** Drop caps, pull quotes, elegant rules.

---

## Font Pairing Quick Reference

| Preset | Display | Body | Source |
| --- | --- | --- | --- |
| Bold Signal | Archivo Black | Space Grotesk | Google |
| Electric Studio | Manrope | Manrope | Google |
| Creative Voltage | Syne | Space Mono | Google |
| Dark Botanical | Cormorant | IBM Plex Sans | Google |
| Notebook Tabs | Bodoni Moda | DM Sans | Google |
| Pastel Geometry | Plus Jakarta Sans | Plus Jakarta Sans | Google |
| Split Pastel | Outfit | Outfit | Google |
| Vintage Editorial | Fraunces | Work Sans | Google |
| Neon Cyber | Clash Display | Satoshi | Fontshare |
| Terminal Green | JetBrains Mono | JetBrains Mono | Google/JetBrains |
| Swiss Modern | Archivo | Nunito | Google |
| Paper & Ink | Cormorant Garamond | Source Serif 4 | Google |

### Matching style to source content
- Report / financial / corporate → Swiss Modern, Electric Studio (restrained, authoritative)
- AI / tech / product → Neon Cyber, Creative Voltage, Terminal Green
- Essay / literary / editorial → Paper & Ink, Vintage Editorial, Dark Botanical
- Friendly / educational / internal → Pastel Geometry, Split Pastel, Notebook Tabs

---

## DO NOT USE (Generic AI Patterns)
- **Fonts:** Inter, Roboto, Arial, system fonts as display.
- **Colors:** `#6366f1` generic indigo, purple gradients on white.
- **Layouts:** Everything centered, generic hero sections, identical card grids.
- **Decorations:** Realistic illustrations, gratuitous glassmorphism, purposeless drop shadows.

---

## CSS Gotchas

**Negating CSS functions** — CSS forbids a leading `-` before a function; the browser silently discards the whole declaration (no error).
```css
/* WRONG — silently ignored */
right: -clamp(28px, 3.5vw, 44px);
/* CORRECT */
right: calc(-1 * clamp(28px, 3.5vw, 44px));
```

**Slide switching** — never use `display:none/block`; only `.active`/`.visible` (visibility/opacity/pointer-events). A later `.slide-content { display:flex }` overrides `display` and shows every slide at once.
