---
name: technology-selection
description: >
  Selects the appropriate technology stack, tools, and architecture for a
  project: inspect the file system, decide between initializing a pnpm
  monorepo and adding artifacts to an existing one, pick the frontend, backend
  and tooling stack, and record a mandatory execution plan. Invoke whenever the
  user asks to create a new project, add a new frontend or backend application
  or library to a codebase, or requests architecture decisions or project
  structure setup.
---

# Technology Selection

Select the appropriate technology stack, tools, and architecture for the project.

## When to use

Always run `technology-selection .` when:
- User explicitly requests to **create a new project**.
- User requests to **add a new application** (frontend or backend) or **library** to the codebase.
- User requests architecture decisions or project structure setup.

## How to use

### Step 1: Analyze Project State & Requirements

Before making decisions, inspect the current file system state.

1.  **Check File System State**:
    - Is the current directory **empty** (or contains only hidden files like `.git`)?
    - Does a **Monorepo Configuration** exist? (Look for `pnpm-workspace.yaml`, `lerna.json`, `turbo.json`, or `workspaces` in `package.json`).

2.  **Determine Action Path**:
    - **Path A: Initialize Monorepo**:
        - IF (Directory is Empty) OR (Directory is NOT Empty AND No Monorepo Config found).
        - **Action**: Create a new Monorepo structure.
    - **Path B: Add to Monorepo**:
        - IF (Monorepo Config found).
        - **Action**: Create specific artifacts (App/Lib) based on user request.

### Step 2: Determine Project Architecture

#### Path A: Initialize Monorepo (Default for Empty/Non-Monorepo)
- **Tooling**: pnpm (package manager), Biome (formatter/linter)
- **Directory Structure**:
  - `apps/`: Frontend applications
  - `packages/`: Shared libraries
  - `server/`: Backend applications
- **Configuration**:
  - Create `pnpm-workspace.yaml`
  - Initialize `package.json`
  - Setup Biome configuration

#### Path B: Add Artifacts (For Existing Monorepo)
Identify what needs to be created:

1.  **Frontend Application**
    - **Location**: `apps/<app-name>`
    - **Stack**: React + TypeScript + Vite + Tailwind CSS
    - **Constraint**: **STRICTLY PROHIBITED**: Next.js, Remix, Nuxt, or any full-stack meta-frameworks. Use standard Client-Side Rendering (CSR) with Vite.
    - **Actions**: Setup Vite (with JSX source tracing), Tailwind, Shadcn/UI.

2.  **Backend Application**
    - **Location**: `server/<service-name>`
    - **Stack**: Node.js + TypeScript (Hono/Express/NestJS based on need)

3.  **Shared Capabilities (Libraries)**
    - **Location**: `packages/<lib-name>`
    - **Type 1: React Components** (UI Kit)
        - **Stack**: React + TypeScript + Tailwind
        - **Usage**: Export components or lib for apps or server to consume.
        - **Output**: Support **ESM** and **CJS** formats, and include **Type Definitions** (`.d.ts`).
    - **Type 2: TypeScript Capabilities** (Utils/Config/Logic)
        - **Stack**: TypeScript (No React)
        - **Usage**: Shared logic, types, or constants.
        - **Output**: Support **ESM** and **CJS** formats, and include **Type Definitions** (`.d.ts`).

### Step 3: Select Technology Stack Details

#### Frontend Stack (Default)
- **Framework**: React + TypeScript (Vite-based CSR)
- **Prohibited**: Next.js, Remix, Nuxt, SvelteKit, or any SSR/Full-stack framework.
- **Styling**: Tailwind CSS
- **Icons**: lucide-react
- **UI Library**: shadcn/ui
- **Build Tool**: Vite
- **Special Configurations**:
  - **Vite + Tailwind**: Must include Babel plugin for JSX source tracing (See Data: ViteTailwindConfig)
  - **Auth**: Better Auth (See Data: BetterAuth)
  - **DB**: Supabase (See Data: Supabase)

#### Backend Stack (Default)
- **Runtime**: Node.js
- **Language**: TypeScript

#### Tooling & Infrastructure
- **Package Manager**: pnpm
- **Formatter/Linter**: Biome
- **CI/CD**: GitHub Actions (See Data: GitHubActionsGitPages)

### Step 4: Output Decision Plan & Log Execution

1.  **Summarize the execution plan**:
    - **Current State**: (Empty / No-Monorepo / Existing-Monorepo)
    - **Action**: (Initialize Monorepo / Add Frontend App / Add Backend App / Add React Lib / Add TS Lib)
    - **Structure**: Define paths for new files.
    - **Tech Stack**: Confirm tools being used.
    - **Configuration Actions**: List specific setup steps (pnpm init, vite create, etc.).

2.  **Save Execution Plan (Mandatory)**:
    - **Action**: Create a markdown file recording the **Execution Plan**.
    - **Location**: `<monorepo-root>/data/execution_plans/<YYYYMMDD_HHmmss>_<action_type>_plan.md`
    - **Content**:
      - **User Requirement**: The original request.
      - **Architecture Decision**: The selected path and stack.
      - **Planned Steps**: The detailed list of actions to be executed (e.g., file creation, command execution).

## Data

### ViteTailwindConfig

See [references/vite-tailwind.md](./references/vite-tailwind.md) for Babel plugin and Vite configuration details.

### BetterAuth

See [references/better-auth.md](./references/better-auth.md) for implementation details.

### GitHubActionsGitPages

See [references/github-actions-git-pages.md](./references/github-actions-git-pages.md) for workflow configuration details.

### Supabase

See [references/supabase.md](./references/supabase.md) for implementation details.
