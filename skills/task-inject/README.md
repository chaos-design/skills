# Task Inject

[中文](./README.zh-CN.md)

Lets you inject modification feedback and adjustment instructions into a task
the agent is already executing — mid-run, from another terminal, another
session, or an automation. The running agent picks instructions up at fixed
checkpoints, reacts according to their severity, and acknowledges every
application with evidence in an audit log.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill task-inject
```

## What it does

| Stage | Who | Result |
| --- | --- | --- |
| Inject | You, any time | `inbox/NNN-slug.md` with an action (`halt`/`redirect`/`revise`/`note`), an optional target, and the instruction body. Writes are atomic, so it is safe while the agent runs. |
| Check | Agent, at fixed checkpoints | `check` lists pending instructions with `halt` first, so a stop order is never hidden behind a cosmetic note. |
| Apply | Agent | The instruction is folded in (or the run stops), then stamped `applied:` with an evidence note, moved to `applied/`, and logged. |
| Audit | Anyone | `LOG.md` records every applied or discarded instruction with a UTC+8 timestamp. |

Severity decides what happens to the current work:

| Action | Effect |
| --- | --- |
| `halt` | Stop at the next tool-call boundary. No further writes, no commit. Report state and wait. |
| `redirect` | Abandon the current direction; re-scope before any further work. |
| `revise` | Finish the current atomic step, then fold the change in before moving on. |
| `note` | Advisory; apply at the next natural checkpoint, work order unchanged. |

## Design

Detailed architecture, message lifecycle, checkpoint decision procedure and the
principles behind each choice: [docs/design.md](docs/design.md) ·
[设计说明（中文）](docs/design.zh-CN.md).

- **The directory is the state.** Pending instructions are files in `inbox/`,
  consumed ones in `applied/`; the log is append-only. Nothing can drift.
- **Injection is decoupled from execution.** The channel is the repo itself,
  so feedback works mid-run, across machines that share the repo, and from
  automations — without sockets or chat streams.
- **Gates live in code.** A `halt` cannot be applied without a note recording
  exactly where the run stopped; ids are never reused; `check --strict`
  exits non-zero while anything is pending, so CI can assert a drained inbox.
- **Acknowledged consumption.** Instructions are never read silently; `apply`
  is the proof that feedback was received, and what was done about it.
- **Composes with plan-flow.** `--target <plan NN>` binds an instruction to a
  plan; the plan file itself stays the single source of truth.

## Usage

```bash
S=skills/task-inject/scripts/task_inject.py

python3 $S init                                     # once per repo: creates .injects/
# --- you, while the agent works ---
python3 $S inject "先别动数据库" --action halt
python3 $S inject "改做 CLI，不是 Web" --action redirect --sender reviewer
python3 $S inject "标题改成《XX 报告》" --action revise --target 01
python3 $S discard 003 "写错了，撤回"
# --- the agent, at its checkpoints ---
python3 $S check [--json] [--strict]
python3 $S apply 004 --note "已停在迁移前；最后一个完成步骤是 schema 复核"
python3 $S log [--last 5]
```

| Command | Purpose |
| --- | --- |
| `init [--dir]` | Create the `.injects/` root (`inbox/`, `applied/`, `README.md`); default dir is `TASK_INJECT_ROOT`, else `.injects` |
| `inject <text>` | Append an instruction (`--action`, `--sender`, `--target`) |
| `check` | Pending instructions, severity-first (`--json`, `--strict`) |
| `apply <id>` | Consume one instruction with an evidence note (`--note`) |
| `discard <id> <reason>` | Withdraw a not-yet-applied instruction (reason required) |
| `log [--last N]` | Audit trail of applications and discards |

The root is resolved from `--root`, then `TASK_INJECT_ROOT`, then the nearest
`.injects/` above the working directory.

## When the agent checks

Five fixed checkpoints, and no polling in between:

1. On receiving a task, before planning it.
2. After each completed subtask, before starting the next.
3. Before any hard-to-reverse operation (deletion, schema change, upgrade,
   push, publish).
4. Before any Git commit, plan-flow progress tick or archive, or final report.
5. Immediately before presenting the final answer.

## Requirements

- Python 3.9+, standard library only.
- A repository with an `.injects/` directory (created by `init`).

## Non-goals

- It does not interrupt a tool call that is already running; `halt` takes
  effect at the next boundary.
- It does not commit to Git; an injected change never authorizes a commit.
- It does not edit `plans/` directly; re-scoping goes through plan-flow.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
