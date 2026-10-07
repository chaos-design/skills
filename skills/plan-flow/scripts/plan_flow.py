#!/usr/bin/env python3
"""plan-flow: create, monitor and archive plans in a `plans/` directory.

The directory a plan lives in (`planing/`, `pending/`, `archive/`) is the only
source of its state. Progress is derived from Markdown checkboxes, so there is
no second copy of state to keep in sync.

Standard library only. All timestamps are UTC+8 (`YYYY-MM-DD HH:mm:ss`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATES = ("planing", "pending", "archive")
PRIORITIES = ("P0", "P1", "P2")
DOD_KEYS = ("code", "linter_result", "unit_test_result", "func_test_result", "status")

SECTION_KINDS = (("实施任务", "tasks"), ("完成标准", "dod"), ("待决事项", "decisions"))
LOG_HEADING = "## 进度日志"
CHECKBOX = re.compile(r"^(\s*- \[)([ xX])(\] )(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


class PlanError(Exception):
    """A user-facing failure; printed without a traceback."""


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# Root discovery
# --------------------------------------------------------------------------- #


def is_plans_root(path: Path) -> bool:
    return (path / "README.md").is_file() and any((path / s).is_dir() for s in STATES)


def find_root(explicit: str | None) -> Path:
    candidate = explicit or os.environ.get("PLAN_FLOW_ROOT")
    if candidate:
        root = Path(candidate).expanduser().resolve()
        if not root.is_dir():
            raise PlanError(f"plans root does not exist: {root}")
        return root
    for directory in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        if is_plans_root(directory):
            return directory
        if (directory / "plans" / "README.md").is_file():
            return directory / "plans"
    raise PlanError("no plans/ directory found; pass --root or set PLAN_FLOW_ROOT")


# --------------------------------------------------------------------------- #
# Plan file model
# --------------------------------------------------------------------------- #


class Plan:
    def __init__(self, path: Path):
        self.path = path
        self.state = path.parent.name
        self.lines = path.read_text(encoding="utf-8").split("\n")

    # frontmatter ----------------------------------------------------------- #

    def _frontmatter_end(self) -> int:
        if self.lines and self.lines[0] == "---":
            for i in range(1, len(self.lines)):
                if self.lines[i] == "---":
                    return i
        return -1

    def meta(self) -> dict[str, str]:
        end = self._frontmatter_end()
        out: dict[str, str] = {}
        for line in self.lines[1:end] if end > 0 else []:
            key, sep, value = line.partition(":")
            if sep:
                out[key.strip()] = value.strip()
        return out

    def set_meta(self, key: str, value: str) -> None:
        end = self._frontmatter_end()
        if end < 0:
            raise PlanError(f"{self.path.name}: missing frontmatter")
        for i in range(1, end):
            if self.lines[i].partition(":")[0].strip() == key:
                self.lines[i] = f"{key}: {value}"
                return
        self.lines.insert(end, f"{key}: {value}")

    @property
    def title(self) -> str:
        for line in self.lines:
            if line.startswith("# "):
                return line[2:].strip()
        return self.meta().get("title", self.path.stem)

    # checkboxes ------------------------------------------------------------ #

    def items(self) -> list[dict]:
        """Every checkbox outside code fences, numbered in file order."""
        items: list[dict] = []
        kind = "other"
        in_fence = False
        for idx, line in enumerate(self.lines):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if line.startswith("## "):
                kind = next((k for key, k in SECTION_KINDS if key in line), "other")
                continue
            match = CHECKBOX.match(line)
            if match:
                items.append(
                    {
                        "n": len(items) + 1,
                        "line": idx,
                        "kind": kind,
                        "done": match.group(2) in "xX",
                        "text": match.group(4).strip(),
                    }
                )
        return items

    def progress(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for item in self.items():
            done, total = out.setdefault(item["kind"], [0, 0])
            out[item["kind"]] = [done + item["done"], total + 1]
        return out

    def set_done(self, item: dict, done: bool) -> None:
        match = CHECKBOX.match(self.lines[item["line"]])
        assert match
        mark = "x" if done else " "
        self.lines[item["line"]] = f"{match.group(1)}{mark}{match.group(3)}{match.group(4)}"

    # sections -------------------------------------------------------------- #

    def append_to_section(self, heading: str, line: str) -> None:
        """Append `line` at the end of a `## heading` section, creating it if absent."""
        start = next((i for i, l in enumerate(self.lines) if l.strip() == heading), -1)
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

    def log(self, message: str) -> None:
        self.append_to_section(LOG_HEADING, f"- {now()} {message}")

    def save(self) -> None:
        self.set_meta("updated", now())
        self.path.write_text("\n".join(self.lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Lookup
# --------------------------------------------------------------------------- #


def all_plans(root: Path) -> list[Plan]:
    plans = [Plan(p) for s in STATES if (root / s).is_dir() for p in sorted((root / s).glob("*.md"))]
    return plans


def resolve(root: Path, ref: str) -> Plan:
    """Match by filename, `NN` prefix, or slug substring."""
    plans = all_plans(root)
    ref_l = ref.lower().removesuffix(".md")
    exact = [p for p in plans if p.path.stem.lower() == ref_l]
    if not exact and ref_l.isdigit():
        exact = [p for p in plans if p.path.stem.split("-")[0].lstrip("0") == ref_l.lstrip("0")]
    hits = exact or [p for p in plans if ref_l in p.path.stem.lower()]
    if not hits:
        raise PlanError(f"no plan matches '{ref}'")
    if len(hits) > 1:
        names = ", ".join(f"{p.state}/{p.path.name}" for p in hits)
        raise PlanError(f"'{ref}' is ambiguous: {names}")
    return hits[0]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def next_number(root: Path) -> int:
    numbers = [int(m.group(1)) for p in all_plans(root) if (m := re.match(r"(\d+)-", p.path.name))]
    return max(numbers, default=0) + 1


def render_plan(args: argparse.Namespace, stamp: str) -> str:
    tasks = args.task or ["待拆解：补全可独立验证的实施步骤"]
    out = [
        "---",
        f"title: {args.title}",
        f"priority: {args.priority}",
        f"created: {stamp}",
        f"updated: {stamp}",
        "---",
        "",
        f"# {args.title}",
        "",
        "## 目标",
        "",
        args.goal or "待补充：一句话说明完成后的可观察结果。",
        "",
        "## 范围",
        "",
        "- 包含：待补充",
        "- 不包含：待补充",
        "",
    ]
    if args.state == "pending":
        out += ["## 待决事项", ""]
        out += [f"- [ ] {d}" for d in args.decision]
        out += [""]
    out += ["## 实施任务", ""]
    out += [f"- [ ] {t}" for t in tasks]
    out += [
        "",
        "## 完成标准",
        "",
        "- [ ] code: 实现、迁移和文档均已完成，不保留双轨逻辑",
        "- [ ] linter_result: `corepack pnpm lint` 退出码为 0",
        "- [ ] unit_test_result: 新增边界测试通过，关键包覆盖率不低于 90%",
        "- [ ] func_test_result: 对应场景完成真实进程验证",
        "- [ ] status: 状态、剩余风险和回滚方式已记录",
        "",
        "## 风险与回滚",
        "",
        "- 风险：待补充",
        "- 回滚：待补充",
        "",
        LOG_HEADING,
        "",
        f"- {stamp} 创建（{args.state}）",
        "",
    ]
    return "\n".join(out)


def cmd_new(root: Path, args: argparse.Namespace) -> None:
    if args.state == "pending" and not args.decision:
        raise PlanError("--state pending requires at least one --decision")
    if args.state == "archive":
        raise PlanError("plans cannot be created directly in archive")
    slug = args.slug or slugify(args.title)
    if not slug:
        raise PlanError("title has no ASCII characters; pass --slug")
    number = args.number if args.number is not None else next_number(root)
    target = root / args.state / f"{number:02d}-{slug}.md"
    if any(p.path.name == target.name for p in all_plans(root)):
        raise PlanError(f"plan already exists: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_plan(args, now()), encoding="utf-8")
    print(f"created {args.state}/{target.name}")


def summarize(plan: Plan) -> dict:
    progress = plan.progress()
    meta = plan.meta()
    return {
        "state": plan.state,
        "file": plan.path.name,
        "title": plan.title,
        "priority": meta.get("priority", "-"),
        "updated": meta.get("updated", "-"),
        "progress": progress,
    }


def fmt(progress: dict[str, list[int]], kind: str) -> str:
    done, total = progress.get(kind, [0, 0])
    return f"{done}/{total}" if total else "-"


def cmd_status(root: Path, args: argparse.Namespace) -> None:
    rows = [summarize(p) for p in all_plans(root)]
    if args.state:
        rows = [r for r in rows if r["state"] == args.state]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    counts = {s: sum(r["state"] == s for r in rows) for s in STATES}
    print("  ".join(f"{s}={counts[s]}" for s in STATES))
    if not rows:
        return
    print(f"{'state':8} {'pri':3} {'tasks':6} {'dod':6} {'decide':6} {'updated':19}  plan")
    order = {s: i for i, s in enumerate(STATES)}
    for r in sorted(rows, key=lambda r: (order[r["state"]], r["priority"], r["file"])):
        p = r["progress"]
        print(
            f"{r['state']:8} {r['priority']:3} {fmt(p, 'tasks'):6} {fmt(p, 'dod'):6} "
            f"{fmt(p, 'decisions'):6} {r['updated']:19}  {r['file']}"
        )


def cmd_show(root: Path, args: argparse.Namespace) -> None:
    plan = resolve(root, args.plan)
    print(f"{plan.state}/{plan.path.name}  {plan.title}")
    for item in plan.items():
        mark = "x" if item["done"] else " "
        print(f"  {item['n']:>2}. [{mark}] ({item['kind']}) {item['text']}")


def cmd_tick(root: Path, args: argparse.Namespace) -> None:
    plan = resolve(root, args.plan)
    if plan.state == "archive":
        raise PlanError("archived plans are read-only")
    by_n = {i["n"]: i for i in plan.items()}
    for n in args.items:
        if n not in by_n:
            raise PlanError(f"{plan.path.name} has no checkbox #{n}")
    for n in args.items:
        item = by_n[n]
        plan.set_done(item, not args.undo)
        plan.log(f"{'撤销' if args.undo else '完成'} #{n} {item['text']}")
    if args.note:
        plan.log(args.note)
    plan.save()
    print(f"{plan.state}/{plan.path.name} " + " ".join(f"#{n}" for n in args.items))


def unchecked(plan: Plan, *kinds: str) -> list[dict]:
    return [i for i in plan.items() if i["kind"] in kinds and not i["done"]]


def placeholders(plan: Plan) -> list[str]:
    return [l.strip() for l in plan.lines if re.search(r"待补充|待拆解", l) and not l.startswith("- 20")]


def missing_dod(plan: Plan) -> list[str]:
    declared = {i["text"].split(":")[0].strip() for i in plan.items() if i["kind"] == "dod"}
    return sorted(set(DOD_KEYS) - declared)


def cmd_move(root: Path, args: argparse.Namespace) -> None:
    plan = resolve(root, args.plan)
    if plan.state == args.to:
        raise PlanError(f"{plan.path.name} is already in {args.to}")
    if plan.state == "archive":
        raise PlanError("archive only accepts corrections; do not reopen archived plans")

    if args.to == "archive":
        if plan.state != "planing":
            raise PlanError("only plans in planing can be archived; resolve pending decisions first")
        open_items = unchecked(plan, "tasks", "dod", "decisions")
        if open_items:
            lines = "\n".join(f"  #{i['n']} ({i['kind']}) {i['text']}" for i in open_items)
            raise PlanError(f"cannot archive; unchecked items remain:\n{lines}")
        missing = missing_dod(plan)
        if missing:
            raise PlanError("DoD is missing keys: " + ", ".join(missing))
        if placeholders(plan):
            raise PlanError("unfilled placeholders remain:\n  " + "\n  ".join(placeholders(plan)))
        plan.log("归档：任务与完成标准全部满足")
    elif args.to == "pending":
        if not args.reason:
            raise PlanError("moving to pending requires --reason (the decision that is needed)")
        plan.append_to_section("## 待决事项", f"- [ ] {args.reason}")
        plan.log(f"转入 pending：{args.reason}")
    else:  # planing, from pending
        if unchecked(plan, "decisions"):
            lines = "\n".join(f"  #{i['n']} {i['text']}" for i in unchecked(plan, "decisions"))
            raise PlanError(f"decisions still open:\n{lines}")
        missing = missing_dod(plan)
        if missing:
            raise PlanError("DoD is missing keys: " + ", ".join(missing))
        if placeholders(plan):
            raise PlanError("unfilled placeholders remain:\n  " + "\n  ".join(placeholders(plan)))
        plan.log("决策完成，转入 planing")

    plan.save()
    destination = root / args.to
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / plan.path.name
    plan.path.rename(target)
    print(f"moved {plan.state}/{plan.path.name} -> {args.to}/")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", help="plans directory (default: PLAN_FLOW_ROOT or nearest plans/)")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="create a plan from the standard template")
    new.add_argument("title")
    new.add_argument("--priority", choices=PRIORITIES, default="P1")
    new.add_argument("--state", choices=("planing", "pending"), default="planing")
    new.add_argument("--goal")
    new.add_argument("--task", action="append", help="implementation task (repeatable)")
    new.add_argument("--decision", action="append", default=[], help="open decision (repeatable)")
    new.add_argument("--slug", help="file slug; required when the title has no ASCII characters")
    new.add_argument("--number", type=int, help="override the auto-assigned NN prefix")
    new.set_defaults(func=cmd_new)

    status = sub.add_parser("status", help="list plans and their progress")
    status.add_argument("--state", choices=STATES)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    show = sub.add_parser("show", help="list a plan's numbered checkboxes")
    show.add_argument("plan", help="NN prefix, slug fragment, or file name")
    show.set_defaults(func=cmd_show)

    tick = sub.add_parser("tick", help="check (or --undo) checkboxes and log it")
    tick.add_argument("plan")
    tick.add_argument("items", type=int, nargs="+", help="checkbox numbers from `show`")
    tick.add_argument("--undo", action="store_true")
    tick.add_argument("--note", help="extra line for the progress log")
    tick.set_defaults(func=cmd_tick)

    move = sub.add_parser("move", help="change state: planing | pending | archive")
    move.add_argument("plan")
    move.add_argument("to", choices=STATES)
    move.add_argument("--reason", help="required for pending: the decision that is blocking")
    move.set_defaults(func=cmd_move)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(find_root(args.root), args)
    except PlanError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
