---
name: plan-flow
description: >
  Runs the plan lifecycle for a repository's `plans/` directory (planing /
  pending / archive): turns a non-trivial task into a plan file with scope,
  implementation tasks and a Definition of Done, ticks progress while work
  proceeds, reports progress on request, and archives the plan only when every
  task and DoD item is checked. Invoke whenever the user sends a multi-step
  task, asks to plan, split, track, resume, or archive work, or asks "how far
  along are we" in a repository that has a `plans/` directory.
---

# Plan Flow

The directory a plan lives in is its only state. Progress is the checkbox count
inside the file. Nothing else is stored, so nothing can drift.

| State | Directory | Meaning |
| --- | --- | --- |
| planing | `plans/planing/` | Designed and broken down; ready to implement |
| pending | `plans/pending/` | Blocked on a product, security, release or platform decision |
| archive | `plans/archive/` | Done; read-only except for corrections |

The `plans/README.md` of the target repository is the contract (states, P0/P1/P2
priorities, Definition of Done). Read it once before the first plan; if it
disagrees with this skill, the README wins.

## Script

All state changes go through the script, so gates are enforced rather than
remembered. Python 3.9+, standard library only. The plans root is found from
`--root`, then `PLAN_FLOW_ROOT`, then the nearest `plans/` above the working
directory.

```bash
S=skills/plan-flow/scripts/plan_flow.py

python3 $S new "Workspace boundary" --priority P0 \
  --goal "Symlinks cannot escape the workspace" \
  --task "Add realpath boundary check" --task "Add boundary tests"
python3 $S new "Release signing" --state pending --decision "Who owns the signing cert?"
python3 $S status [--state planing] [--json]
python3 $S show 01                      # numbered checkboxes
python3 $S tick 01 1 2 --note "12 boundary tests pass"   # --undo to revert
python3 $S move 02 planing              # pending -> planing
python3 $S move 01 pending --reason "Needs a decision on ..."
python3 $S move 01 archive
```

A plan is addressed by its `NN` prefix, a slug fragment, or its file name. Titles
without ASCII characters need `--slug`.

## Workflow

### 1. On receiving a task: decide whether it needs a plan

Create a plan when the task has more than one independently verifiable step,
touches more than one package or boundary, or will outlive this conversation.
Do not create one for a single edit, a question, or a one-command fix; say so
and just do the work.

Check `status` first. If an existing plan already covers the task, resume it
instead of creating a duplicate.

### 2. Create the plan

1. Choose the state. If a decision outside the code is required (product,
   security, release, platform), use `--state pending` with one `--decision`
   per open question. Otherwise `planing`.
2. Choose priority by README definition: P0 for boundary escape, credential
   leak, wrong-workspace write or uncontrolled damage; P1 for unreachable core
   features, incomplete recovery, unreliable concurrent writes or broken gates;
   P2 for the rest.
3. Run `new`, then immediately edit the file to replace every `待补充` /
   `待拆解` placeholder: goal, scope (included and excluded), tasks that are each
   independently verifiable, DoD wording specific to this plan, risk and
   rollback. Real paths, commands and numbers; no adjectives.
4. Show the user the plan path and the task list. If the goal is ambiguous,
   stop and ask before implementing.

### 3. Monitor while working

- After each task is actually finished and verified, run `tick`. Tick
  immediately, not in a batch at the end, so `status` is always true.
- Tick DoD items only with evidence: `linter_result` after lint exits 0,
  `unit_test_result` after tests pass, `func_test_result` after a real-process
  run. Put the evidence in `--note` (command, exit code, counts).
- If work reveals a decision you cannot make from the code, run
  `move <plan> pending --reason "..."` and tell the user what is needed.
- If the scope changes, edit the plan file (add or remove a task) and note why
  in the progress log; do not tick around a stale task list.
- When the user asks for progress, run `status` (or `status --json`) and
  report numbers: tasks `done/total`, DoD `done/total`, open decisions, and the
  next unchecked item. Do not paraphrase from memory.

### 4. Archive

1. Run `show` and confirm every task and DoD item is checked with evidence.
2. Fill in the `status` DoD item with remaining risks and the rollback method.
3. Run `move <plan> archive`. The script refuses when any checkbox is open,
   a DoD key is missing, a placeholder remains, or the plan is still pending.
   Fix the cause; do not edit checkboxes to get past the gate.
4. Report the archived path and the remaining risks.

Archived plans are not reopened. New work after archival is a new plan that
references the old one.

## Rules

- Never create Git commits for plan changes unless the user asks; the README
  leaves version baselines to the maintainers.
- Never hand-move plan files between state directories; use `move` so the gate
  and the progress log apply.
- Do not edit `plans/README.md` tables from this skill. The master plan is the
  single source for issue counts.
- A plan without a Definition of Done is not ready for `planing`.
- All timestamps are UTC+8, `YYYY-MM-DD HH:mm:ss`; the script writes them.

## Plan File Contract

```markdown
---
title: <title>
priority: P0|P1|P2
created: <YYYY-MM-DD HH:mm:ss>
updated: <YYYY-MM-DD HH:mm:ss>
---

# <title>

## 目标
## 范围
## 待决事项            (pending only; each item is a checkbox)
## 实施任务            (checkboxes; counted as "tasks")
## 完成标准            (code, linter_result, unit_test_result, func_test_result, status)
## 风险与回滚
## 进度日志            (appended by the script)
```

Checkboxes are classified by the section they sit in, so keep those headings.
