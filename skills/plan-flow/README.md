# Plan Flow

[中文](./README.zh-CN.md)

Turns a task you send into a plan file under a repository's `plans/` directory,
tracks progress while the agent works, and archives the plan only when it is
really done. The convention it follows is the `plans/README.md` plan center:
`planing/`, `pending/`, `archive/`, P0/P1/P2 priorities and a five-item
Definition of Done.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill plan-flow
```

## What it does

| Stage | Trigger | Result |
| --- | --- | --- |
| Plan | You send a multi-step task | `plans/planing/NN-slug.md` with goal, scope, tasks, DoD, risk and rollback. A task that needs an outside decision goes to `pending/` instead. |
| Monitor | Work proceeds, or you ask for progress | Checkboxes are ticked with evidence; `status` reports `done/total` for tasks, DoD and open decisions. |
| Archive | All work verified | `plans/archive/NN-slug.md`. The move is refused while anything is unchecked. |

## Design

- **The directory is the state.** A plan's state is the folder it sits in; its
  progress is the checkbox count in the file. There is no index or status field
  to fall out of sync.
- **Gates live in code.** `move` refuses to archive with open checkboxes, a
  missing DoD key or leftover placeholders, to leave `pending` with an open
  decision, and to reopen anything in `archive`. An agent cannot forget a rule
  the script enforces.
- **Every tick is logged** with a UTC+8 timestamp in the plan's progress log, so
  the file doubles as an audit trail.
- **No second source of truth.** It never edits the `plans/README.md` tables.

## Usage

```bash
S=skills/plan-flow/scripts/plan_flow.py

python3 $S new "Workspace boundary" --priority P0 \
  --goal "Symlinks cannot escape the workspace" \
  --task "Add realpath boundary check" --task "Add boundary tests"
python3 $S status
python3 $S show 01
python3 $S tick 01 1 2 --note "12 boundary tests pass"
python3 $S move 01 archive
```

| Command | Purpose |
| --- | --- |
| `new <title>` | Create a plan (`--priority`, `--state planing\|pending`, `--goal`, `--task`, `--decision`, `--slug`, `--number`) |
| `status` | Table of all plans with progress (`--state`, `--json`) |
| `show <plan>` | Numbered checkboxes of one plan |
| `tick <plan> N...` | Check items, append to the progress log (`--undo`, `--note`) |
| `move <plan> <state>` | `planing`, `pending` (needs `--reason`) or `archive` |

`<plan>` is the `NN` prefix, a slug fragment or the file name. The plans root is
resolved from `--root`, then `PLAN_FLOW_ROOT`, then the nearest `plans/` above
the working directory.

## Requirements

- Python 3.9+, standard library only.
- A repository with a `plans/README.md` (state directories are created on
  demand).

## Non-goals

- It does not commit to Git; version baselines stay with the maintainers.
- It does not decide priorities or scope for you; it records and enforces them.
- It does not reopen archived plans. New work is a new plan.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
