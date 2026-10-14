# chaos-design/skills — Site

Standalone directory site for the [`chaos-design/skills`](https://github.com/chaos-design/skills)
agent skills repository. It renders the published skills as a leaderboard and a
per-skill detail page, in the layout language of
[skills.sh](https://www.skills.sh/): ASCII wordmark hero, install command, agent
strip, a sortable/searchable leaderboard and a detail view for every skill.

All site code lives under this `site/` directory; nothing outside it is required
to build or deploy the page.

## Stack

- **Next.js 15** (App Router, TypeScript, fully static export — `output: "export"`)
- **Tailwind CSS v4** with the Vercel Geist gray tokens (`--ds-gray-*`)
- **shadcn/ui** components (new-york style, neutral base) under `src/components/ui`
  — including the Sonner toaster, which carries the copy confirmations
- **lucide** icons throughout
- **Geist Sans / Geist Mono** fonts (bundled with the `geist` package, self-hosted
  at build time — the export never fetches fonts from a CDN)
- **Biome** for linting and formatting (replaces ESLint)
- **Vitest** for unit tests of the data pipeline and leaderboard logic

## Commands

```bash
npm install          # install dependencies
npm run dev          # local dev server on http://localhost:3456
npm run sync:skills  # regenerate public/data/skills.json from the repo
npm run lint         # Biome (check formatting + lint)
npm run lint:fix     # Biome (auto-fix formatting + lint)
npm run typecheck    # tsc --noEmit
npm test             # vitest run
npm run build        # static export into out/
```

## Data

`public/data/skills.json` is generated, not hand-written:

- skill metadata comes from `skills/<name>/manifest.json`, falling back to
  `SKILL.md` frontmatter;
- activity metrics (total commits, 8 weekly buckets, last update, contributors)
  come from the **GitHub REST API** — `GET /repos/chaos-design/skills/commits?path=skills/<name>`,
  paginated — so the numbers do not depend on how deep the local checkout is;
- the agent strip is the union of the `compat` lists across manifests.

The sync needs network access. Anonymous calls are limited to 60 requests/hour
(one per skill directory, so there is headroom); set `GITHUB_TOKEN` to raise
it, which is what CI does.

Regenerate it after adding or renaming a skill, or after merges that change a
skill's history:

```bash
npm run sync:skills
git add public/data/skills.json
```

The generated file is deterministic — the rolling activity windows are anchored
to the newest commit in the repository, not to wall-clock time, so re-running
the script without repository changes only advances `generatedAt`. CI checks the
committed data against the repository on pull requests (ignoring `generatedAt`).

### Freshness at runtime

Because the file lives in `public/`, the browser re-fetches it on every visit
instead of reading numbers that were baked into the bundle:

- the build passes the generated file to `SkillsProvider` as `initialData`, so
  the first paint is complete and nothing shifts;
- on mount, and again whenever the tab regains focus, the same file is fetched
  with `cache: "no-store"` and swapped in when it changed;
- the site workflow additionally regenerates and redeploys on a schedule and
  whenever anything under `skills/` changes, so the deployed JSON stays current
  without anyone editing data by hand.

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
|-- public/
|   |   `-- data/
|   |       `-- skills.json    # generated dataset, re-fetched at runtime
|-- scripts/
|   |-- sync-skills.mjs        # repo -> public/data/skills.json
|   `-- sync-skills.test.mjs   # parser + bucketing unit tests
|-- src/
|   |-- app/
|   |   |-- [skill]/
|   |   |   `-- page.tsx       # per-skill detail page (SSG via generateStaticParams)
|   |   |-- globals.css        # Tailwind v4 + Geist tokens + animations
|   |   |-- icon.svg           # favicon
|   |   |-- layout.tsx         # fonts + metadata
|   |   |-- opengraph-image.tsx# build-time OG card
|   |   `-- page.tsx           # page composition
|   |-- components/
|   |   |-- ui/                # shadcn/ui components (sonner.tsx = copy toasts)
|   |   |-- agents-carousel.tsx
|   |   |-- activity-sparkline.tsx
|   |   |-- agent-logos.tsx    # official brand marks for the supported agents
|   |   |-- brand-ascii.ts     # SKILLS wordmark
|   |   |-- command-line.tsx   # wrapping token layout for a command
|   |   |-- hero.tsx           # Try it now / Available for these agents split
|   |   |-- install-command.tsx
|   |   |-- installation.tsx   # Installation block: Command / Prompt switch
|   |   |-- leaderboard.tsx    # search + tabs (client)
|   |   |-- leaderboard-table.tsx
|   |   |-- skill-detail.tsx   # detail page body
|   |   |-- skill-row.tsx      # click anywhere copies the install command
|   |   |-- skills-provider.tsx# runtime data fetch + revalidate
|   |   |-- site-footer.tsx
|   |   |-- site-header.tsx
|   |   |-- theme-init.tsx     # no-flash theme/language script
|   |   `-- theme-switch.tsx
|   `-- lib/
|       |-- i18n.tsx           # en/zh chrome strings
|       |-- notify.tsx         # copy confirmation via the shadcn toaster
|       |-- skills.ts          # types, install strings, filter, sort, formatting
|       |-- skills-data.ts     # build-time read of public/data/skills.json
|       |-- skills.test.ts
|       |-- use-isomorphic-layout-effect.ts
|       |-- use-resolved-theme.ts  # reads the .dark class for the toaster
|       `-- utils.ts           # cn()
|-- next.config.ts             # output: "export", BASE_PATH aware
|-- vercel.json
`-- vitest.config.ts
```

## Conventions

- Generated date/time values use UTC+8, formatted as `YYYY-MM-DD HH:mm:ss`.
- The leaderboard and detail pages only show real, repository-derived data —
  no invented install counts or activity numbers.
- Keep components small and single-purpose; page composition lives in
  `src/app/page.tsx` and `src/app/[skill]/page.tsx`, data access in
  `src/lib/skills.ts`.
- Every copy answers with the shadcn/ui (Sonner) toast at the top of the
  viewport: the card carries the exact text that went to the clipboard, and
  repeated copies stack as overlapping cards rather than queueing elsewhere.
  `src/lib/notify.tsx` is the only place that raises one.
- Lint and format with Biome (`biome.json`): `npm run lint` to check,
  `npm run lint:fix` to apply fixes.
