#!/usr/bin/env python3
"""task-inject: inject modification feedback into a running agent's task flow.

The `.injects/` directory is the only state. Pending instructions live in
`inbox/`, consumed ones in `applied/`, and the audit trail in `LOG.md`. The
running agent reads `inbox/` at fixed checkpoints; anyone (user, another
session, an automation) can append to it at any time, including mid-run.

Four actions, ordered by severity:

  halt      stop at the next tool-call boundary; no further writes
  redirect  abandon the current direction; re-scope before continuing
  revise    finish the current atomic step, then fold the change in
  note      advisory; apply at the next natural checkpoint

Standard library only. All timestamps are UTC+8 (`YYYY-MM-DD HH:mm:ss`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ACTIONS = ("halt", "redirect", "revise", "note")
SEVERITY = {name: rank for rank, name in enumerate(ACTIONS)}
DEFAULT_DIR = ".injects"
LOG_NAME = "LOG.md"
SLUG_RE = re.compile(r"[^a-z0-9-]+")
ID_RE = re.compile(r"^(\d{3})")


class InjectError(Exception):
    """A user-facing failure; printed without a traceback."""


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# Root discovery
# --------------------------------------------------------------------------- #


def is_inject_root(path: Path) -> bool:
    return (path / "inbox").is_dir() and (path / "applied").is_dir()


def find_root(explicit: str | None) -> Path:
    candidate = explicit or os.environ.get("TASK_INJECT_ROOT")
    if candidate:
        root = Path(candidate).expanduser().resolve()
        if not is_inject_root(root):
            raise InjectError(
                f"not an inject root (needs inbox/ and applied/): {root}"
            )
        return root
    for directory in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        if is_inject_root(directory):
            return directory
        if is_inject_root(directory / DEFAULT_DIR):
            return directory / DEFAULT_DIR
    raise InjectError(
        f"no .injects/ directory found; run init or pass --root / TASK_INJECT_ROOT"
    )


def cmd_init(args: argparse.Namespace) -> None:
    default_dir = os.environ.get("TASK_INJECT_ROOT") or DEFAULT_DIR
    root = Path(args.dir if args.dir is not None else default_dir).expanduser().resolve()
    if is_inject_root(root):
        print(f"already initialised: {root}")
        return
    (root / "inbox").mkdir(parents=True, exist_ok=True)
    (root / "applied").mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text(
        "# .injects\n\n"
        "Runtime instruction inbox for a running agent (task-inject skill).\n\n"
        "- `inbox/` pending instructions; written only by `inject`\n"
        "- `applied/` consumed instructions, with applied/discard metadata\n"
        f"- `{LOG_NAME}` audit trail appended by `apply` and `discard`\n\n"
        "Actions: halt > redirect > revise > note. See the task-inject skill.\n",
        encoding="utf-8",
    )
    print(f"initialised inject root: {root}")


# --------------------------------------------------------------------------- #
# Message file model
# --------------------------------------------------------------------------- #


def next_id(root: Path) -> str:
    top = 0
    for sub in ("inbox", "applied"):
        for path in (root / sub).glob("*.md"):
            match = ID_RE.match(path.name)
            if match:
                top = max(top, int(match.group(1)))
    if top >= 999:
        raise InjectError("id space exhausted (999); archive the inject root")
    return f"{top + 1:03d}"


def slugify(text: str) -> str:
    slug = SLUG_RE.sub("-", text.lower()).strip("-")
    return "-".join(slug.split("-")[:5]) or "message"


def parse_message(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").split("\n")
    meta: dict[str, str] = {}
    if lines and lines[0] == "---":
        end = -1
        for i in range(1, len(lines)):
            if lines[i] == "---":
                end = i
                break
        if end < 0:
            raise InjectError(f"{path}: unterminated frontmatter")
        for line in lines[1:end]:
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = value.strip()
        body = "\n".join(lines[end + 1 :]).strip()
    else:
        body = "\n".join(lines).strip()
    action = meta.get("action", "")
    if action not in ACTIONS:
        raise InjectError(f"{path}: unknown or missing action: {action!r}")
    return {
        "path": path,
        "id": meta.get("id", ID_RE.match(path.name).group(1)),
        "action": action,
        "from": meta.get("from", "user"),
        "target": meta.get("target", ""),
        "created": meta.get("created", ""),
        "applied": meta.get("applied", ""),
        "note": meta.get("note", ""),
        "reason": meta.get("reason", ""),
        "discarded": meta.get("discarded", ""),
        "body": body,
    }


def set_meta(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                lines[i:i] = [f"{key}: {value}"]
                break
        path.write_text("\n".join(lines), encoding="utf-8")


def render_message(
    msg_id: str, action: str, sender: str, target: str, body: str
) -> str:
    front = [f"id: {msg_id}", f"action: {action}", f"from: {sender}"]
    if target:
        front.append(f"target: {target}")
    front.append(f"created: {now()}")
    return "---\n" + "\n".join(front) + "\n---\n\n" + body.strip() + "\n"


def atomic_write(path: Path, text: str) -> None:
    """Mid-run safe: a checkpoint never sees a half-written instruction."""
    handle, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    os.replace(tmp, path)


def append_log(root: Path, line: str) -> None:
    log = root / LOG_NAME
    if not log.exists():
        log.write_text("# Inject log\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def find_inbox(root: Path, msg_id: str) -> Path:
    for path in (root / "inbox").glob(f"{msg_id}-*.md"):
        return path
    raise InjectError(f"no pending message {msg_id} in inbox")


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_inject(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    if not args.text.strip():
        raise InjectError("instruction body is empty")
    msg_id = next_id(root)
    name = f"{msg_id}-{slugify(args.text)}.md"
    atomic_write(
        root / "inbox" / name,
        render_message(msg_id, args.action, args.sender, args.target, args.text),
    )
    print(f"injected {msg_id} ({args.action}) -> inbox/{name}")


def cmd_check(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    pending = sorted(
        (parse_message(p) for p in (root / "inbox").glob("*.md")),
        key=lambda m: (SEVERITY[m["action"]], m["id"]),
    )
    if args.json:
        print(
            json.dumps(
                [
                    {
                        k: (str(v) if k == "path" else v)
                        for k, v in m.items()
                        if k != "path"
                    }
                    | {"path": str(m["path"])}
                    for m in pending
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if not pending:
            print("inbox empty; no pending instructions")
        for m in pending:
            head = f"{m['id']} [{m['action']}]"
            if m["target"]:
                head += f" target={m['target']}"
            print(f"{head} ({m['created']})")
            print("  " + m["body"].replace("\n", "\n  "))
    if args.strict and pending:
        raise InjectError(f"{len(pending)} pending instruction(s) not drained")


def cmd_apply(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    path = find_inbox(root, args.id)
    msg = parse_message(path)
    if msg["action"] == "halt" and not args.note:
        raise InjectError(
            "a halt must be acknowledged with --note recording exactly where "
            "the run stopped (last finished step, in-flight changes)"
        )
    stamp = now()
    set_meta(path, "applied", stamp)
    if args.note:
        set_meta(path, "note", args.note.replace("\n", " "))
    target = Path(root / "applied" / path.name)
    os.replace(path, target)
    desc = "applied" if msg["action"] != "halt" else "applied (halt acknowledged)"
    tail = f" — {args.note}" if args.note else ""
    where = f", target={msg['target']}" if msg["target"] else ""
    append_log(
        root,
        f"- {stamp} {desc} {msg['id']} ({msg['action']}{where}){tail}",
    )
    print(f"{desc} {msg['id']} at {stamp}")


def cmd_discard(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    path = find_inbox(root, args.id)
    msg = parse_message(path)
    stamp = now()
    set_meta(path, "discarded", stamp)
    set_meta(path, "reason", args.reason.replace("\n", " "))
    os.replace(path, root / "applied" / path.name)
    append_log(
        root,
        f"- {stamp} discarded {msg['id']} ({msg['action']}) — {args.reason}",
    )
    print(f"discarded {msg['id']} at {stamp}")


def cmd_log(args: argparse.Namespace) -> None:
    root = find_root(args.root)
    log = root / LOG_NAME
    if not log.exists():
        print("log empty")
        return
    lines = log.read_text(encoding="utf-8").split("\n")
    if args.last:
        lines = [ln for ln in lines if ln.startswith("- ")][-args.last :]
    else:
        print(log.read_text(encoding="utf-8").rstrip())
        return
    if not lines:
        print("log empty")
        return
    for line in lines:
        print(line)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="task_inject.py",
        description="Inject and drain runtime instructions for a running agent.",
    )
    parser.add_argument(
        "--root",
        help="inject root directory (default: nearest .injects/ or TASK_INJECT_ROOT)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create an .injects/ root")
    p.add_argument(
        "--dir",
        default=None,
        help="root path (default TASK_INJECT_ROOT, else .injects)",
    )
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("inject", help="append an instruction to the inbox")
    p.add_argument("text", help="instruction body")
    p.add_argument(
        "--action", choices=ACTIONS, default="note", help="severity (default note)"
    )
    p.add_argument("--sender", default="user", help="who wrote it (default user)")
    p.add_argument("--target", default="", help="optional reference: plan id, path, step")
    p.set_defaults(func=cmd_inject)

    p = sub.add_parser("check", help="list pending instructions, halt first")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when any instruction is pending (CI gate)",
    )
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("apply", help="consume an inbox instruction")
    p.add_argument("id", help="message id, e.g. 003")
    p.add_argument("--note", default="", help="evidence: what changed / where halted")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("discard", help="withdraw a not-yet-applied instruction")
    p.add_argument("id", help="message id, e.g. 003")
    p.add_argument("reason", help="why it is withdrawn (required)")
    p.set_defaults(func=cmd_discard)

    p = sub.add_parser("log", help="show the audit trail")
    p.add_argument("--last", type=int, metavar="N", help="only the last N entries")
    p.set_defaults(func=cmd_log)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except InjectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
