# Change Intake

[中文](./README.zh-CN.md)

Turn any proposed change — feature or fix, big or small — into the right
tracking structure. A short probe decides whether the repository can take
GitHub issues; if it can, the change becomes an RFC or a Task Pool with child
issues. If it cannot, planning falls back to `plan-flow` into local `plans/`.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill change-intake
```

## What it does

| Change | Mode | Main tracker | Result |
| --- | --- | --- | --- |
| New feature | `github` | GitHub | `RFC: <title>` main issue + sub-issues attached beneath it |
| Bug fix | `github` | GitHub | `Task Pool: <problem>` main issue + one fix record per task |
| Either | `local` | plan-flow | `plans/planing/NN-slug.md` with goal, tasks, DoD, risk and rollback |

A `changes/NNN-slug.md` record is written first. It holds the routing decision,
the breakdown and the hand-off — issue numbers on GitHub, the plan id locally —
so the same change is never planned twice and nothing is left untracked.

## Design

- **One decision, one record.** `probe` checks the origin remote, `gh`
  authentication and repository permissions before any issue is created. The
  reason for the chosen mode is stored in the record.
- **Remote state is linked, not copied.** Issue numbers and the plan id are
  bound back into the record; issue bodies and plan files stay authoritative.
- **Gates live in code.** `check --strict` exits non-zero while a record is
  unbound or has a binding that contradicts its mode (`--plan` on a GitHub
  record, issue numbers on a local record).
- **No duplicate RFCs.** The workflow searches existing issues before creating
  a main issue, and the script refuses a duplicate record title.
- **Honest fallback.** No GitHub remote, no `gh`, no auth, or no write
  permission means local planning — never a fabricated issue URL.

## Usage

```bash
S=skills/change-intake/scripts/change_intake.py

python3 $S init                                   # once per repository
python3 $S probe --json
python3 $S new "Add SSO login" --kind feature \
  --goal "Users can sign in with SSO" \
  --task "Add callback endpoint" --task "Verify id tokens"
python3 $S bind 001 --main 123 --child 124 --child 125   # github mode
python3 $S bind 001 --plan 07                            # local mode
python3 $S status
python3 $S check --strict
```

| Command | Purpose |
| --- | --- |
| `init` | Create `changes/README.md` once per repo |
| `probe` | Report `github`/`local`, repo slug, reason and checks (`--json`) |
| `new <title>` | Create a routing record (`--kind feature\|fix`, `--goal`, `--task`, `--slug`, `--mode`, `--repo`, `--cwd`) |
| `bind <id>` | Write back `--main` / `--child` (GitHub) or `--plan` (local), with an optional `--note` |
| `show <id>` | Numbered task breakdown of a record |
| `status` | Table of all routed changes (`--json`) |
| `check` | Report inconsistent bindings; `--strict` exits non-zero |

The root is resolved from `--root`, then `CHANGE_INTAKE_ROOT`, then the nearest
`changes/README.md` above the working directory. `--mode` and `--repo` on
`new` are rehearsal overrides for offline testing.

## GitHub details

The main issue uses the `rfc` label for features and `task-pool` for fixes;
every issue carries `change-intake`. Children are attached with the native
sub-issues API (`POST /issues/{main}/sub_issues`) and also listed as a
checklist in the main issue body. If the API is unavailable, the checklist
links remain the parent-child structure and the limitation is reported.
All issue numbers come from real `gh` output.

## Requirements

- Python 3.9+, standard library only.
- For the GitHub path: `gh` CLI, authenticated, with `triage`/`push`/
  `maintain`/`admin` permission on the repository.
- For the local path: the `plan-flow` skill and a repository `plans/README.md`.

## Non-goals

- It does not create issues itself; the agent uses `gh` so every number is real.
- It does not edit plans or tick their progress; plan-flow owns that.
- It does not push or commit; version baselines stay with the maintainers.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
