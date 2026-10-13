# Technology Selection

[中文](./README.zh-CN.md)

Turns a project request into a concrete technology decision. The skill inspects
the file system first, decides between initializing a pnpm monorepo and adding
artifacts to an existing one, applies the default stack (React + TypeScript +
Vite CSR, Tailwind CSS, shadcn/ui on the frontend; Node.js + TypeScript on the
backend; pnpm and Biome for tooling), and records a mandatory execution plan
before any scaffolding runs.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill technology-selection
```

## What it does

| Stage | Trigger | Result |
| --- | --- | --- |
| Inspect | A project, application, or library is requested | File-system state classified as empty, non-monorepo, or existing monorepo |
| Decide | State is known | Path A (initialize a pnpm monorepo) or Path B (add frontend app / backend app / React lib / TS lib) |
| Configure | Stack is chosen | Default stack applied: Vite CSR frontend with Tailwind CSS, shadcn/ui and lucide-react; Node.js + TypeScript backend; pnpm, Biome and GitHub Actions tooling |
| Record | Before any file is written | Execution plan saved to `data/execution_plans/<timestamp>_<action>_plan.md` |

## Decision rules

- **Full-stack meta-frameworks are prohibited** for generated frontend
  applications: Next.js, Remix, Nuxt, SvelteKit and friends never enter the
  default stack. Frontends are standard client-side React rendered by Vite.
- **The monorepo layout is fixed**: `apps/` for frontend applications,
  `packages/` for shared libraries, `server/` for backend applications.
- **Shared libraries are dual-format**: both ESM and CJS output plus `.d.ts`
  type definitions, whether they ship React components or plain TypeScript.
- **The execution plan is mandatory**: the decision is written down before the
  first file is created, so the architecture is reviewable after the fact.

## Bundled references

| Reference | Used for |
| --- | --- |
| [`references/vite-tailwind.md`](./references/vite-tailwind.md) | Babel plugin for JSX source location tracing plus Vite + Tailwind configuration |
| [`references/better-auth.md`](./references/better-auth.md) | Better Auth integration details for frontend authentication |
| [`references/supabase.md`](./references/supabase.md) | Supabase setup and usage as the default database |
| [`references/github-actions-git-pages.md`](./references/github-actions-git-pages.md) | GitHub Actions workflow for deploying to GitHub Pages |

## Usage

The skill runs as agent instructions; there is no script to execute. Point an
agent at a directory and ask for a new project, application, or library, and it
will follow the four steps in [`SKILL.md`](./SKILL.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE).
