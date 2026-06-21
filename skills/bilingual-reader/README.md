# Bilingual Reader

Bilingual Reader is a coding-agent skill for generating offline English-Chinese close-reading pages. It accepts English source material from links, images, document files, local file paths, attachments, or pasted text; uses [Web Markdown](../web-markdown/README.md) for source normalization into Markdown; and produces a self-contained close-reading page that opens directly from `file://`.

GitHub: <https://github.com/chaos-design/skills>

[中文](./README.zh-CN.md)

## Capabilities

- Standard workflow: raw input -> `web-markdown` performs source normalization -> `bilingual-reader` structures, translates, and enriches the Markdown -> self-contained HTML output.
- Generates bilingual close-reading pages with a hero section, source-faithful summary, paragraph-aligned original/translated content, original source images, glossary, and source footer.
- Accepts web links, screenshots or scanned images, PDFs, DOCX files, Markdown, HTML, plain text, local files, attachments, and pasted text when the Agent platform can access them.
- Preserves accessible original images directly in the original tab: web/document images are inserted in reading order, screenshot or OCR inputs show the source image at the top for reference, and accessible image bytes are inlined so the final HTML still works from `file://`.
- Supports CEFR vocabulary groups: `B1`, `B2`, `C1`, `C2`, and `Term`.
- Provides hover vocabulary tooltips, IPA, part of speech, definitions, examples, Chinese translations, and browser-native pronunciation.
- Includes indexed visual templates selected from article tone, content density, user intent, and language-learning needs.
- Produces final HTML with all data, CSS, and JavaScript inlined. No CDN, remote font, local server, `fetch()`, or module import is required for offline execution.

## Documentation

- [Data processing flow](./references/data-processing-flow.md) explains the complete pipeline from raw source intake to Markdown, reviewed `data.json`, static HTML, glossary, original content, and artifact review.

## Template Gallery

Templates are selected from `assets/templates/templates.json`. If the user does not name a template, the model chooses one from the indexed templates based on the article, user intent, tone, density, and language needs.

### `aurora-dashboard`

<img src="../../screenshots/bilingual-reader/aurora-dashboard.webp" width="420" alt="aurora-dashboard template screenshot">

- Best for: AI explainers, research digests, market analysis, and metric-heavy technical reading.
- Avoid for: Quiet literary essays or classical content where dashboard energy distracts.

### `blueprint-grid`

<img src="../../screenshots/bilingual-reader/blueprint-grid.webp" width="420" alt="blueprint-grid template screenshot">

- Best for: Systems design, engineering notes, API concepts, product specs, and procedural articles.
- Avoid for: Personal essays or playful education that needs warmth.

### `broadsheet`

<img src="../../screenshots/bilingual-reader/broadsheet.webp" width="420" alt="broadsheet template screenshot">

- Best for: News analysis, policy commentary, historical writing, and serious public-interest essays.
- Avoid for: Highly interactive study sessions or modern SaaS/product storytelling.

### `card-atlas`

<img src="../../screenshots/bilingual-reader/card-atlas.webp" width="420" alt="card-atlas template screenshot">

- Best for: Longform articles, source walkthroughs, concept maps, and guided reading workshops.
- Avoid for: Very short texts or poster-like pages where persistent navigation is unnecessary.

### `command-center`

<img src="../../screenshots/bilingual-reader/command-center.webp" width="420" alt="command-center template screenshot">

- Best for: Strategic briefings, launch narratives, operations, security, and decisive explainers.
- Avoid for: Calm reflective prose or exam prep sheets.

### `compact-study`

<img src="../../screenshots/bilingual-reader/compact-study.webp" width="420" alt="compact-study template screenshot">

- Best for: Exam review, intensive reading, vocabulary-heavy material, and technical summaries.
- Avoid for: Presentation-style pages or writing that needs atmosphere and breathing room.

### `editorial-split`

<img src="../../screenshots/bilingual-reader/editorial-split.webp" width="420" alt="editorial-split template screenshot">

- Best for: Essays, interviews, cultural commentary, design writing, and typography-led reading.
- Avoid for: Dense technical references or flashcard-like study material.

### `gradient-magazine`

<img src="../../screenshots/bilingual-reader/gradient-magazine.webp" width="420" alt="gradient-magazine template screenshot">

- Best for: Creative industry articles, trend reports, product storytelling, and accessible education.
- Avoid for: Regulated disclosures or quiet academic reading.

### `ink-scroll`

<img src="../../screenshots/bilingual-reader/ink-scroll.webp" width="420" alt="ink-scroll template screenshot">

- Best for: Chinese culture, history, philosophy, literary essays, and refined traditional reading.
- Avoid for: SaaS dashboards, operational briefings, or casual youth content.

### `kanban-flow`

<img src="../../screenshots/bilingual-reader/kanban-flow.webp" width="420" alt="kanban-flow template screenshot">

- Best for: Product management, startup articles, workflow explainers, learning plans, and checklists.
- Avoid for: Classical literary reading or emotional narratives.

### `midnight-lab`

<img src="../../screenshots/bilingual-reader/midnight-lab.webp" width="420" alt="midnight-lab template screenshot">

- Best for: Developer education, debugging stories, research notes, security analysis, and lab-style reading.
- Avoid for: Warm consumer-facing content or traditional print essays.

### `mono-focus`

<img src="../../screenshots/bilingual-reader/mono-focus.webp" width="420" alt="mono-focus template screenshot">

- Best for: Code-adjacent articles, investigative summaries, concise briefs, and low-distraction study.
- Avoid for: Design-forward editorials or visual narratives.

### `paper-notes`

<img src="../../screenshots/bilingual-reader/paper-notes.webp" width="420" alt="paper-notes template screenshot">

- Best for: Beginner-friendly reading, classroom handouts, guided learning, and reflective articles.
- Avoid for: Hard technical specs or urgent briefings needing stronger authority.

### `synthwave-arcade`

<img src="../../screenshots/bilingual-reader/synthwave-arcade.webp" width="420" alt="synthwave-arcade template screenshot">

- Best for: Gaming, internet culture, youth technology, creative coding, and hackathon recaps.
- Avoid for: Healthcare, finance, legal, or trust-sensitive contexts.

## Installation

### Install from a remote skill package

Install this skill globally from the remote repository with:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
```

`web-markdown` is a required dependency and must be installed alongside `bilingual-reader`. If only `bilingual-reader` is installed, raw input may not be normalized into Markdown and downstream extraction, image preservation, code-block preservation, or translation may fail.

When an agent discovers that `web-markdown` is missing, it should ask the user before installing it, show the command above, and continue only after the dependency is available.

If you use one of the manual copy methods below, also copy `skills/web-markdown` into the same agent skills root so it sits next to `bilingual-reader`.

### Quick add to a specific skills directory

Use this when you already know the skills directory that your agent scans. Run the command from this repository root, and change `DEST` to the exact target directory you want.

```bash
DEST=".agents/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

The target directory must contain `SKILL.md` at its root. Supporting folders such as `assets/` and `references/` must stay next to it; optional templates live under `assets/templates/`. The `tests/` directory is a source-project validation fixture and should not be installed with the skill.

### Install in Codex

Codex discovers skills from `.agents/skills/` in the current repository path hierarchy, from `$HOME/.agents/skills/`, and from admin/system skill locations. For a repository-scoped install:

```bash
DEST=".agents/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

For a user-level install available across repositories:

```bash
DEST="$HOME/.agents/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

Codex can also install catalog or GitHub-hosted skills through the in-session `$skill-installer`. After adding a skill, start a new Codex session if it is not detected immediately.

### Install in Claude Code

Claude Code personal skills live under `~/.claude/skills/<skill-name>/SKILL.md`, and project skills live under `.claude/skills/<skill-name>/SKILL.md`.

```bash
DEST="$HOME/.claude/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

For a project-scoped Claude Code install, use:

```bash
DEST=".claude/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

Restart Claude Code if the newly copied skill does not appear.

### Install in Trae

Trae project skills live under `.trae/skills/`, and global skills live under `~/.trae/skills/` on macOS/Linux. Some Trae CN installations use `~/.trae-cn/skills/`; if your Settings > Skills and Commands page shows a different global directory, use that directory.

```bash
DEST="$HOME/.trae/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

For Trae CN local installs that use the `.trae-cn` home directory:

```bash
DEST="$HOME/.trae-cn/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

For a project-scoped Trae install:

```bash
DEST=".trae/skills/bilingual-reader"
INSTALL_FILES=(SKILL.md prompt.md assets references)
mkdir -p "$DEST"
rm -rf "$DEST/tests"
cp -R "${INSTALL_FILES[@]}" "$DEST"/
```

### Use as a source project

```bash
git clone https://github.com/chaos-design/skills.git
cd skills
```

## End-to-End Processing Flow

`bilingual-reader` is a dependency-aware close-reading generation skill. A complete run starts with skill installation and dependency configuration, then proceeds through source normalization, human review of `data.json`, template rendering, and final quality assurance.

```mermaid
flowchart TD
  A[Create or install bilingual-reader skill] --> B[Install required web-markdown dependency]
  B --> C[Verify skill files: SKILL.md, references, assets, templates, scripts]
  C --> D[Configure output folder, template preference, language, and source input]
  D --> E{Input type}
  E -- URL, PDF, DOCX, file, image, or pasted text --> F[Normalize source with web-markdown]
  E -- Existing Markdown --> G[Use Markdown as normalized source]
  F --> Q[Reject boundary failures: empty input, invalid URL, malformed metadata, unsafe media, oversize content]
  G --> Q
  Q --> H[Generate data.json only]
  H --> I[Human review: translation quality, summary fidelity, glossary, images, metadata]
  I --> J{Review approved?}
  J -- No --> K[Revise data.json without inventing source content]
  K --> I
  J -- Yes --> L[Select indexed visual template]
  L --> M[Render self-contained bilingual HTML]
  M --> N[Run quality assurance: CJK fields, source images, tooltips, offline assets]
  N --> O{Checks pass?}
  O -- No --> K
  O -- Yes --> P[Deliver data.json and final HTML]
```

1. Create or install the skill so `SKILL.md`, `references/`, `assets/`, templates, runtime CSS, runtime JavaScript, and scripts stay in the same skill root.
2. Install `web-markdown` next to `bilingual-reader`; it is the required source-normalization dependency for URLs, documents, images, and pasted content.
3. Configure the run by confirming the source, output folder, optional template preference, target reading language, and whether existing generated files may be overwritten.
4. Normalize raw source into Markdown while preserving title, source metadata, body order, images, links, tables, and code blocks.
5. Reject unsafe boundary inputs before generation: empty or tiny sources, unsupported control characters, invalid `Source` or `Fetched` metadata, unclosed code fences, malformed tables, unsupported image sources, oversize HTML/Markdown/JSON, duplicate quiz options, invalid glossary regex, and incompatible CLI options.
6. Generate `data.json` first and stop for human review. The reviewer checks Chinese translations, summary fidelity, glossary entries, source images, and metadata before any final HTML is rendered.
7. Render the approved data into a selected template with all data, CSS, and JavaScript inlined.
8. Validate the final artifact for CJK translation fields, image sizing, source attribution, tooltip behavior, pronunciation support, duplicate IDs, offline `file://` execution, and absence of forbidden runtime resources.
9. Deliver both `data.json` and the final HTML. Do not treat the HTML alone as a complete deliverable.

## Usage

Ask a SKILL-aware agent:

```text
Create an English-Chinese close-reading page for this article with a summary, paragraph-aligned translation, CEFR glossary, hover tooltips, and native browser pronunciation.
```

The agent will:

1. Fetch a URL, read a document or file, extract text from an image, or use pasted source text.
2. Invoke `web-markdown` to convert the raw input into standard Markdown while preserving the title, source metadata, body text, images, links, tables, and code blocks.
3. Stop with a clear error if the Markdown is empty, too short, too large, has invalid metadata, contains unsupported control characters, has broken tables, uses unsupported image references, or leaves code fences unclosed.
4. Extract the title, source metadata, and body paragraphs from the Markdown in reading order.
5. Translate and structure the study content, then select one indexed template under `assets/templates/<name>/template.html`.
6. Inline content, theme values, runtime CSS, and runtime JavaScript into the final HTML.
7. Validate that the generated page has no external scripts, external stylesheets, `fetch()`, module imports, duplicate IDs, invalid glossary runtime rules, or unreplaced placeholders.

Supported input sources:

- Links: fetch the web page and extract the main English text.
- Images: use vision/OCR to extract visible English text from screenshots or scans.
- Documents and files: read accessible PDFs, DOCX files, Markdown, HTML, plain text, local file paths, or attachments.
- Pasted text: use the provided text directly.

### Troubleshooting

- If the body is empty, paragraph order is wrong, original images/code blocks are missing, or page generation fails, first confirm that `web-markdown` is installed correctly.
- Run `web-markdown` on the same input and verify that it produces valid Markdown. Fix fetching or Markdown conversion before continuing with the close-reading page.

## Configuration

Important files:

```text
.
├── SKILL.md                    # root skill entry with trigger conditions, workflow, and quality rules
├── prompt.md                   # platform-neutral harness
├── references/
│   └── data-schema.md          # exact data.json field contract
├── assets/
│   ├── template.html           # base full-page shell used by the renderer
│   ├── runtime.css             # shared styles
│   ├── runtime.js              # theme switching, tooltips, auto-wrapping, pronunciation, glossary grouping, and reading progress
│   └── templates/
│       ├── templates.json      # compact optional-template index for progressive loading
│       └── <name>/
│           └── template.html   # optional visual templates
```

Theme values are injected through the template `THEME` object. Article-specific content belongs only in `data.json`; do not fork templates for one article.

## Examples

Minimal glossary item:

```json
{
  "autonomous": {
    "w": "autonomous",
    "ipa": "/ɔːˈtɒnəməs/",
    "pos": "adj.",
    "level": "C1",
    "def": "自主的，自治的；无需外部控制即可运作的。",
    "eg": "Fully autonomous systems operate independently.",
    "egzh": "完全自主的系统能独立运行。"
  }
}
```

Hover markup in summary rows:

```html
<span class="w" data-k="autonomous">autonomous<span class="tip"></span></span>
```

Original-view auto-wrap rule:

```json
["\\bautonomous\\b", "i", "autonomous"]
```

## Quality Checks

```bash
python3 -m json.tool skills/bilingual-reader/assets/templates/templates.json > /dev/null
```

This verifies that the template index is valid JSON. The skill itself is a file-based asset package and does not require an external build step.

## Project Structure

```text
.
├── SKILL.md                         # root skill entry
├── prompt.md                        # portable agent instructions
├── assets/                          # base shell and shared runtime
│   └── templates/                   # progressively loaded optional templates
└── references/                      # data.json contract
```

This repository keeps skill runtime files under `skills/bilingual-reader` and longer user-facing introductions under `skills/bilingual-reader`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
