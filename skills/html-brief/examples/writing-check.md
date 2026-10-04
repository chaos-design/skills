---
title: Writing check, line by line
subtitle: What the draft looked like before the check ran
theme: document
mode: auto
---

## Annotated sentence {span=2}

```annot
The {bad|service} {warn|was restarted} by the operator before the {fix|retry budget expired}, and {good|alerts fired within one minute}.
```

> note: The check reads machine-checkable rules only
>
> Sentence length, passive voice, wordy pairs, empty verbs in Chinese and stock
> phrases. A callout with a blank quote line gets a title; one without it stays
> a single body paragraph, however the source wraps it.

## Findings from one draft {span=2}

```limits
Sentence length | 34 words | 100% | limit is 25 words
Passive voice | 3 | 45% | limit is 0
Wordy pairs | 2 | 30% | in order to, prior to
Stock phrases | 1 | 20% | 赋能
```

> tip: Run with `--check warn` while drafting. Switch to `--check strict` when
> the brief ships, so a page is never produced from a draft that still has
> findings.

## Shortest rewrite {span=2}

1. Name the actor: the operator restarted the service.
2. Cut the length: the retry budget expired first.
3. Replace the pair: use `before`, not `prior to`.

```flow LR
draft -> check: findings
check -> agent: line, rule, hint
agent -> draft: one corrected line
agent -> page: render
```

## Commands

```bash
python3 scripts/html_brief.py check draft.md
python3 scripts/html_brief.py render draft.md --check strict --out brief.html
```