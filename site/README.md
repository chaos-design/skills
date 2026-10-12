# chaos-design/skills — Site

Standalone directory site for the [`chaos-design/skills`](https://github.com/chaos-design/skills)
agent skills repository. It renders the published skills as a leaderboard, in the
layout language of [skills.sh](https://www.skills.sh/): ASCII wordmark hero,
install command, agent strip and a sortable/searchable leaderboard.

All site code lives under this `site/` directory; nothing outside it is required
to build or deploy the page.

## Stack

- **Next.js 15** (App Router, TypeScript, fully static export — `output: "export"`)
- **Tailwind CSS v4** with the Vercel Geist gray tokens (`--ds-gray-*`)
- **shadcn/ui** components (new-york style, neutral base) under `src/components/ui`
- **lucide** icons throughout
- **Geist Sans / Geist Mono** fonts (bundled with the `geist` package, self-hosted
  at build time — the export never fetches fonts from a CDN)
- **Vitest** for unit tests of the data pipeline and leaderboard logic

## Commands

```bash
npm install          # install dependencies
npm run dev          # local dev server on http://localhost:3000
npm run sync:skills  # regenerate src/data/skills.generated.json from the repo
npm run lint         # ESLint (next/core-web-vitals)
npm run typecheck    # tsc --noEmit
npm test             # vitest run
npm run build        # static export into out/
```

## Data

`src/data/skills.generated.json` is generated, not hand-written:

- skill metadata comes from `skills/<name>/manifest.json`, falling back to
  `SKILL.md` frontmatter;
- activity metrics (total commits, 8 weekly buckets, last update, contributors)
  come from the git history of each `skills/<name>` directory;
- the agent strip is the union of the `compat` lists across manifests.

Regenerate it after adding or renaming a skill, or after merges that change a
skill's history:

```bash
npm run sync:skills
git add src/data/skills.generated.json
```

The generated file is deterministic — the rolling activity windows are anchored
to the newest commit in the repository, not to wall-clock time, so re-running
the script without repository changes only advances `generatedAt`. CI fails when
the committed data drifts from the repository (ignoring `generatedAt`).

## Deployment

The build produces a fully static `out/` directory that needs no server.

### Vercel

Import the repository into Vercel and set **Root Directory** to `site`.
`vercel.json` pins the framework, build command and output directory; the
default build has no `BASE_PATH`, so the site is served from the domain root.

### GitHub Pages

The `site` GitHub Actions workflow (`.github/workflows/site.yml`) runs
lint / typecheck / tests / build on every push and pull request that touches
`site/`, and on pushes to `main` additionally deploys the export to GitHub
Pages with `BASE_PATH=/skills` (project pages live under `/<repo>`).

To enable it: repository **Settings → Pages → Source: GitHub Actions**.
The `deploy-pages` job only runs after a pull request is merged into `main`.

### Local preview of the export

```bash
npm run build
npx serve out        # or any static file server
```

## Structure

```text
site/
|-- scripts/
|   |-- sync-skills.mjs        # repo -> src/data/skills.generated.json
|   `-- sync-skills.test.mjs   # parser + bucketing unit tests
|-- src/
|   |-- app/
|   |   |-- globals.css        # Tailwind v4 + Geist tokens + animations
|   |   |-- icon.svg           # favicon
|   |   |-- layout.tsx         # fonts + metadata
|   |   |-- opengraph-image.tsx# build-time OG card
|   |   `-- page.tsx           # page composition
|   |-- components/
|   |   |-- ui/                # shadcn/ui components
|   |   |-- agents-carousel.tsx
|   |   |-- activity-sparkline.tsx
|   |   |-- brand-ascii.ts     # SKILLS wordmark
|   |   |-- hero.tsx
|   |   |-- install-command.tsx
|   |   |-- leaderboard.tsx    # search + tabs (client)
|   |   |-- leaderboard-table.tsx
|   |   |-- skill-row.tsx
|   |   |-- site-footer.tsx
|   |   `-- site-header.tsx
|   |-- data/
|   |   `-- skills.generated.json
|   `-- lib/
|       |-- skills.ts          # types, filter, sort, formatting
|       |-- skills.test.ts
|       `-- utils.ts           # cn()
|-- next.config.ts             # output: "export", BASE_PATH aware
|-- vercel.json
`-- vitest.config.ts
```

## Conventions

- Generated date/time values use UTC+8, formatted as `YYYY-MM-DD HH:mm:ss`.
- The leaderboard only shows real, repository-derived data — no invented
  install counts or activity numbers.
- Keep components small and single-purpose; page composition lives in
  `src/app/page.tsx`, data access in `src/lib/skills.ts`.
