# Change intake

This directory is the single source of truth for routed changes. One file per
proposal: `NNN-<slug>.md`. The file records the routing decision, the breakdown
and the hand-off to the real tracker — issue numbers on GitHub, a plan-flow
`NN` locally. Nothing here is a second copy of an issue or a plan.

| Field | Meaning |
| --- | --- |
| `mode: github` | `main` plus optional `children` issue numbers must be bound |
| `mode: local` | `plan` must be bound to a plan-flow plan |

`skills/change-intake/scripts/change_intake.py check --strict` exits non-zero
while any record is unbound or has a binding that contradicts its mode. All
timestamps are UTC+8, `YYYY-MM-DD HH:mm:ss`.
