# Frontend Slides

Frontend Slides 会把文章、笔记、文档、图片或类 PPT 素材生成基于 deck-stage 的 HTML 演示页。当前模板库对齐参考仓库的 Bold Template Pack，提供 34 个强风格视觉方向。

来源：[zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides/)

## 安装

可以直接从 Chaos Design Skills 仓库安装该 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill frontend-slides
```

## 功能

- 输出固定 1920×1080 舞台的浏览器可运行 HTML deck。
- 使用共享的 `<deck-stage width="1920" height="1080">` 运行时，支持缩放、键盘、触控、锚点和打印。
- 模板参考 Bold Template Pack：34 个视觉模板，每个模板都有 `preview.md`、`design.md` 和 `template.html`。
- 最终单文件交付时应内联 `assets/runtime/deck-stage.js`。

## 使用方式

```text
用 frontend-slides 把这篇文章做成中文演示稿，风格从 bold template pack 里选一个。
```

工作流：

1. 读取 `templates/selection-index.json` 或 `templates/templates.json` 进行候选筛选。
2. 只读取候选模板的 `preview.md`；确认方向后读取选中模板的 `design.md`。
3. 生成 `<deck-stage width="1920" height="1080">`，每页必须是直接的 `section` 子元素。
4. 验证缩放、键盘导航、触控、右侧锚点、打印和内容边界。

## Skill Files

```text
skills/frontend-slides/
├── SKILL.md
├── prompt.md
├── assets/
│   ├── runtime-manifest.json
│   └── runtime/
├── templates/
│   ├── templates.json
│   ├── selection-index.json
│   └── <template-slug>/
│       ├── template.html
│       ├── preview.md
│       └── design.md
└── references/
```

## 模板图库

截图从 `tests/frontend-slides/<template>/index.html` 生成，并保存到 `screenshots/frontend-slides/`。

### `8-bit-orbit`

<img src="../../screenshots/frontend-slides/8-bit-orbit.webp" width="420" alt="8-bit-orbit 模板截图">

- 名称：8-Bit Orbit
- 标语：Pixel-art neon arcade aesthetic on a deep navy void.
- 适合：Anything that should feel like a CRT screen at 2am: cyberpunk, gaming, web3, indie dev tools, hackathon demos. Just as good for a tech talk that wants to lean into nostalgic-digital craft, a synthwave brand deck, or a creative review that wants to feel like a console.

### `biennale-yellow`

<img src="../../screenshots/frontend-slides/biennale-yellow.webp" width="420" alt="biennale-yellow 模板截图">

- 名称：Biennale Yellow
- 标语：Solar yellow on warm parchment with deep indigo serif and atmospheric sun-glow gradients.
- 适合：Anything that should feel like an art-biennale poster or a museum's annual programme: exhibition decks, arts-institution announcements, design conference brochures, curatorial pitches, literary publications, studio retrospectives. Equally good for any deck wanting Dutch-editorial atmosphere with an unmistakable single-color signature.

### `block-frame`

<img src="../../screenshots/frontend-slides/block-frame.webp" width="420" alt="block-frame 模板截图">

- 名称：BlockFrame
- 标语：Neobrutalist deck with pastel-neon color blocks and chunky black borders.
- 适合：Anything that should feel pop-graphic and design-led: indie SaaS launches, agency credentials, creative reviews, brand redesigns. Also a strong unexpected pick for tech, finance, or research when the speaker wants to land as confident and contemporary rather than buttoned-up.

### `blue-professional`

<img src="../../screenshots/frontend-slides/blue-professional.webp" width="420" alt="blue-professional 模板截图">

- 名称：Blue Professional
- 标语：Cream paper background with electric cobalt blue accents; clean modern professional.
- 适合：Anything that should feel modern-considered and lightly authoritative: B2B SaaS pitches, consulting deliverables, advisory updates, investor reports. Also a clean, tasteful choice whenever you want to read as professional without going stiff — research synthesis, internal reviews, brand work for service businesses.

### `bold-poster`

<img src="../../screenshots/frontend-slides/bold-poster.webp" width="420" alt="bold-poster 模板截图">

- 名称：Bold Poster
- 标语：Editorial poster aesthetic with massive Shrikhand display and a single fire-engine red accent.
- 适合：Anything that should land like a magazine cover: brand manifestos, founder vision decks, editorial / cultural pitches, creative reviews. Excellent any time you want a few words to feel like a poster — including unexpected fits like a tech keynote or a finance manifesto that wants to be quotable.

### `broadside`

<img src="../../screenshots/frontend-slides/broadside.webp" width="420" alt="broadside 模板截图">

- 名称：Broadside
- 标语：Dark editorial canvas with a single fire orange accent and bilingual Latin/Chinese type stack.
- 适合：Anything that should land like a broadside newspaper headline: brand manifestos, magazine and cultural pitches, design talks, bilingual EN/CN decks, founder vision statements. Also a striking pick for tech, research, or business decks that want a dramatic single-accent editorial feel.

### `capsule`

<img src="../../screenshots/frontend-slides/capsule.webp" width="420" alt="capsule 模板截图">

- 名称：Capsule
- 标语：Modular pill-shaped cards on warm bone with a full pastel-pop palette.
- 适合：Anything that should feel modular, modern, and a little Y2K: lifestyle brands, creator portfolios, DTC launches, beauty / wellness, agency credentials. Also fun for a playful tech demo or a research deck that wants pop-art clarity instead of gravitas.

### `cartesian`

<img src="../../screenshots/frontend-slides/cartesian.webp" width="420" alt="cartesian 模板截图">

- 名称：Cartesian
- 标语：Quiet warm-neutral palette with classical Playfair serifs; tasteful and unhurried.
- 适合：Anything that should feel quiet, considered, and grown-up: investment theses, white papers, advisory work, longform research, gallery / cultural decks. Also a strong choice for editorial features, founder reflections, or any deck where restraint is the message — including across tech and finance.

### `cobalt-grid`

<img src="../../screenshots/frontend-slides/cobalt-grid.webp" width="420" alt="cobalt-grid 模板截图">

- 名称：Cobalt Grid
- 标语：Electric cobalt serifs on a graph-paper canvas, anchored by stair-stepped pixel-glitch decorations and slim hairline rules.
- 适合：Anything that should feel like a quietly serious design / research bulletin, art publication, or curated trend report. Strong for studio annuals, agency capabilities decks, design-research publications, architecture / art / academic decks, and any deck wanting one strict accent colour and a printed-ledger calmness rather than corporate polish.

### `coral`

<img src="../../screenshots/frontend-slides/coral.webp" width="420" alt="coral 模板截图">

- 名称：Coral
- 标语：Cream and coral on near-black, set in oversized Bebas Neue.
- 适合：Anything that should feel warm-graphic and editorial: fashion, beauty, fitness, F&B, lifestyle brands, agency credentials. Just as strong for a creator portfolio, a manifesto, or a tech / research deck that wants warmth and a single bold accent instead of corporate cool.

### `creative-mode`

<img src="../../screenshots/frontend-slides/creative-mode.webp" width="420" alt="creative-mode 模板截图">

- 名称：Creative Mode
- 标语：Cream paper canvas with confident multi-color (green, pink, orange, yellow) accents and Archivo Black display.
- 适合：Anything that should feel design-led and confident: creative agency pitches, design studio decks, ad shop credentials, brand creative reviews, art-direction reviews. Also a great unexpected pick for a tech talk, research findings, or finance review when the speaker wants to lead with taste rather than convention.

### `daisy-days`

<img src="../../screenshots/frontend-slides/daisy-days.webp" width="420" alt="daisy-days 模板截图">

- 名称：Daisy Days
- 标语：Cheerful pastel deck with hand-drawn daisies, stars, and rainbows. Friendly, soft, and warm.
- 适合：Anything that should feel friendly, soft, and joyful: educational content, kids and family, wellness programs, community workshops, creator portfolios for craft / illustration. Also lovely for an unexpected playful internal kickoff, a wedding planning deck, or any moment where warmth is the message — including across tech or business contexts.

### `editorial-forest`

<img src="../../screenshots/frontend-slides/editorial-forest.webp" width="420" alt="editorial-forest 模板截图">

- 名称：Editorial Forest
- 标语：Forest green, dusty pink, and warm cream meet Source Serif 4 in a quiet, intentional quarterly-review deck.
- 适合：Anything that should feel like a considered editorial — quarterly reviews, internal readouts, studio updates, creative-agency presentations. Equally good for any deck that wants to feel warm and unhurried rather than corporate, including research recaps, book or program announcements, and team retrospectives.

### `editorial-tri-tone`

<img src="../../screenshots/frontend-slides/editorial-tri-tone.webp" width="420" alt="editorial-tri-tone 模板截图">

- 名称：Editorial Tri-Tone
- 标语：Three-color editorial system: dusty pink, mustard cream, and deep burgundy, set in Bricolage + Instrument Serif.
- 适合：Anything that should feel like a fashion-magazine spread: editorial pitches, fashion brand decks, lifestyle media, art direction reviews. Equally good for any deck — including tech, research, or business — that wants tri-tone discipline and serif/sans contrast instead of the usual neutrals.

### `emerald-editorial`

<img src="../../screenshots/frontend-slides/emerald-editorial.webp" width="420" alt="emerald-editorial 模板截图">

- 名称：Emerald Editorial
- 标语：A magazine-cover business deck: emerald + navy + paper, double-rule masthead ornaments, and a bold Bodoni-style display serif.
- 适合：Anything that should feel like the front of a serious magazine, including but not limited to leadership readouts, planning-office reviews, and strategy briefings. The double-rule masthead ornament gives it editorial gravitas without making it stiff — also a great unexpected pick for product launches or research recaps that want to feel considered rather than corporate.

### `grove`

<img src="../../screenshots/frontend-slides/grove.webp" width="420" alt="grove 模板截图">

- 名称：Grove
- 标语：Forest-green canvas with cream type, classical Playfair serifs, and a single rust accent.
- 适合：Anything that should feel organic, considered, and grown-up: sustainability and wellness brands, outdoor / nature products, wineries and restaurants, literary or arts decks, advisory deliverables, bilingual EN/CN reports. Also a calm, distinctive choice for tech, research, or business decks that want patience over urgency.

### `long-table`

<img src="../../screenshots/frontend-slides/long-table.webp" width="420" alt="long-table 模板截图">

- 名称：Long Table
- 标语：Warm cream and rust-red supper-club aesthetic with bold uppercase grotesk headlines, Fraunces serifs, and pill-shaped outlined buttons.
- 适合：Anything that should feel like a warm, intimate, modern hospitality / community brand: supper clubs, dinner series, small restaurants, creative-studio events, membership pitches, lifestyle and wine brands. Equally good for any deck wanting a single warm accent colour, mixed-weight typography, and a social-media-aware modern-editorial voice.

### `mat`

<img src="../../screenshots/frontend-slides/mat.webp" width="420" alt="mat 模板截图">

- 名称：Mat
- 标语：Dark sage canvas with bone paper and burnt-orange accent; mid-century modern with wood undertones.
- 适合：Anything that should feel mid-century, tactile, and intentional: design studio credentials, architecture / interior brands, ceramics / craft / furniture, advisory decks. Also a warm, distinctive choice for tech, research, or business decks that want a considered analog feel instead of digital-cool.

### `monochrome`

<img src="../../screenshots/frontend-slides/monochrome.webp" width="420" alt="monochrome 模板截图">

- 名称：Monochrome
- 标语：Ivory ledger paper with all-black type; Lora serif headlines, Jost body, no color at all.
- 适合：Anything that should feel like a hand-typeset ledger: user research synthesis, white papers, longform reports, academic and policy briefs, advisory deliverables, bilingual EN/CN reports. Equally good for tech, design, or brand decks that want their words to be the only thing on the page.

### `neo-grid-bold`

<img src="../../screenshots/frontend-slides/neo-grid-bold.webp" width="420" alt="neo-grid-bold 模板截图">

- 名称：Neo-Grid Bold
- 标语：Editorial neo-brutalism with a single neon yellow accent on off-white paper.
- 适合：Anything that should feel confident and editorial-graphic: design-led pitches, brand work, founder talks, conference keynotes. Excellent for stat-heavy slides, comparisons, and process flows. Just as strong for tech, research, or finance when the speaker wants to read as design-led rather than corporate.

### `peoples-platform`

<img src="../../screenshots/frontend-slides/peoples-platform.webp" width="420" alt="peoples-platform 模板截图">

- 名称：People's Platform (Block & Bold)
- 标语：Activist poster energy: blue, orange, red on cream, with Alfa Slab + Caveat Brush.
- 适合：Anything that should feel honest, loud, and graphic: cultural commentary, manifestos, civic and community decks, design talks, campaign pitches. Excellent for founder-vision moments, mission statements, or any deck — including across industries — that wants protest-poster energy instead of corporate polish.

### `pin-and-paper`

<img src="../../screenshots/frontend-slides/pin-and-paper.webp" width="420" alt="pin-and-paper 模板截图">

- 名称：Pin & Paper
- 标语：Yellow paper with safety-pin illustrations, ink-blue handwritten Caveat, paper-grain texture.
- 适合：Anything that should feel hand-crafted, warm, and literary: qualitative research findings, founder reflections, longform brand stories, workshop debriefs. The signature safety-pin illustrations and paper-grain texture make it especially good for any deck — including tech or business — that wants personality and warmth over polish.

### `pink-script`

<img src="../../screenshots/frontend-slides/pink-script.webp" width="420" alt="pink-script 模板截图">

- 名称：Pink Script — After Hours
- 标语：Black canvas, hot pink accent, pearl-cream paper, Instrument Serif headlines: late-night editorial luxury.
- 适合：Anything that should feel nocturnal, intentional, and a little luxe: fashion brand decks, creator personal brands, after-hours / nightlife / spirits launches, luxury product reveals, editorial features. Also a striking unexpected pick for a tech keynote, research synthesis, or business pitch that wants to land with magnetic confidence.

### `playful`

<img src="../../screenshots/frontend-slides/playful.webp" width="420" alt="playful 模板截图">

- 名称：Playful
- 标语：Sun-warm peach background with Syne display: a friendly indie launch deck.
- 适合：Anything that should feel warm, indie, and approachable: creator portfolios, indie product launches, lifestyle brands, small-business pitches, newsletter / community decks. Also welcoming for any deck — including tech or research — that wants to feel friendly and human rather than corporate.

### `raw-grid`

<img src="../../screenshots/frontend-slides/raw-grid.webp" width="420" alt="raw-grid 模板截图">

- 名称：Raw Grid
- 标语：Neo-brutalist deck with thick borders, offset shadows, and a pink/sage/ink palette.
- 适合：Anything that should feel direct and graphic-confident: founder pitches, accelerator demos, brand decks, indie launches, creator portfolios. Strong for stat slides, comparison tables, and process flows. Equally good for tech, research, or finance when the speaker wants the deck to feel scrappy-confident rather than buttoned-up.

### `retro-windows`

<img src="../../screenshots/frontend-slides/retro-windows.webp" width="420" alt="retro-windows 模板截图">

- 名称：Retro Windows
- 标语：Windows 95 chrome: gray title bars, MS Sans Serif, pixel typography, full nostalgia.
- 适合：Anything that should feel knowingly nostalgic: retro gaming, Y2K-aesthetic brands, creator portfolios with a 90s vibe, tech-history talks, deliberately tongue-in-cheek decks. A great choice anywhere a playful retro reference is the entire point.

### `retro-zine`

<img src="../../screenshots/frontend-slides/retro-zine.webp" width="420" alt="retro-zine 模板截图">

- 名称：Retro Zine
- 标语：Beige paper with green accent and Bebas Neue + Caveat: a riso-printed zine in HTML form.
- 适合：Anything that should feel printed, lo-fi, and crafted: indie zines and publications, music / arts brands, creator portfolios, small-batch craft launches, community decks. Also a great underdog choice for tech, research, or business decks that want a riso-print warmth instead of digital polish.

### `sakura-chroma`

<img src="../../screenshots/frontend-slides/sakura-chroma.webp" width="420" alt="sakura-chroma 模板截图">

- 名称：Sakura Chroma
- 标语：Vintage Japanese cassette-package aesthetic: cream paper, diagonal rainbow ribbons, condensed bold type, JIS-style spec checkboxes.
- 适合：Anything that should feel like a vintage Japanese cassette package or a TDK / Sony / Sakura Color product catalogue: indie hardware brand decks, music-label release schedules, analog studio retrospectives, zine and magazine pitches, kawaii-tech product launches, creative-studio annual reports. Equally good for any deck wanting bold colour, condensed display type, and a tactile printed-product personality.

### `scatterbrain`

<img src="../../screenshots/frontend-slides/scatterbrain.webp" width="420" alt="scatterbrain 模板截图">

- 名称：Scatterbrain
- 标语：Post-it inspired: pastel sticky notes, Caveat handwriting, Shrikhand and Zilla Slab type stack.
- 适合：Anything that should feel like a designer's whiteboard: brainstorms, workshops, creative-agency credentials, design-thinking sessions, ideation pitches, art-direction reviews. Equally fun for any deck — including tech, research, or business — that wants to read as in-progress thinking rather than polished conclusions.

### `signal`

<img src="../../screenshots/frontend-slides/signal.webp" width="420" alt="signal 模板截图">

- 名称：Signal
- 标语：Deep navy canvas with bone paper and a single muted-gold accent; institutional with quiet weight.
- 适合：Anything that should feel weighty, considered, and credibly institutional: investor decks, board presentations, consulting deliverables, legal / policy briefs, advisory pitches. Also a strong choice for tech, research, or brand work that wants to read as quietly authoritative rather than loud.

### `soft-editorial`

<img src="../../screenshots/frontend-slides/soft-editorial.webp" width="420" alt="soft-editorial 模板截图">

- 名称：Soft Editorial
- 标语：Cormorant Garamond serif on warm paper with sage, blush, and lemon accents.
- 适合：Anything that should feel literary, elegant, and unhurried: editorial features, longform brand stories, gallery / museum decks, advisory deliverables, wedding / lifestyle media, founder essays. Equally good for tech, research, or business decks that want a Sunday-supplement warmth instead of corporate polish.

### `stencil-tablet`

<img src="../../screenshots/frontend-slides/stencil-tablet.webp" width="420" alt="stencil-tablet 模板截图">

- 名称：Stencil & Tablet
- 标语：Bone paper with stencil-cut headlines and a six-color earth palette: archaeology meets brand.
- 适合：Anything that should feel archival, tactile, and weighty-graphic: museum and cultural-institution decks, art / architecture brands, longform research, heritage and craft brands, manifestos. A great choice anytime — including across tech and business — when you want the deck to feel like a field manual rather than a slide deck.

### `studio`

<img src="../../screenshots/frontend-slides/studio.webp" width="420" alt="studio 模板截图">

- 名称：Studio
- 标语：Black canvas with electric-yellow type; high-voltage design studio aesthetic.
- 适合：Anything that should feel electric and design-led: studio credentials, creative agency pitches, brand showcases, art-direction reviews, fashion / sneaker brand work. Also a striking unexpected choice for tech, research, or business decks where the speaker wants the deck to *be* a brand statement.

### `vellum`

<img src="../../screenshots/frontend-slides/vellum.webp" width="420" alt="vellum 模板截图">

- 名称：Vellum
- 标语：Deep navy canvas with warm-yellow Cormorant serifs and a single dusty teal accent. A quiet, scholarly aesthetic.
- 适合：Anything that should feel scholarly, literary, and quietly intelligent: research synthesis, white papers, academic and policy briefs, advisory deliverables, longform editorial pieces, founder reflections. Equally strong for any deck — including tech, business, or creator work — that wants a calm, considered atmosphere instead of energetic visuals.

## 更新截图

模板变化后，从 `tests/frontend-slides/<template-slug>/index.html` 以 1280×720 重新生成 WebP 截图，文件名与模板 slug 保持一致。
