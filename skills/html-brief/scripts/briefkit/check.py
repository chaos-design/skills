"""Writing check for briefs.

The rules are adapted from ASD-STE100, the controlled English used in aircraft
maintenance manuals: short sentences, one idea per word, and steps written as
commands. Only the parts a machine can judge are checked. Findings never change
the page; `strict` mode refuses to render so an agent can fix the draft first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .parser import (
    CalloutBlock,
    CodeBlock,
    ComponentBlock,
    Heading,
    ListBlock,
    Paragraph,
    QuoteBlock,
    TableBlock,
    parse_draft,
)

WORDY_PAIRS = (
    ("in order to", "to"),
    ("prior to", "before"),
    ("utilize", "use"),
    ("utilise", "use"),
    ("leverage", "use"),
    ("at this point in time", "now"),
    ("due to the fact that", "because"),
    ("in the event that", "if"),
    ("a large number of", "many"),
    ("is able to", "can"),
    ("has the ability to", "can"),
    ("with regard to", "about"),
    ("subsequent to", "after"),
)

ZH_WORDY = (
    ("进行优化", "优化"),
    ("进行改进", "改进"),
    ("开展分析", "分析"),
    ("加以说明", "说明"),
    ("具有能力", "能"),
    ("进行了", "已"),
)

ZH_STOCK = ("赋能", "闭环", "抓手", "颗粒度", "打法", "心智")

_SENTENCE_SPLIT = re.compile(r"(?<=[。！？；])\s*|(?<=[.!?;])\s+")
_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b", re.IGNORECASE)
_CJK = re.compile(r"[\u4e00-\u9fff]")

MAX_SENTENCE_WORDS = 25
MAX_SENTENCE_CJK = 45
MAX_PARAGRAPH_SENTENCES = 6
MAX_LIST_ITEM_WORDS = 30


@dataclass
class Finding:
    line: int
    rule: str
    message: str
    hint: str = ""

    def render(self, source: str = "") -> str:
        where = f"{source + ':' if source else ''}line {self.line} · {self.rule}"
        out = f"{where}: {self.message}"
        if self.hint:
            out += f" ({self.hint})"
        return out


def _sentences(text: str) -> list[str]:
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(text) if part.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _is_cjk(text: str) -> bool:
    return bool(_CJK.search(text))


def _check_text(
    text: str, line: int, rule_prefix: str, findings: list[Finding], *, light: bool = False
) -> None:
    stripped = text.strip()
    if not stripped:
        return
    if light:
        lowered = stripped.lower()
        for wordy, better in WORDY_PAIRS:
            if wordy in lowered:
                findings.append(
                    Finding(line, f"{rule_prefix}-word", f"`{wordy}` is wordy", f"write `{better}`")
                )
        for stock in ZH_STOCK:
            if stock in stripped:
                findings.append(
                    Finding(
                        line, f"{rule_prefix}-style", f"`{stock}` is a stock phrase", "use a concrete noun"
                    )
                )
        return
    if _is_cjk(stripped):
        for sentence in _sentences(stripped):
            if len(sentence) > MAX_SENTENCE_CJK:
                findings.append(
                    Finding(
                        line,
                        f"{rule_prefix}-length",
                        f"sentence is {len(sentence)} characters",
                        f"keep a sentence under {MAX_SENTENCE_CJK}",
                    )
                )
            if sentence.count("的") >= 3:
                findings.append(
                    Finding(line, f"{rule_prefix}-density", "three or more 的 in one sentence", "replace one with a verb")
                )
            for wordy, better in ZH_WORDY:
                if wordy in sentence:
                    findings.append(
                        Finding(line, f"{rule_prefix}-word", f"`{wordy}` is wordy", f"write `{better}`")
                    )
            for stock in ZH_STOCK:
                if stock in sentence:
                    findings.append(
                        Finding(line, f"{rule_prefix}-style", f"`{stock}` is a stock phrase", "use a concrete noun or verb")
                    )
        return

    for sentence in _sentences(stripped):
        words = [word for word in re.split(r"\s+", sentence) if word]
        if len(words) > MAX_SENTENCE_WORDS:
            findings.append(
                Finding(
                    line,
                    f"{rule_prefix}-length",
                    f"sentence is {len(words)} words",
                    f"keep a sentence under {MAX_SENTENCE_WORDS}",
                )
            )
        if _PASSIVE.search(sentence):
            findings.append(
                Finding(line, f"{rule_prefix}-voice", "passive voice", "name the actor")
            )
        lowered = sentence.lower()
        for wordy, better in WORDY_PAIRS:
            if wordy in lowered:
                findings.append(
                    Finding(line, f"{rule_prefix}-word", f"`{wordy}` is wordy", f"write `{better}`")
                )


def check_draft(text: str) -> list[Finding]:
    """Check the prose of a draft. Diagram labels are left to the layout code."""
    findings: list[Finding] = []
    document = parse_draft(text)
    for panel in document.panels:
        for block in panel.blocks:
            if isinstance(block, Paragraph):
                sentences = _sentences(block.text)
                _check_text(block.text, block.line, "sentence", findings)
                if len(sentences) > MAX_PARAGRAPH_SENTENCES:
                    findings.append(
                        Finding(
                            block.line,
                            "paragraph",
                            f"paragraph has {len(sentences)} sentences",
                            f"split after {MAX_PARAGRAPH_SENTENCES}",
                        )
                    )
            elif isinstance(block, ListBlock):
                for item in block.items:
                    words = [word for word in re.split(r"\s+", item) if word]
                    if _is_cjk(item):
                        _check_text(item, block.line, "step", findings)
                    elif len(words) > MAX_LIST_ITEM_WORDS:
                        findings.append(
                            Finding(
                                block.line,
                                "step",
                                f"list item is {len(words)} words",
                                f"keep a step under {MAX_LIST_ITEM_WORDS} words",
                            )
                        )
            elif isinstance(block, (QuoteBlock, CalloutBlock)):
                _check_text(block.text, block.line, "callout", findings)
            elif isinstance(block, TableBlock):
                for row in block.rows:
                    for cell in row:
                        _check_text(cell, block.line, "cell", findings, light=True)
            elif isinstance(block, (Heading, CodeBlock, ComponentBlock)):
                continue
    return findings

