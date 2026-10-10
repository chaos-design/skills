---
name: task-inject
description: >
  Lets a user (or an orchestrator) inject modification feedback and adjustment
  instructions into a task the agent is already executing. Instructions are
  appended to a repo's `.injects/inbox/` at any time — including mid-run — and
  the running agent drains them at fixed checkpoints. Four severity levels
  (halt / redirect / revise / note) decide whether the current step finishes,
  stops at the next tool boundary, or the whole direction is re-planned. Every
  application is acknowledged with evidence and appended to an audit log.
  Invoke whenever the user says "stop", "change direction", "also do X",
  "wait, use Y instead" while work is in progress, or asks how injected
  feedback is tracked in a repository that has a `.injects/` directory.
---

# Task Inject

The `.injects/` directory is the only state. Pending instructions are files in
`inbox/`; consumed ones move to `applied/`; the audit trail is `LOG.md`.
Nothing else is stored, so nothing can drift, and the inbox can be written
while the agent is running.

| Directory | Meaning |
| --- | --- |
| `inbox/` | Pending instructions; written only by `inject`, read by the agent at checkpoints |
| `applied/` | Consumed instructions, with `applied:`/`discarded:` metadata kept in frontmatter |
| `LOG.md` | Append-only audit trail written by `apply` and `discard` |

## Core functions

1. **Inject anywhere, anytime.** A user in another terminal, another session,
   or an automation appends an instruction without interrupting the file the
   agent is currently working from. Writes are atomic (temp file + rename), so
   a checkpoint never sees a half-written instruction.
2. **Severity-ordered drain.** `check` always surfaces `halt` first, then
   `redirect`, `revise`, `note` — the agent can never read a cosmetic note and
   miss a stop order sitting behind it.
3. **Acknowledged application.** An instruction is not silently consumed:
   `apply` stamps `applied:` and an evidence `note:` into the file, moves it to
   `applied/`, and appends one line to `LOG.md`.
4. **Enforced gates.** A `halt` cannot be applied without a note recording
   exactly where the run stopped; ids are never reused; `check --strict`
   exits non-zero while anything is pending, so CI can assert the inbox is
   drained.

## Script

All state changes go through the script, so gates are enforced rather than
remembered. Python 3.9+, standard library only. The root is found from
`--root`, then `TASK_INJECT_ROOT`, then the nearest `.injects/` above the
working directory.

```bash
S=skills/task-inject/scripts/task_inject.py

python3 $S init                                   # create .injects/ once per repo
python3 $S inject "先别动数据库" --action halt     # user side, any time
python3 $S inject "标题改成《XX 报告》" --action revise --target 01 --sender reviewer
python3 $S check [--json] [--strict]              # agent side, at checkpoints
python3 $S apply 004 --note "已停在迁移前; ..."    # consume, with evidence
python3 $S discard 003 "写错了, 撤回"              # withdraw before it is applied
python3 $S log [--last 5]                         # audit trail
```

A message is addressed by its `NNN` id. Actions, in severity order:

| Action | Meaning | When it takes effect |
| --- | --- | --- |
| `halt` | Stop everything | Next tool-call boundary; no further writes, no commit |
| `redirect` | Wrong direction | Current subtask is abandoned; re-scope before any further work |
| `revise` | Modify current work | Current atomic step finishes, then the change is folded in before moving on |
| `note` | Advisory | Next natural checkpoint; work order unchanged |

## Workflow

### 1. When to check (fixed checkpoints)

Run `check` at these points and nowhere else; between checkpoints, keep
working without polling:

1. On receiving a task, before planning it.
2. After each completed subtask or atomic step (before starting the next).
3. Before any hard-to-reverse operation: deletions, schema changes,
   dependency upgrades, `git push`, publishing.
4. Before any Git commit, plan-flow `tick`/`move`/`archive`, or final report.
5. Immediately before presenting the final answer.

### 2. How to react to each action

- **`halt`** — stop at the next tool boundary. Do not start the next command,
  write, or edit. Report: last fully finished step, what is in flight
  (uncommitted edits, running processes), what remains. Then acknowledge:
  `apply <id> --note "stopped before <X>; <in-flight state>"`. Wait for new
  instructions; do not resume on your own.
- **`redirect`** — do not continue the current direction, not even to a
  "natural stopping point". Stop, restate the new goal in your own words, and
  re-scope first (with plan-flow: edit the plan's tasks or create a new plan).
  Then `apply <id> --note "<new direction>"`.
- **`revise`** — finish the current atomic step, then incorporate the change
  before starting anything new. The change must be visible in the result, not
  just acknowledged. Then `apply <id> --note "<what changed>"`.
- **`note`** — fold it in when convenient, at the latest at the next
  checkpoint. Then `apply <id> --note "<how it was folded in>"`.

If several instructions are pending, handle them in the order `check` prints
them (severity first). A lower-severity message that conflicts with a
higher-severity one is still acknowledged, but the higher one wins.

### 3. How a new instruction reaches the agent

The agent never watches a socket or a chat stream. The channel is the repo:

```bash
python3 skills/task-inject/scripts/task_inject.py \
  inject "换掉方案 B，评审意见见邮件" --action redirect --sender reviewer
```

That writes `inbox/00N-<slug>.md`. The running agent picks it up at its next
checkpoint via `check`. This works mid-run, from another machine that shares
the repo, or from an automation that reacts to review comments.

### 4. Integration with the existing workflow

- **With plan-flow.** Use `--target <plan NN>` to bind an instruction to a
  plan. When applying a `revise`/`redirect` that targets a plan, also update
  the plan itself (edit its task list, or note the change in its progress
  log) so the plan stays the single source of truth. This skill never edits
  `plans/` directly.
- **With the normal agent loop.** Nothing in the loop changes except the five
  checkpoints; `check` is read-only and cheap.
- **With Git.** An injected change does not authorize a commit. Commits still
  follow the repository's own rules; a `halt` outranks everything, including
  plan-flow's archive gates.
- **With CI / automations.** `check --strict` exits non-zero while the inbox
  is not drained, so a pipeline can assert no instruction was dropped.

## Rules

- Never edit, delete, or reorder files in `inbox/` by hand; only `apply`,
  `discard`, and `inject` touch them.
- Never treat an instruction as read without `apply`; the log is the proof
  that feedback was received.
- A `halt` is never "applied" back to work; it is acknowledged and the run
  stops until a human says otherwise.
- Do not poll `check` in a loop; it runs at the five checkpoints only.
- All timestamps are UTC+8, `YYYY-MM-DD HH:mm:ss`; the script writes them.

## Message file contract

```markdown
---
id: 004
action: halt|redirect|revise|note
from: user|reviewer|ci|...
target: <optional: plan NN, path, or step ref>
created: <YYYY-MM-DD HH:mm:ss>
applied: <set by apply>          # discarded/reason/note likewise
---

<instruction body, one or more lines>
```

Filenames are `NNN-<slug>.md`. Ids are allocated from the highest existing id
across `inbox/` and `applied/` plus one, so they are never reused even after
the inbox is drained.
