#!/usr/bin/env python3
"""change-intake: route a proposed change into GitHub issues or a local plan.

A local `changes/` directory is the only state. One record per proposed change
holds the routing decision, the breakdown and the hand-off to the real tracker
(issue numbers on GitHub, a plan-flow `NN` locally). The script enforces the
routing gates; it never calls `gh` or modifies `plans/` itself.

Standard library only. All timestamps are UTC+8 (`YYYY-MM-DD HH:mm:ss`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KINDS = ("feature", "fix")
MODES = ("github", "local")
ROOT_MARKER = "changes/README.md"
WRITE_PERMS = ("triage", "push", "maintain", "admin")


class IntakeError(Exception):
    """A user-facing failure; printed without a traceback."""


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# GitHub probe (pure decision + thin process wrappers)
# --------------------------------------------------------------------------- #


def parse_github_remote(url: str) -> str:
    """`git@github.com:o/r.git`, `https://github.com/o/r` -> `o/r`; else ""."""
    value = re.sub(r"\.git$", "", url.strip().rstrip("/"))
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+)$", value)
    if not match:
        return ""
    owner, name = match.groups()
    if not re.fullmatch(r"[\w.-]+", owner) or not re.fullmatch(r"[\w.-]+", name):
        return ""
    return f"{owner}/{name}"


def decide(checks: dict) -> tuple[str, str]:
    """The whole routing policy. Kept pure so it can be tested offline."""
    if not checks["github_url"]:
        return "local", "origin is not a GitHub repository"
    if not checks["gh_cli"]:
        return "local", "gh CLI is not installed"
    if not checks["gh_auth"]:
        return "local", "gh is not authenticated"
    if not checks["repo_slug"]:
        return "local", "cannot resolve owner/name"
    if not checks["issue_write"]:
        return "local", "no issue write permission on this repository"
    return "github", f"{checks['repo_slug']} accepts issues"


def run(cmd: list[str], cwd: Path | None = None) -> str:
    if not shutil.which(cmd[0]):
        return ""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def probe_checks(cwd: Path | None = None) -> dict:
    remote = run(["git", "remote", "get-url", "origin"], cwd)
    from_remote = parse_github_remote(remote)
    gh_cli = bool(shutil.which("gh"))
    gh_auth = False
    slug = ""
    if gh_cli:
        auth = subprocess.run(
            ["gh", "auth", "status"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            check=False,
        )
        gh_auth = auth.returncode == 0
    issue_write = False
    if gh_cli and gh_auth:
        slug = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd)
        slug = parse_github_remote(f"https://github.com/{slug}") if slug else from_remote
        if slug:
            raw = run(["gh", "api", f"repos/{slug}", "--jq", ".permissions"], cwd)
            try:
                perms = json.loads(raw) if raw else {}
            except ValueError:
                perms = {}
            issue_write = any(perms.get(key) is True for key in WRITE_PERMS)
    return {
        "remote": remote,
        "github_url": bool(from_remote),
        "gh_cli": gh_cli,
        "gh_auth": gh_auth,
        "repo_slug": slug,
        "issue_write": issue_write,
    }


def probe(cwd: Path | None = None) -> dict:
    checks = probe_checks(cwd)
    mode, reason = decide(checks)
    return {"mode": mode, "reason": reason, "repo": checks["repo_slug"], "checks": checks}


# --------------------------------------------------------------------------- #
# Root and record model
# --------------------------------------------------------------------------- #


def find_root(explicit: str | None) -> Path:
    candidate = explicit or os.environ.get("CHANGE_INTAKE_ROOT")
    if candidate:
        root = Path(candidate).expanduser().resolve()
        if not root.is_dir():
            raise IntakeError(f"changes root does not exist: {root}")
        return root
    here = Path.cwd().resolve()
    for directory in (here, *here.parents):
        if (directory / ROOT_MARKER).is_file():
            return directory
    raise IntakeError("no changes/ directory found; run `init` or pass --root")


class Record:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").split("\n")

    def meta(self) -> dict[str, str]:
        end = self._frontmatter_end()
        out: dict[str, str] = {}
        for line in self.lines[1:end] if end > 0 else []:
            key, sep, value = line.partition(":")
            if sep:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                out[key.strip()] = value
        return out

    def _frontmatter_end(self) -> int:
        if self.lines and self.lines[0] == "---":
            for index in range(1, len(self.lines)):
                if self.lines[index] == "---":
                    return index
        return -1

    def set_meta(self, key: str, value: str) -> None:
        end = self._frontmatter_end()
        if end < 0:
            raise IntakeError(f"{self.path.name}: missing frontmatter")
        for index in range(1, end):
            if self.lines[index].partition(":")[0].strip() == key:
                self.lines[index] = f"{key}: {value}"
                return
        self.lines.insert(end, f"{key}: {value}")

    def append_to_section(self, heading: str, line: str) -> None:
        start = next((i for i, text in enumerate(self.lines) if text.strip() == heading), -1)
        if start < 0:
            while self.lines and self.lines[-1] == "":
                self.lines.pop()
            self.lines += ["", heading, "", line, ""]
            return
        end = next(
            (i for i in range(start + 1, len(self.lines)) if self.lines[i].startswith("## ")),
            len(self.lines),
        )
        insert_at = end
        while insert_at > start + 1 and self.lines[insert_at - 1].strip() == "":
            insert_at -= 1
        self.lines.insert(insert_at, line)

    def replace_section(self, heading: str, lines: list[str]) -> None:
        start = next((i for i, text in enumerate(self.lines) if text.strip() == heading), -1)
        if start < 0:
            self.lines += ["", heading, "", *lines, ""]
            return
        end = next(
            (i for i in range(start + 1, len(self.lines)) if self.lines[i].startswith("## ")),
            len(self.lines),
        )
        self.lines[start + 1 : end] = ["", *lines, ""]

    def log(self, message: str) -> None:
        self.append_to_section("## 进度日志", f"- {now()} {message}")

    def save(self) -> None:
        self.set_meta("updated", now())
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def all_records(root: Path) -> list[Record]:
    return [Record(path) for path in sorted(root.glob("[0-9][0-9][0-9]-*.md"))]


def resolve(root: Path, ref: str) -> Record:
    records = all_records(root)
    wanted = ref.lower().removesuffix(".md")
    exact = [r for r in records if r.path.stem.lower() == wanted]
    if not exact and wanted.isdigit():
        exact = [r for r in records if r.path.stem.split("-")[0] == f"{int(wanted):03d}"]
    hits = exact or [r for r in records if wanted in r.path.stem.lower()]
    if not hits:
        raise IntakeError(f"no change record matches '{ref}'")
    if len(hits) > 1:
        names = ", ".join(r.path.name for r in hits)
        raise IntakeError(f"'{ref}' is ambiguous: {names}")
    return hits[0]


def next_number(root: Path) -> int:
    numbers = [int(m.group(1)) for p in root.glob("[0-9][0-9][0-9]-*.md") if (m := re.match(r"(\d+)-", p.name))]
    return max(numbers, default=0) + 1


init_readme = """# Change intake

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
"""


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve() if args.root else Path.cwd().resolve()
    marker = root / ROOT_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    if marker.exists():
        print(f"already initialized: {marker}")
        return
    marker.write_text(init_readme, encoding="utf-8")
    print(f"initialized {marker}")


def cmd_probe(args: argparse.Namespace) -> None:
    result = probe(Path(args.cwd).expanduser().resolve() if args.cwd else None)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"mode={result['mode']} repo={result['repo'] or '-'} reason={result['reason']}")
    for key, value in result["checks"].items():
        print(f"  {key}: {value}")


def cmd_new(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    result = probe(Path(args.cwd).expanduser().resolve() if args.cwd else None)
    mode = args.mode or result["mode"]
    if mode not in MODES:
        raise IntakeError(f"invalid mode: {mode}")
    repo = args.repo or (result["repo"] if mode == "github" else "")
    if mode == "github" and not repo:
        raise IntakeError("--repo is required when routing to GitHub without a detected remote")
    if args.kind not in KINDS:
        raise IntakeError(f"invalid --kind: {args.kind}")
    if not args.task:
        raise IntakeError("at least one --task is required; a change with no steps needs no record")

    title = args.title.strip()
    for record in all_records(root):
        existing = record.meta().get("title", "").strip().lower()
        if existing == title.lower():
            raise IntakeError(f"already routed as {record.path.name}; resume it instead of duplicating")

    slug = args.slug or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        raise IntakeError("title has no ASCII characters; pass --slug")
    number = next_number(root)
    target = root / f"{number:03d}-{slug}.md"
    stamp = now()
    kind_label = "RFC" if args.kind == "feature" else "Task Pool"
    probe_note = (
        f"手动指定（探测结果为 {result['mode']}：{result['reason']}）"
        if args.mode and args.mode != result["mode"]
        else result["reason"]
    )
    decision = (
        f"- 模式：github（仓库 {repo}；{probe_note}）"
        if mode == "github"
        else f"- 模式：local（{probe_note}；交给 plan-flow）"
    )
    lines = [
        "---",
        f"id: {number:03d}",
        f"title: {title}",
        f"kind: {args.kind}",
        f"mode: {mode}",
        f"repo: {repo or '-'}",
        'main: ""',
        'children: ""',
        'plan: ""',
        f"created: {stamp}",
        f"updated: {stamp}",
        "---",
        "",
        f"# {title}",
        "",
        "## 决策",
        "",
        decision,
        f"- 类型：{args.kind} → {kind_label} 主 issue + 子 issue"
        if mode == "github"
        else f"- 类型：{args.kind} → 本地计划（plan-flow）",
        "",
        "## 目标",
        "",
        args.goal or "待补充：一句话描述完成后的可观察结果。",
        "",
        "## 拆解",
        "",
        f"### {kind_label}: {title}（主）",
        "",
        "- 包含：待补充",
        "- 不包含：待补充",
        "",
    ]
    for task in args.task:
        lines.append(f"- [ ] {task}")
    lines += [
        "",
        "- 风险与回滚：待补充",
        "",
        "## 远端映射",
        "",
        "- 主 issue：待创建",
        "- 子 issue：待创建",
        "- 本地计划：待创建",
        "",
        "## 进度日志",
        "",
        f"- {stamp} 创建路由记录（mode={mode}, kind={args.kind}）",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"created {target.relative_to(root)}  mode={mode} kind={args.kind}")
    if mode == "github":
        print("next: create/locate the main issue with gh, child issues below it, then:")
        print(f"  change_intake.py bind {number:03d} --main N [--child N ...]")
    else:
        print("next: load the plan-flow skill, create its plan, then:")
        print(f"  change_intake.py bind {number:03d} --plan NN")


def cmd_bind(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    record = resolve(root, args.ref)
    meta = record.meta()
    mode = meta.get("mode", "")
    if args.plan and mode != "local":
        raise IntakeError(f"{record.path.name} is a github record; --plan is not allowed")
    if (args.main or args.child) and mode != "github":
        raise IntakeError(f"{record.path.name} is a local record; use --plan instead")
    if mode == "local":
        if not args.plan:
            raise IntakeError("--plan is required for a local record")
        record.set_meta("plan", args.plan)
        mapping = [f"- 本地计划：plans/planing/{args.plan}-*.md"]
    else:
        if not args.main:
            raise IntakeError("--main is required for a github record")
        children = [str(int(value)) for value in args.child]
        record.set_meta("main", str(int(args.main)))
        record.set_meta("children", ", ".join(children))
        kind = meta.get("kind", "")
        label = "RFC" if kind == "feature" else "Task Pool"
        mapping = [
            f"- 主 issue：#{args.main}（{label}）",
            f"- 子 issue：{', '.join('#' + c for c in children) if children else '无'}",
            "- 本地计划：不适用",
        ]
    record.replace_section("## 远端映射", mapping)
    record.log(args.note or f"绑定远端映射（mode={mode}）")
    record.save()
    print(f"bound {record.path.name}: {'; '.join(mapping)}")


def cmd_show(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    record = resolve(root, args.ref)
    meta = record.meta()
    print(f"{record.path.name}  {meta.get('title', '')}")
    print(f"mode={meta.get('mode', '-')} kind={meta.get('kind', '-')} repo={meta.get('repo', '-')}")
    print(
        f"main={meta.get('main') or '-'}  children={meta.get('children') or '-'}  "
        f"plan={meta.get('plan') or '-'}"
    )
    in_breakdown = False
    index = 0
    for line in record.lines:
        if line.startswith("## "):
            in_breakdown = line.strip() == "## 拆解"
            continue
        if in_breakdown and re.match(r"^- \[[ xX]\] ", line):
            index += 1
            mark = "x" if line[3] in "xX" else " "
            print(f"  {index:>2}. [{mark}] {line[6:]}")


def cmd_status(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    rows = []
    for record in all_records(root):
        meta = record.meta()
        rows.append(
            {
                "id": meta.get("id", record.path.stem[:3]),
                "title": meta.get("title", ""),
                "kind": meta.get("kind", "-"),
                "mode": meta.get("mode", "-"),
                "main": meta.get("main") or "",
                "children": len([c for c in meta.get("children", "").split(",") if c.strip()]),
                "plan": meta.get("plan") or "",
                "updated": meta.get("updated", "-"),
                "file": record.path.name,
            }
        )
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("no change records")
        return
    print(f"{'id':4} {'kind':8} {'mode':7} {'main':5} {'kids':5} {'plan':5} {'updated':19}  file")
    for row in rows:
        print(
            f"{row['id']:4} {row['kind']:8} {row['mode']:7} {row['main'] or '-':5} "
            f"{row['children']:<5} {row['plan'] or '-':5} {row['updated']:19}  {row['file']}"
        )


def cmd_check(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    problems: list[str] = []
    for record in all_records(root):
        meta = record.meta()
        ident = meta.get("id", record.path.name)
        mode = meta.get("mode", "")
        main = meta.get("main", "")
        children = [c for c in meta.get("children", "").split(",") if c.strip()]
        plan = meta.get("plan", "")
        if mode == "github":
            if not main:
                problems.append(f"{ident}: github record has no main issue")
            if plan:
                problems.append(f"{ident}: github record has a local plan binding")
        elif mode == "local":
            if not plan:
                problems.append(f"{ident}: local record has no plan-flow binding")
            if main or children:
                problems.append(f"{ident}: local record has issue bindings")
        else:
            problems.append(f"{ident}: unknown mode '{mode}'")
    if problems:
        print("\n".join(problems))
        if args.strict:
            sys.exit(1)
    else:
        print(f"ok: {len(all_records(root))} records, all bound consistently")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create changes/README.md once per repo")
    p_init.add_argument("--root")
    p_init.set_defaults(func=cmd_init)

    p_probe = sub.add_parser("probe", help="detect GitHub remote, gh auth and issue permission")
    p_probe.add_argument("--cwd")
    p_probe.add_argument("--json", action="store_true")
    p_probe.set_defaults(func=cmd_probe)

    p_new = sub.add_parser("new", help="route a proposed change into a record")
    p_new.add_argument("title")
    p_new.add_argument("--kind", required=True, choices=KINDS)
    p_new.add_argument("--goal")
    p_new.add_argument("--task", action="append", default=[])
    p_new.add_argument("--slug")
    p_new.add_argument("--mode", choices=MODES, help="rehearsal override; normally probed")
    p_new.add_argument("--repo", help="owner/name override for --mode github")
    p_new.add_argument("--cwd", help="repository to probe (defaults to the working directory)")
    p_new.add_argument("--root")
    p_new.set_defaults(func=cmd_new)

    p_bind = sub.add_parser("bind", help="write back issue numbers or a plan-flow id")
    p_bind.add_argument("ref")
    p_bind.add_argument("--main")
    p_bind.add_argument("--child", action="append", default=[])
    p_bind.add_argument("--plan")
    p_bind.add_argument("--note")
    p_bind.add_argument("--root")
    p_bind.set_defaults(func=cmd_bind)

    p_show = sub.add_parser("show", help="numbered breakdown of one record")
    p_show.add_argument("ref")
    p_show.add_argument("--root")
    p_show.set_defaults(func=cmd_show)

    p_status = sub.add_parser("status", help="table of all routed changes")
    p_status.add_argument("--json", action="store_true")
    p_status.add_argument("--root")
    p_status.set_defaults(func=cmd_status)

    p_check = sub.add_parser("check", help="assert every record is bound consistently")
    p_check.add_argument("--strict", action="store_true", help="exit non-zero on any problem")
    p_check.add_argument("--root")
    p_check.set_defaults(func=cmd_check)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except IntakeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
