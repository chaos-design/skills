---
name: change-intake
description: >
  Routes a proposed change (large or small) into the right tracking structure.
  First probes whether the repository is on GitHub and whether the authenticated
  user can create issues. On GitHub, a planned feature becomes an RFC main issue
  with child issues attached beneath it, and a bug fix becomes a Task Pool main
  issue with fix records; a local `changes/` record is the single source of
  truth for the routing decision and the issue numbers. Without a GitHub remote,
  without gh authentication or without issue permission, it delegates planning
  to the plan-flow skill and writes the plan into the repository's `plans/`.
  Invoke whenever the user proposes a new feature, a fix, or any change that
  needs to be tracked, or asks to create an RFC, a Task Pool, or an issue plan.
---

# Change Intake

One proposed change → one routing decision → one record. The `changes/`
directory is the only local state; the real work is tracked either by GitHub
issues or by a plan-flow plan. The record holds the decision, the breakdown and
the hand-off (issue numbers or the plan id), so nothing can be planned twice
and nothing is left untracked.

| Mode | Condition | Main tracker | What gets created |
| --- | --- | --- | --- |
| `github` | GitHub origin + authenticated `gh` + issue write permission | GitHub issues | feature → `RFC: <title>` + sub-issues; fix → `Task Pool: <title>` + fix records |
| `local` | no GitHub remote, or `gh` missing/unauthenticated, or no issue permission | plan-flow plan in `plans/` | one plan with the same goal and tasks |

## Script

All routing state goes through the script, so gates are enforced rather than
remembered. Python 3.9+, standard library only. The root is found from
`--root`, then `CHANGE_INTAKE_ROOT`, then the nearest `changes/README.md` above
the working directory.

```bash
S=skills/change-intake/scripts/change_intake.py

python3 $S init                                   # once per repository
python3 $S probe [--json]                         # decide github vs local
python3 $S new "Add SSO login" --kind feature \
  --goal "Users can sign in with SSO" \
  --task "Add callback endpoint" --task "Verify id tokens"
python3 $S bind 001 --main 123 --child 124 --child 125
python3 $S bind 001 --plan 07                     # local mode only
python3 $S show 001
python3 $S status [--json]
python3 $S check --strict                         # gate: every record bound
```

`--mode github|local` and `--repo owner/name` on `new` are rehearsal overrides;
in normal use the mode comes from `probe`. `--cwd` on `probe`/`new` chooses the
repository to probe. A record is addressed by its `NNN`
id, a slug fragment, or its file name. All timestamps are UTC+8,
`YYYY-MM-DD HH:mm:ss`; the script writes them.

## Workflow

### 1. Decide whether this change needs tracking

Route any new change the user asks for — feature or fix, big or small. Say so
and skip the record only when the work is a single edit with no independently
verifiable step (a typo, a one-command fix). Do not silently skip tracking for
anything that will outlive the conversation.

### 2. Probe the environment

Run `python3 $S probe --json`. Read `mode` and `reason`:

- `github` means `git remote get-url origin` points at GitHub, `gh` is
  authenticated, and the repository permissions include `triage`, `push`,
  `maintain` or `admin`.
- `local` means one of those failed. Report the `reason` to the user before
  falling back; never assume permission you did not probe.

If the probe fails halfway (e.g. network error) treat it as `local` and say
why. A later probe can be re-run; the mode is recorded at creation time.

### 3. Classify the change

- **feature** — new capability, behavior, endpoint, interface or content that
  does not exist yet.
- **fix** — existing behavior that is wrong, a regression, or a defect with a
  reproducible symptom.

A request that mixes both is a fix if it restores intended behavior, otherwise
a feature; if genuinely ambiguous, ask the user instead of guessing.

### 4. Create the routing record

Run `new` with the title, `--kind`, a concrete `--goal` and at least one
`--task` per independently verifiable step. Then edit the generated file:
replace `待补充` in scope and risks with real paths, commands and observable
outcomes. Show the user the record path and the task list before creating
anything remote. A duplicate title is refused — resume the existing record.

### 5a. GitHub path (RFC / Task Pool)

1. Ensure the labels exist (safe to re-run):
   `gh label create rfc --color 1d76db --description "Design proposal" --force`,
   then `task-pool`, `change-intake` and `fix` the same way.
2. **Never duplicate the main issue.** Search first:
   `gh issue list --state all --label rfc --search "<title>" --json number,title,state,url`.
   Reuse an exact title match only after confirming it covers this change;
   otherwise create a new one.
3. For a **feature**, create the RFC:
   ```bash
   url=$(gh issue create --title "RFC: <title>" --label "rfc,change-intake" --body-file - <<'EOF'
   <goal, scope (included/excluded), task checklist, risks and rollback>
   EOF
   )
   main=${url##*/}
   ```
   For a **fix**, do the same with title `Task Pool: <problem>` and label
   `task-pool,change-intake`; the body is the pool of fix records with symptom,
   reproduction, expected behavior and acceptance criteria.
4. Create each child issue from the record's tasks, then attach it under the
   main issue:
   ```bash
   child_url=$(gh issue create --title "<task>" --label "change-intake,fix" \
     --body-file - <<'EOF'
   <symptom / reproduction / expected / acceptance>
   EOF
   )
   child=${child_url##*/}
   node=$(gh api repos/OWNER/REPO/issues/$child --jq .node_id)
   gh api -X POST repos/OWNER/REPO/issues/$main/sub_issues -f sub_issue_id="$node"
   ```
   Update the main issue body so its checklist shows `#<child>` for each task:
   `gh issue view $main --json body -q .body > /tmp/main.md`, edit, then
   `gh issue edit $main --body-file /tmp/main.md`.
   If the sub-issues API is unavailable, keep the checklist links as the
   parent-child structure and tell the user native sub-issues were not set.
5. Bind real numbers back to the record:
   `python3 $S bind <id> --main "$main" --child "$child" ...`. Never invent an
   issue number — take it from `gh` output.

### 5b. Local path (plan-flow)

1. Load the `plan-flow` skill and follow it. Its `plans/README.md` is the
   contract; if the repository has no `plans/README.md`, create one following
   that contract before continuing (or ask the user).
2. Create the plan with the same goal and tasks:
   `python3 skills/plan-flow/scripts/plan_flow.py new "<title>" --goal "<goal>" --task "<task>" ...`
   Choose P0/P1/P2 by that README, then replace every `待补充` / `待拆解`
   placeholder with concrete content.
3. Bind the plan id: `python3 $S bind <id> --plan <NN>`.
4. The plan file is the single source of truth for execution. Progress ticks,
   decisions and archival happen in plan-flow, not in the change record.

### 6. Progress and completion

- On GitHub, tick the main issue's checklist as children close
  (`gh issue edit <main> --body-file ...`) and report numbers from issue state.
- Locally, use plan-flow `status`, `tick` and `move` with evidence; never edit
  the checkbox count by hand.
- Run `check --strict` after binding. It fails while a record is unbound or has
  a binding that contradicts its mode.
- Report the actual record path, issue URLs or plan path, and the open items.

## Rules

- Never create a duplicate RFC or Task Pool: search issues before creating and
  refuse a duplicate local record title.
- Never create issues in local mode, and never touch `plans/` in github mode.
- Never fabricate issue numbers, plan ids, labels, or evidence; use real `gh`
  and script output.
- Never edit `changes/README.md` to work around a gate; fix the record.
- Do not create Git commits for routing changes unless the user asks.
- Timestamps are UTC+8, `YYYY-MM-DD HH:mm:ss`; the script writes them.

## Record file contract

```markdown
---
id: 001
title: <title>
kind: feature|fix
mode: github|local
repo: owner/name|-
main: ""          # main issue number, bound by `bind`
children: ""      # comma-separated child issue numbers
plan: ""          # plan-flow NN in local mode
created: <YYYY-MM-DD HH:mm:ss>
updated: <YYYY-MM-DD HH:mm:ss>
---

# <title>

## 决策
## 目标
## 拆解              (checklisted tasks; counted by `show`)
## 远端映射          (written by `bind`)
## 进度日志          (appended by the script)
```
