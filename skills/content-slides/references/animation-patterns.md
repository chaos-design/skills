# Animation Patterns Reference

Match animation to the intended feeling of the source content. Prefer CSS-only; animations trigger when a slide gains the `.visible` class.

## Effect-to-Feeling Guide

| Feeling | Animations | Visual cues |
| --- | --- | --- |
| **Dramatic / Cinematic** | Slow fade-ins (1–1.5s), scale 0.9→1, parallax | Dark backgrounds, spotlight, full-bleed images |
| **Techy / Futuristic** | Neon glow (box-shadow), glitch/scramble text, grid reveals | Particle canvas, grid patterns, monospace accents, cyan/magenta |
| **Playful / Friendly** | Bouncy/spring easing, floating/bobbing | Rounded corners, pastel/bright colors |
| **Professional / Corporate** | Subtle fast (200–300ms), clean cuts | Navy/slate/charcoal, precise spacing, data focus |
| **Calm / Minimal** | Very slow gentle fades | High whitespace, muted palette, serif type, generous padding |
| **Editorial / Magazine** | Staggered text reveals, image-text interplay | Strong type hierarchy, pull quotes, grid-breaking layouts |

## Entrance Animations

```css
/* Fade + slide up (most versatile) */
.reveal { opacity: 0; transform: translateY(30px);
    transition: opacity 0.6s var(--ease-out-expo), transform 0.6s var(--ease-out-expo); }
.slide.visible .reveal { opacity: 1; transform: translateY(0); }

/* Scale in */
.reveal-scale { opacity: 0; transform: scale(0.9);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo); }
.slide.visible .reveal-scale { opacity: 1; transform: scale(1); }

/* Slide from left */
.reveal-left { opacity: 0; transform: translateX(-50px);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo); }
.slide.visible .reveal-left { opacity: 1; transform: translateX(0); }

/* Blur in */
.reveal-blur { opacity: 0; filter: blur(10px);
    transition: opacity 0.8s, filter 0.8s var(--ease-out-expo); }
.slide.visible .reveal-blur { opacity: 1; filter: blur(0); }
```

Stagger children with `:nth-child` transition-delay (see html-template.md section 1).

## Background Effects

```css
/* Gradient mesh — layered radial gradients for depth */
.gradient-bg {
    background:
        radial-gradient(ellipse at 20% 80%, rgba(120,0,255,0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0,255,200,0.2) 0%, transparent 50%),
        var(--bg-primary);
}

/* Grid pattern — subtle structural lines */
.grid-bg {
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}
```

## Interactive Effect (optional)

```javascript
/* 3D tilt on hover — depth for cards/panels */
class TiltEffect {
    constructor(el) {
        el.style.transformStyle = 'preserve-3d';
        el.addEventListener('mousemove', (e) => {
            const r = el.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            el.style.transform = `rotateY(${x*10}deg) rotateX(${-y*10}deg)`;
        });
        el.addEventListener('mouseleave', () => { el.style.transform = 'rotateY(0) rotateX(0)'; });
    }
}
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Fonts not loading | Verify Fontshare/Google URL and that font names match in CSS |
| Animations not triggering | Confirm `.visible` is toggled in `showSlide`; check the `.slide.visible .reveal` selector |
| All slides visible at once | You used `display:none/block` — switch to `.active`/`.visible` (visibility/opacity) |
| Element in wrong position | You negated a CSS function directly — use `calc(-1 * ...)` |
| Performance | Animate only `transform`/`opacity`; use `will-change` sparingly; throttle wheel handler |
