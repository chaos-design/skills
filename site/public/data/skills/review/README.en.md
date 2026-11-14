# Review

Reviews code changes and returns actionable, severity-graded findings. Bugs
come first; structure, performance and behavior changes follow. Works from
uncommitted working-tree changes, a commit, a branch diff, or a GitHub pull
request — and when the request says "comment" / "评论", posts the finished
review to the PR via `gh`.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill review
```

## What it does

| Input | Trigger | Result |
| --- | --- | --- |
| None (default) | "review my changes" | `git diff`, `git diff --cached` and untracked files, reviewed in place |
| Commit hash | "review abc1234" | `git show <hash>` |
| Branch | "review this branch against main" | `git diff <branch>...HEAD` |
| PR URL / number | "review https://github.com/org/repo/pull/9 并且comment" | PR context plus diff via `gh pr`; review posted as a PR comment when requested |

The request is free-form: the target may sit in the same sentence as extra
instructions, so the skill extracts the target and any flags before running
anything.

## Design

- **Diffs alone are not enough.** Every modified file is read in full — code
  that looks wrong in isolation may be correct given surrounding logic, and
  vice versa. The PR body is read for stated intent; a mismatch between
  intent and diff is itself a finding.
- **Certain or silent.** A finding is only reported after investigation.
  Hypothetical problems are not flagged; when something cannot be verified,
  the review says "not sure about X" instead of guessing.
- **Scenarios, not vibes.** Each finding names the exact inputs, environment
  or scenario required for the issue to arise, because the severity depends
  on them.
- **Plain comment, no verdicts.** The PR review is posted as one ordinary
  comment (`gh pr comment --body-file`); it never submits an approving or
  blocking review, leaving the merge decision with the maintainers.

## Usage

Reviews are triggered by asking, in any of the four modes:

```text
review                              # uncommitted changes (default)
review 4d97295                      # one commit
review main...HEAD                  # branch diff
review https://github.com/org/repo/pull/9
review https://github.com/org/repo/pull/9，并且comment   # also post to the PR
```

Findings are ordered by severity:

| Label | Meaning |
| --- | --- |
| **P0** | Blocking bug; breaks in a realistic scenario |
| **P1** | Likely bug or risky behavior change; needs a fix or confirmation |
| **P2** | Minor: structure, naming, maintainability |

Each finding references `path:line`, states what breaks, the exact scenario
required, and the suggested fix. The report ends with a one-line verdict:
counts per severity and whether the change can merge as-is.

## Requirements

- `git` for diff modes; `gh` authenticated (`gh auth status`) for PR mode.
- Read access to the repository being reviewed; `gh pr checkout` for
  full-file PR context.

## Non-goals

- It does not fix the code; it reviews it. Apply fixes separately.
- It does not approve or block pull requests; the comment is advisory.
- It does not review pre-existing code outside the diff.

## License

Apache-2.0. See [`LICENSE`](https://github.com/chaos-design/skills/blob/main/skills/review/LICENSE).

