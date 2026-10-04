"""SVG diagram components: flow, sequence, tree and timeline.

All geometry is computed here. The renderer never asks the model for
coordinates and never guesses: node boxes come from measured label widths,
edges route around other nodes, and every diagram is normalized to its own
bounding box before it is written out.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .parser import DraftError
from .textutil import esc, text_px, wrap_text

FONT = 12.5
LABEL_FONT = 11.5
LINE_H = 17
PAD_X = 13
PAD_Y = 9
MIN_NODE_W = 84.0
MIN_NODE_H = 38.0

ARROW_HEAD = 8.0
MUTED = "var(--muted)"

_ARROW_RE = re.compile(r"\s*(-\.->|==>|-->|->)\s*")
_GROUP_OPEN_RE = re.compile(r"^group\s+(?P<name>.+?)\s*\{$")
_GROUP_CLOSE_RE = re.compile(r"^\}$")
_FRAGMENT_OPEN_RE = re.compile(
    r"^(?P<kind>alt|opt|loop|par|try|critical|break)\b(?P<rest>.*?)\s*\{$", re.IGNORECASE
)
_FRAGMENT_ELSE_RE = re.compile(r"^}\s*(?:else|elif|optional)?\s*(?P<label>.*?)\s*\{$", re.IGNORECASE)
_PARTICIPANT_RE = re.compile(r"^participant\s+(?P<name>.+?)(?:\s+as\s+(?P<label>.+))?$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# shared svg helpers
# --------------------------------------------------------------------------- #
def _n(value: float) -> str:
    return f"{value:.1f}"


def rounded_path(points: list[tuple[float, float]], radius: float = 9.0) -> str:
    """Orthogonal polyline with rounded corners."""
    clean = [points[0]]
    for point in points[1:]:
        if abs(point[0] - clean[-1][0]) > 0.01 or abs(point[1] - clean[-1][1]) > 0.01:
            clean.append(point)
    if len(clean) < 2:
        return ""
    parts = [f"M {_n(clean[0][0])} {_n(clean[0][1])}"]
    for index in range(1, len(clean) - 1):
        prev, corner, nxt = clean[index - 1], clean[index], clean[index + 1]
        v1 = (prev[0] - corner[0], prev[1] - corner[1])
        v2 = (nxt[0] - corner[0], nxt[1] - corner[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if l1 < 0.01 or l2 < 0.01:
            continue
        trim = min(radius, l1 / 2, l2 / 2)
        start = (corner[0] + v1[0] / l1 * trim, corner[1] + v1[1] / l1 * trim)
        end = (corner[0] + v2[0] / l2 * trim, corner[1] + v2[1] / l2 * trim)
        parts.append(f"L {_n(start[0])} {_n(start[1])}")
        parts.append(f"Q {_n(corner[0])} {_n(corner[1])} {_n(end[0])} {_n(end[1])}")
    parts.append(f"L {_n(clean[-1][0])} {_n(clean[-1][1])}")
    return " ".join(parts)


def bezier_point(p0, p1, p2, p3, t: float) -> tuple[float, float]:
    mt = 1 - t
    a = mt ** 3
    b = 3 * mt * mt * t
    c = 3 * mt * t * t
    d = t ** 3
    return (
        a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
        a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
    )


def arrow_head(tip: tuple[float, float], direction: tuple[float, float], size: float = ARROW_HEAD) -> str:
    dx, dy = direction
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    base = (tip[0] - ux * size, tip[1] - uy * size)
    left = (base[0] - uy * size * 0.42, base[1] + ux * size * 0.42)
    right = (base[0] + uy * size * 0.42, base[1] - ux * size * 0.42)
    points = (
        f"{_n(tip[0])},{_n(tip[1])} {_n(left[0])},{_n(left[1])} {_n(right[0])},{_n(right[1])}"
    )
    return f'<polygon class="edge-head" points="{points}" />'


def text_node(
    text: str,
    x: float,
    y: float,
    size: float = FONT,
    anchor: str = "middle",
    cls: str = "node-label",
    fill: str | None = None,
) -> str:
    style = f' style="fill:{fill}"' if fill else ""
    return (
        f'<text class="{cls}" x="{_n(x)}" y="{_n(y)}" font-size="{size}" '
        f'text-anchor="{anchor}" dominant-baseline="middle"{style}>{esc(text)}</text>'
    )


class Canvas:
    """Collects svg fragments together with the bounding box they occupy."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.min_x = math.inf
        self.min_y = math.inf
        self.max_x = -math.inf
        self.max_y = -math.inf

    def add(self, fragment: str) -> None:
        self.parts.append(fragment)

    def extend(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.min_x = min(self.min_x, x0, x1)
        self.min_y = min(self.min_y, y0, y1)
        self.max_x = max(self.max_x, x0, x1)
        self.max_y = max(self.max_y, y0, y1)

    def point(self, x: float, y: float) -> None:
        self.extend(x, y, x, y)

    def render(self, label: str, margin: float = 16.0) -> str:
        if not math.isfinite(self.min_x):
            self.min_x = self.min_y = 0.0
            self.max_x = self.max_y = 1.0
        bbox = f' data-bbox="{_n(self.min_x)} {_n(self.min_y)} {_n(self.max_x)} {_n(self.max_y)}"'
        body = f'<g transform="translate({_n(margin - self.min_x)},{_n(margin - self.min_y)})">'
        body += "".join(self.parts) + bbox + "</g>"
        width = self.max_x - self.min_x + margin * 2
        height = self.max_y - self.min_y + margin * 2
        return (
            f'<figure class="diagram" role="img" aria-label="{esc(label)}">'
            f'<svg viewBox="0 0 {_n(width)} {_n(height)}" width="{_n(width)}" height="{_n(height)}" '
            f'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">'
            f"<title>{esc(label)}</title>{body}</svg></figure>"
        )


def place_label_box(x: float, y: float, label: str, anchor: str, placed: list[list[float]]) -> tuple[float, float]:
    """Nudge a label along the vertical axis until it clears the others.

    Parallel edges out of one node put their labels on nearly the same spot.
    A short search beats hand-tuned offsets because it adapts to any graph.
    """
    width = text_px(label, LABEL_FONT) + 8
    left = x if anchor == "start" else x - width / 2
    box = [left, y - 9, left + width, y + 5]
    if not any(_overlaps(box, other) for other in placed):
        placed.append(box)
        return x, y
    for offset in (14, -14, 28, -28, 42, -42):
        moved = [box[0], box[1] + offset, box[2], box[3] + offset]
        if moved[1] < -60 or not any(_overlaps(moved, other) for other in placed):
            placed.append(moved)
            return x, y + offset
    placed.append(box)
    return x, y


def _overlaps(a: list[float], b: list[float]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def edge_label(x: float, y: float, label: str, anchor: str = "middle") -> str:
    width = text_px(label, LABEL_FONT)
    left = x - width / 2 - 4 if anchor == "middle" else x - 4
    return (
        f'<rect class="edge-label-bg" x="{_n(left)}" y="{_n(y - 9)}" width="{_n(width + 8)}" '
        f'height="14" rx="4" />'
        + text_node(label, x, y - 1, size=LABEL_FONT, cls="edge-label", anchor=anchor, fill=MUTED)
    )


# --------------------------------------------------------------------------- #
# flow
# --------------------------------------------------------------------------- #
@dataclass
class FlowNode:
    label: str
    shape: str = "rect"
    emphasis: bool = False
    group: str = ""
    order: int = 0
    width: float = 0.0
    height: float = 0.0
    cx: float = 0.0
    cy: float = 0.0
    lines: list[str] = field(default_factory=list)


@dataclass
class FlowEdge:
    src: str
    dst: str
    label: str = ""
    style: str = "solid"
    backward: bool = False


def _parse_endpoint(token: str) -> tuple[str, str, bool]:
    text = token.strip()
    emphasis = len(text) > 1 and text.startswith("*") and text.endswith("*")
    if emphasis:
        text = text[1:-1].strip()
    wrappers = (
        ("[[", "]]", "parallel"),
        ("[(", ")]", "cylinder"),
        ("((", "))", "round"),
        ("{", "}", "diamond"),
        ("(", ")", "stadium"),
    )
    for opener, closer, shape in wrappers:
        if text.startswith(opener) and text.endswith(closer) and len(text) > len(opener) + len(closer):
            return text[len(opener) : -len(closer)].strip(), shape, emphasis
    return text, "rect", emphasis


def _split_arrow(line: str) -> tuple[str, str, str] | None:
    depth = 0
    index = 0
    while index < len(line):
        char = line[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif depth == 0:
            match = _ARROW_RE.match(line, index)
            if match:
                return line[:index].strip(), match.group(1), line[match.end() :].strip()
        index += 1
    return None


def _split_label(rest: str) -> tuple[str, str]:
    depth = 0
    for index, char in enumerate(rest):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == ":" and depth == 0:
            return rest[:index].strip(), rest[index + 1 :].strip()
    return rest.strip(), ""


def parse_flow(
    text: str, line: int
) -> tuple[dict[str, FlowNode], list[FlowEdge], dict[str, list[str]]]:
    example = (
        "```flow LR\nGateway -> Service: rpc\n{payload ok} -> Cache: read\n"
        "(Query) -> *Response*\ngroup Edge {\n  A -> B\n}\n```"
    )
    nodes: dict[str, FlowNode] = {}
    edges: list[FlowEdge] = []
    groups: dict[str, list[str]] = {}
    stack: list[str] = []

    for offset, raw in enumerate(text.split("\n"), start=1):
        line_text = raw.strip()
        if not line_text or line_text.startswith("#"):
            continue
        group_open = _GROUP_OPEN_RE.match(line_text)
        if group_open:
            stack.append(group_open.group("name").strip())
            groups.setdefault(stack[-1], [])
            continue
        if _GROUP_CLOSE_RE.match(line_text):
            if not stack:
                raise DraftError(
                    "`}` closes a group that was never opened", line + offset, "flow", example
                )
            stack.pop()
            continue
        parts = _split_arrow(line_text)
        if not parts:
            raise DraftError(
                "every flow line needs an arrow between two nodes", line + offset, "flow", example
            )
        src_token, arrow, rest = parts
        dst_token, edge_label_text = _split_label(rest)
        src_label, src_shape, src_emphasis = _parse_endpoint(src_token)
        dst_label, dst_shape, dst_emphasis = _parse_endpoint(dst_token)
        if not src_label or not dst_label:
            raise DraftError("an arrow needs a node label on both sides", line + offset, "flow", example)
        for node_label in (src_label, dst_label):
            if node_label.startswith("[") and not node_label.startswith("[["):
                raise DraftError(
                    f"node `{node_label}` uses square brackets, which are part of the label",
                    line + offset,
                    "flow",
                    example,
                )
        for node_label, shape, emphasis in (
            (src_label, src_shape, src_emphasis),
            (dst_label, dst_shape, dst_emphasis),
        ):
            existing = nodes.get(node_label)
            if existing is not None:
                if shape != "rect" and existing.shape != shape:
                    raise DraftError(
                        f"node `{node_label}` is already declared as `{existing.shape}`",
                        line + offset,
                        "flow",
                        example,
                    )
                existing.emphasis = existing.emphasis or emphasis
                continue
            nodes[node_label] = FlowNode(
                node_label,
                shape,
                emphasis,
                group=stack[-1] if stack else "",
                order=len(nodes),
            )
            if stack:
                groups[stack[-1]].append(node_label)
        style = {"-.->": "dashed", "==>": "bold"}.get(arrow, "solid")
        edges.append(FlowEdge(src_label, dst_label, edge_label_text, style))

    if stack:
        raise DraftError(f"group `{stack[-1]}` is never closed with `}}`", line, "flow", example)
    if not nodes:
        raise DraftError("flow diagram has no nodes", line, "flow", example)
    return nodes, edges, groups


def _measure_node(node: FlowNode, max_label_px: float) -> None:
    node.lines = wrap_text(node.label, FONT, max_label_px)
    widest = max(text_px(item, FONT) for item in node.lines)
    text_h = len(node.lines) * LINE_H
    if node.shape == "diamond":
        node.width = max(112.0, widest * 1.85 + PAD_X)
        node.height = max(60.0, text_h * 1.85 + PAD_Y)
    elif node.shape == "parallel":
        node.width = max(108.0, widest * 1.3 + PAD_X)
        node.height = max(MIN_NODE_H, text_h + PAD_Y * 2)
    elif node.shape == "cylinder":
        node.width = max(104.0, widest + PAD_X * 2 + 8)
        node.height = max(MIN_NODE_H + 12, text_h + PAD_Y * 2 + 14)
    else:
        node.width = max(MIN_NODE_W, widest + PAD_X * 2)
        node.height = max(MIN_NODE_H, text_h + PAD_Y * 2)


def _mark_back_edges(nodes: dict[str, FlowNode], edges: list[FlowEdge]) -> set[int]:
    """Depth-first search that flags edges pointing at an active ancestor."""
    adjacency: dict[str, list[FlowEdge]] = {name: [] for name in nodes}
    for edge in edges:
        if edge.src != edge.dst and edge.dst in adjacency:
            adjacency[edge.src].append(edge)
    white, gray, black = 0, 1, 2
    color = {name: white for name in nodes}
    back: set[int] = set()
    for start in nodes:
        if color[start] != white:
            continue
        color[start] = gray
        stack: list[tuple[str, object]] = [(start, iter(adjacency[start]))]
        while stack:
            name, iterator = stack[-1]
            descended = False
            for edge in iterator:  # type: ignore[union-attr]
                target = edge.dst
                if color[target] == gray:
                    back.add(id(edge))
                elif color[target] == white:
                    color[target] = gray
                    stack.append((target, iter(adjacency[target])))
                    descended = True
                    break
            if not descended:
                color[name] = black
                stack.pop()
    return back


def _layer_graph(
    nodes: dict[str, FlowNode], edges: list[FlowEdge]
) -> tuple[dict[str, int], list[list[str]]]:
    back = _mark_back_edges(nodes, edges)
    ranked_edges: list[FlowEdge] = []
    for edge in edges:
        if edge.src == edge.dst:
            continue
        if id(edge) in back:
            edge.backward = True
            ranked_edges.append(FlowEdge(edge.dst, edge.src))
        else:
            ranked_edges.append(edge)
    rank = {name: 0 for name in nodes}
    for _ in range(len(nodes) + 1):
        changed = False
        for edge in ranked_edges:
            if rank[edge.dst] < rank[edge.src] + 1:
                rank[edge.dst] = rank[edge.src] + 1
                changed = True
        if not changed:
            break
    buckets: dict[int, list[str]] = {}
    for name in sorted(nodes, key=lambda key: nodes[key].order):
        buckets.setdefault(rank[name], []).append(name)
    return rank, [buckets[key] for key in sorted(buckets)]


def _count_crossings(layers: list[list[str]], edges: list[FlowEdge]) -> int:
    rank: dict[str, int] = {}
    for index, layer in enumerate(layers):
        for name in layer:
            rank[name] = index
    total = 0
    for index in range(len(layers) - 1):
        pairs: list[tuple[int, int]] = []
        for edge in edges:
            if edge.src == edge.dst:
                continue
            if rank.get(edge.src) != index or rank.get(edge.dst) != index + 1:
                continue
            pairs.append((layers[index].index(edge.src), layers[index + 1].index(edge.dst)))
        pairs.sort()
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                if pairs[i][0] < pairs[j][0] and pairs[i][1] > pairs[j][1]:
                    total += 1
    return total


def _order_layers(layers: list[list[str]], edges: list[FlowEdge]) -> list[list[str]]:
    ordered = [list(layer) for layer in layers]
    if len(ordered) < 2:
        return ordered
    for iteration in range(8):
        use_successors = iteration % 2 == 0
        for index, layer in enumerate(ordered):
            if use_successors:
                neighbour_layer = ordered[index + 1] if index + 1 < len(ordered) else []
            else:
                neighbour_layer = ordered[index - 1] if index > 0 else []
            position = {name: pos for pos, name in enumerate(neighbour_layer)}
            keyed: list[tuple[float, int, str]] = []
            for fallback, name in enumerate(layer):
                neighbours: list[int] = []
                for edge in edges:
                    if edge.src == edge.dst:
                        continue
                    if use_successors and edge.src == name and edge.dst in position:
                        neighbours.append(position[edge.dst])
                    elif not use_successors and edge.dst == name and edge.src in position:
                        neighbours.append(position[edge.src])
                median = float(fallback)
                if neighbours:
                    neighbours.sort()
                    middle = len(neighbours) // 2
                    median = (
                        float(neighbours[middle])
                        if len(neighbours) % 2
                        else (neighbours[middle - 1] + neighbours[middle]) / 2
                    )
                keyed.append((median, fallback, name))
            keyed.sort(key=lambda item: (item[0], item[1]))
            ordered[index] = [item[2] for item in keyed]

        improved = True
        while improved:
            improved = False
            best = _count_crossings(ordered, edges)
            for index in range(len(ordered) - 1):
                layer = ordered[index]
                for position in range(len(layer) - 1):
                    layer[position], layer[position + 1] = layer[position + 1], layer[position]
                    candidate = _count_crossings(ordered, edges)
                    if candidate < best:
                        best = candidate
                        improved = True
                    else:
                        layer[position], layer[position + 1] = layer[position + 1], layer[position]
            if best == 0:
                break
    return ordered


def _node_shape_svg(node: FlowNode) -> str:
    x = node.cx - node.width / 2
    y = node.cy - node.height / 2
    w = node.width
    h = node.height
    cls = "node node-emph" if node.emphasis else "node"
    if node.shape == "diamond":
        points = (
            f"{_n(node.cx)},{_n(y)} {_n(x + w)},{_n(node.cy)} "
            f"{_n(node.cx)},{_n(y + h)} {_n(x)},{_n(node.cy)}"
        )
        return f'<polygon class="{cls}" points="{points}" />'
    if node.shape == "parallel":
        skew = 14.0
        points = (
            f"{_n(x + skew)},{_n(y)} {_n(x + w)},{_n(y)} "
            f"{_n(x + w - skew)},{_n(y + h)} {_n(x)},{_n(y + h)}"
        )
        return f'<polygon class="{cls}" points="{points}" />'
    if node.shape == "stadium":
        return (
            f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" '
            f'height="{_n(h)}" rx="{_n(h / 2)}" />'
        )
    if node.shape == "round":
        return (
            f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" '
            f'height="{_n(h)}" rx="{_n(min(12.0, h / 2))}" />'
        )
    if node.shape == "cylinder":
        cap = 9.0
        return (
            f'<path class="{cls}" d="M {_n(x)} {_n(y + cap)} '
            f"A {_n(w / 2)} {_n(cap)} 0 0 1 {_n(x + w)} {_n(y + cap)} "
            f"L {_n(x + w)} {_n(y + h - cap)} "
            f"A {_n(w / 2)} {_n(cap)} 0 0 1 {_n(x)} {_n(y + h - cap)} Z "
            f'M {_n(x)} {_n(y + cap)} A {_n(w / 2)} {_n(cap)} 0 0 0 {_n(x + w)} {_n(y + cap)}" />'
        )
    return f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="6" />'


def _place_nodes(nodes: dict[str, FlowNode], layers: list[list[str]], direction: str) -> None:
    layer_gap = 78.0 if direction == "LR" else 68.0
    node_gap = 30.0
    if direction == "LR":
        heights = [
            sum(nodes[name].height for name in layer) + node_gap * max(0, len(layer) - 1)
            for layer in layers
        ]
        axis = max(heights) / 2 if heights else 0.0
        cursor = 0.0
        for layer in layers:
            column_w = max(nodes[name].width for name in layer)
            total_h = sum(nodes[name].height for name in layer) + node_gap * max(0, len(layer) - 1)
            y = axis - total_h / 2
            for name in layer:
                node = nodes[name]
                node.cx = cursor + node.width / 2
                node.cy = y + node.height / 2
                y += node.height + node_gap
            cursor += column_w + layer_gap
        return

    widths = [
        sum(nodes[name].width for name in layer) + node_gap * max(0, len(layer) - 1)
        for layer in layers
    ]
    axis = max(widths) / 2 if widths else 0.0
    cursor = 0.0
    for layer in layers:
        depth = max(nodes[name].height for name in layer)
        total_w = sum(nodes[name].width for name in layer) + node_gap * max(0, len(layer) - 1)
        x = axis - total_w / 2
        for name in layer:
            node = nodes[name]
            node.cx = x + node.width / 2
            node.cy = cursor + depth / 2
            x += node.width + node_gap
        cursor += depth + layer_gap


def render_flow(text: str, args: list[str], line: int, title: str = "Flow") -> str:
    direction = "LR"
    for arg in args:
        if arg.upper() in ("LR", "TB"):
            direction = arg.upper()
        else:
            raise DraftError(
                f"unknown flow argument `{arg}`",
                line,
                "flow",
                "```flow LR\nGateway -> Service: rpc\n```",
            )
    nodes, edges, groups = parse_flow(text, line)
    for node in nodes.values():
        _measure_node(node, 190.0)
    _rank, layers = _layer_graph(nodes, edges)
    layers = _order_layers(layers, edges)
    _place_nodes(nodes, layers, direction)

    canvas = Canvas()
    for group_name, members in groups.items():
        member_nodes = [nodes[name] for name in members if name in nodes]
        if not member_nodes:
            continue
        min_x = min(node.cx - node.width / 2 for node in member_nodes) - 18
        max_x = max(node.cx + node.width / 2 for node in member_nodes) + 18
        min_y = min(node.cy - node.height / 2 for node in member_nodes) - 32
        max_y = max(node.cy + node.height / 2 for node in member_nodes) + 18
        canvas.add(
            f'<g class="flow-group"><rect x="{_n(min_x)}" y="{_n(min_y)}" '
            f'width="{_n(max_x - min_x)}" height="{_n(max_y - min_y)}" rx="10" />'
            f'<text class="group-label" x="{_n(min_x + 12)}" y="{_n(min_y + 16)}" font-size="11.5" '
            f'dominant-baseline="middle">{esc(group_name)}</text></g>'
        )
        canvas.extend(min_x, min_y, max_x, max_y)

    rank_of = {name: index for index, layer in enumerate(layers) for name in layer}
    lane_counter: dict[int, int] = {}
    return_lanes: dict[tuple[str, str], int] = {}
    horizontal = direction == "LR"
    pending: list[tuple[float, float, str, str]] = []
    # Node boxes are placed first so a label never lands on top of a node.
    placed: list[list[float]] = [
        [
            node.cx - node.width / 2 - 3,
            node.cy - node.height / 2 - 3,
            node.cx + node.width / 2 + 3,
            node.cy + node.height / 2 + 3,
        ]
        for node in nodes.values()
    ]

    def queue_label(x: float, y: float, label: str, anchor: str = "middle") -> None:
        lx, ly = place_label_box(x, y, label, anchor, placed)
        pending.append((lx, ly, label, anchor))
        span_x0 = lx if anchor == "start" else lx - text_px(label, LABEL_FONT) / 2
        canvas.extend(span_x0, ly - 12, span_x0 + text_px(label, LABEL_FONT), ly + 10)

    for edge in edges:
        src = nodes[edge.src]
        dst = nodes[edge.dst]

        if edge.src == edge.dst:
            start = (src.cx + src.width / 2, src.cy - 6)
            loop = start[0] + 34
            points = [
                start,
                (loop, start[1]),
                (loop, src.cy - src.height / 2 - 28),
                (src.cx, src.cy - src.height / 2 - 28),
                (src.cx, src.cy - src.height / 2),
            ]
            canvas.add(f'<path class="edge edge-{edge.style}" d="{rounded_path(points)}" />')
            canvas.add(arrow_head(points[-1], (0, 1)))
            for point in points:
                canvas.point(*point)
            if edge.label:
                queue_label(loop + 8, src.cy - src.height / 2 - 34, edge.label, anchor="start")
            continue

        if rank_of[edge.src] == rank_of[edge.dst]:
            layer_index = rank_of[edge.src]
            lane = lane_counter.get(layer_index, 0)
            lane_counter[layer_index] = lane + 1
            lane_x = max(src.cx + src.width / 2, dst.cx + dst.width / 2) + 26 + lane * 14
            points = [
                (src.cx + src.width / 2, src.cy),
                (lane_x, src.cy),
                (lane_x, dst.cy),
                (dst.cx + dst.width / 2, dst.cy),
            ]
            canvas.add(f'<path class="edge edge-{edge.style}" d="{rounded_path(points)}" />')
            canvas.add(arrow_head(points[-1], (-1, 0)))
            for point in points:
                canvas.point(*point)
            if edge.label:
                queue_label(lane_x + 8, (src.cy + dst.cy) / 2, edge.label, anchor="start")
            continue

        pair = (edge.src, edge.dst)
        mutual = any(other.dst == pair[0] and other.src == pair[1] for other in edges)
        if edge.backward and mutual:
            # Request and answer between the same two nodes: send the answer
            # back underneath the pair so the two arrows never overlap.
            slot = return_lanes.get(pair, 0)
            return_lanes[pair] = slot + 1
            if horizontal:
                lane_y = (
                    max(src.cy + src.height / 2, dst.cy + dst.height / 2)
                    + 26
                    + slot * 14
                )
                points = [
                    (src.cx, src.cy + src.height / 2),
                    (src.cx, lane_y),
                    (dst.cx, lane_y),
                    (dst.cx, dst.cy + dst.height / 2),
                ]
                mid = ((src.cx + dst.cx) / 2, lane_y + 12)
            else:
                lane_x = (
                    max(src.cx + src.width / 2, dst.cx + dst.width / 2)
                    + 26
                    + slot * 14
                )
                points = [
                    (src.cx + src.width / 2, src.cy),
                    (lane_x, src.cy),
                    (lane_x, dst.cy),
                    (dst.cx + dst.width / 2, dst.cy),
                ]
                mid = (lane_x + 12, (src.cy + dst.cy) / 2)
            canvas.add(f'<path class="edge edge-{edge.style}" d="{rounded_path(points)}" />')
            toward = (0, -1) if horizontal else (-1, 0)
            canvas.add(arrow_head(points[-1], toward))
            for point in points:
                canvas.point(*point)
            if edge.label:
                queue_label(mid[0], mid[1], edge.label, anchor="middle" if horizontal else "start")
            continue

        if horizontal:
            start = (src.cx + src.width / 2, src.cy)
            end = (dst.cx - dst.width / 2, dst.cy)
            if edge.backward:
                # Leave the source on the left, run in a lane beside both nodes
                # and enter the target from its left edge.
                lane_x = min(start[0], end[0]) - 28
                points = [start, (lane_x, start[1]), (lane_x, dst.cy), end]
                canvas.add(f'<path class="edge edge-{edge.style}" d="{rounded_path(points)}" />')
                canvas.add(arrow_head(end, (1, 0)))
                for point in points:
                    canvas.point(*point)
                # Label the run that leaves the source, where nothing else goes.
                mid = (lane_x + (start[0] - lane_x) * 0.5, src.cy - 13)
            else:
                span = max(26.0, abs(end[0] - start[0]) * 0.45)
                c1 = (start[0] + span, start[1])
                c2 = (end[0] - span, dst.cy)
                canvas.add(
                    f'<path class="edge edge-{edge.style}" d="M {_n(start[0])} {_n(start[1])} '
                    f'C {_n(c1[0])} {_n(c1[1])}, {_n(c2[0])} {_n(c2[1])}, {_n(end[0])} {_n(end[1])}" />'
                )
                canvas.add(arrow_head(end, (end[0] - c2[0], end[1] - c2[1])))
                for point in (start, end, c1, c2):
                    canvas.point(*point)
                mid = bezier_point(start, c1, c2, end, 0.5)
        elif edge.backward:
            # Loop above both nodes so the label clears the target box.
            start = (src.cx, src.cy - src.height / 2)
            end = (dst.cx, dst.cy + dst.height / 2)
            lane_y = min(start[1], end[1]) - 44
            points = [start, (start[0], lane_y), (end[0], lane_y), end]
            canvas.add(f'<path class="edge edge-{edge.style}" d="{rounded_path(points)}" />')
            canvas.add(arrow_head(end, (0, 1)))
            for point in points:
                canvas.point(*point)
            mid = ((start[0] + end[0]) / 2, lane_y - 11)
        else:
            start = (src.cx, src.cy + src.height / 2)
            end = (dst.cx, dst.cy - dst.height / 2)
            span = max(26.0, abs(end[1] - start[1]) * 0.45)
            c1 = (start[0], start[1] + span)
            c2 = (end[0], end[1] - span)
            canvas.add(
                f'<path class="edge edge-{edge.style}" d="M {_n(start[0])} {_n(start[1])} '
                f'C {_n(c1[0])} {_n(c1[1])}, {_n(c2[0])} {_n(c2[1])}, {_n(end[0])} {_n(end[1])}" />'
            )
            canvas.add(arrow_head(end, (end[0] - c2[0], end[1] - c2[1])))
            for point in (start, end, c1, c2):
                canvas.point(*point)
            mid = bezier_point(start, c1, c2, end, 0.5)

        if edge.label:
            anchor = "start" if not horizontal and edge.backward else "middle"
            lx = mid[0] + 8 if anchor == "start" else mid[0]
            ly = mid[1] if anchor == "start" else mid[1] - 12
            queue_label(lx, ly, edge.label, anchor)

    for lx, ly, label, anchor in pending:
        canvas.add(edge_label(lx, ly, label, anchor))

    for name in sorted(nodes, key=lambda key: nodes[key].order):
        node = nodes[name]
        canvas.add(_node_shape_svg(node))
        canvas.extend(
            node.cx - node.width / 2,
            node.cy - node.height / 2,
            node.cx + node.width / 2,
            node.cy + node.height / 2,
        )
        if len(node.lines) == 1:
            canvas.add(text_node(node.lines[0], node.cx, node.cy))
        else:
            start = node.cy - (len(node.lines) - 1) * LINE_H / 2
            for index, item in enumerate(node.lines):
                canvas.add(text_node(item, node.cx, start + index * LINE_H))

    return canvas.render(f"{title} flow diagram")


# --------------------------------------------------------------------------- #
# sequence
# --------------------------------------------------------------------------- #
@dataclass
class SeqEvent:
    index: int
    kind: str  # message | note | activate | deactivate
    src: str = ""
    dst: str = ""
    label: str = ""
    style: str = "solid"
    members: list[str] = field(default_factory=list)
    number: int = 0


@dataclass
class SeqFragment:
    branches: list[tuple[str, int, int]] = field(default_factory=list)
    depth: int = 0


def parse_sequence(
    text: str, line: int
) -> tuple[list[str], dict[str, str], list[SeqEvent], list[SeqFragment]]:
    example = (
        "```sequence\nClient -> Server: SYN\nServer -.-> Client: SYN-ACK\n"
        "note Client, Server: ESTABLISHED\nalt timeout {\n"
        "  Client -> Server: retry\n} else ok {\n  Client -> Done: close\n}\n```"
    )
    order: list[str] = []
    labels: dict[str, str] = {}
    events: list[SeqEvent] = []
    fragments: list[SeqFragment] = []
    stack: list[tuple[SeqFragment, int, str]] = []

    def remember(name: str) -> str:
        if name not in labels:
            order.append(name)
            labels[name] = name
        return name

    def record(event: SeqEvent) -> None:
        events.append(event)

    for offset, raw in enumerate(text.split("\n"), start=1):
        line_text = raw.strip()
        if not line_text or line_text.startswith("#"):
            continue
        participant = _PARTICIPANT_RE.match(line_text)
        if participant:
            key = participant.group("name").strip()
            if key not in labels:
                order.append(key)
            labels[key] = (participant.group("label") or key).strip()
            continue
        if _FRAGMENT_ELSE_RE.match(line_text):
            if not stack:
                raise DraftError("`else` without an open fragment", line + offset, "sequence", example)
            fragment, start, kind = stack[-1]
            fragment.branches.append((kind, start, len(events)))
            match = _FRAGMENT_ELSE_RE.match(line_text)
            stack[-1] = (fragment, len(events), (match.group("label") or "else").strip())
            continue
        if _GROUP_CLOSE_RE.match(line_text):
            if not stack:
                raise DraftError(
                    "`}` closes a fragment that was never opened", line + offset, "sequence", example
                )
            fragment, start, kind = stack.pop()
            fragment.branches.append((kind, start, len(events)))
            continue
        fragment_open = _FRAGMENT_OPEN_RE.match(line_text)
        if fragment_open:
            label = fragment_open.group("rest").strip() or fragment_open.group("kind")
            fragment = SeqFragment(depth=len(stack))
            fragments.append(fragment)
            stack.append((fragment, len(events), label))
            continue

        parts = _split_arrow(line_text)
        if parts:
            src_token, arrow, rest = parts
            dst_token, message_label = _split_label(rest)
            if not src_token.strip() or not dst_token.strip():
                raise DraftError(
                    "an arrow needs a participant on both sides", line + offset, "sequence", example
                )
            src = remember(src_token.strip())
            dst = remember(dst_token.strip())
            style = {"-.->": "dashed", "==>": "bold"}.get(arrow, "solid")
            record(
                SeqEvent(
                    index=len(events),
                    kind="message",
                    src=src,
                    dst=dst,
                    label=message_label.strip(),
                    style=style,
                    number=sum(1 for item in events if item.kind == "message") + 1,
                )
            )
            continue

        if line_text.lower().startswith("note "):
            members_text, _, note_text = line_text[5:].partition(":")
            members = [remember(item.strip()) for item in members_text.split(",") if item.strip()]
            if not members:
                raise DraftError(
                    "`note` needs at least one participant", line + offset, "sequence", example
                )
            record(
                SeqEvent(index=len(events), kind="note", label=note_text.strip(), members=members)
            )
            continue
        keyword, _, rest = line_text.partition(" ")
        if keyword.lower() in ("activate", "deactivate"):
            record(
                SeqEvent(index=len(events), kind=keyword.lower(), src=remember(rest.strip()))
            )
            continue
        raise DraftError(
            f"unrecognised sequence line `{line_text}`", line + offset, "sequence", example
        )

    while stack:
        fragment, start, kind = stack.pop()
        fragment.branches.append((kind, start, len(events)))
    if not order:
        raise DraftError("sequence diagram has no participants", line, "sequence", example)
    return order, labels, events, fragments


def render_sequence(text: str, args: list[str], line: int, title: str = "Sequence") -> str:
    for arg in args:
        if arg != "num":
            raise DraftError(
                f"unknown sequence argument `{arg}`",
                line,
                "sequence",
                "```sequence num\nA -> B: label\n```",
            )
    show_numbers = "num" in args
    order, labels, events, fragments = parse_sequence(text, line)

    head_font = 13.0
    label_font = 12.0
    margin = 28.0
    head_h = 34.0
    top = 76.0

    box_w = {name: max(80.0, text_px(labels[name], head_font) + 26) for name in order}
    needed = 150.0
    for event in events:
        if event.kind != "message" or event.src == event.dst:
            continue
        label = event.label or "→"
        needed = max(needed, min(text_px(label, label_font) + 58, 330))
    for fragment in fragments:
        for kind_label, _start, _end in fragment.branches:
            needed = max(needed, min(text_px(kind_label, label_font) + 76, 300))
    gap = needed

    lanes: dict[str, float] = {}
    cursor = margin + box_w[order[0]] / 2
    lanes[order[0]] = cursor
    for index, name in enumerate(order):
        if index:
            cursor += gap
        lanes[name] = cursor

    canvas = Canvas()
    open_spans: dict[str, list[float]] = {}
    spans: list[tuple[str, float, float]] = []
    notes: list[tuple[float, float, float, list[str]]] = []
    event_y: dict[int, float] = {}
    y = top

    for event in events:
        if event.kind == "message":
            y += 48
            event_y[event.index] = y
            continue
        if event.kind == "activate":
            open_spans.setdefault(event.src, []).append(y)
            continue
        if event.kind == "deactivate":
            starts = open_spans.get(event.src) or []
            if starts:
                spans.append((event.src, starts.pop(), max(6.0, y - starts[-1] if starts else y)))
            continue
        note_lines = wrap_text(event.label or "", label_font, max(210.0, gap * 1.5))
        height = len(note_lines) * 17 + 14
        xs = [lanes[member] for member in event.members]
        left = min(xs) - 48
        right = max(max(xs) + 48, left + max(text_px(item, label_font) for item in note_lines) + 26)
        box_y = y + 18
        notes.append((left, box_y, right, note_lines))
        y = box_y + height + 16
    bottom = y + 26

    for name, starts in open_spans.items():
        for start_y in starts:
            spans.append((name, start_y, bottom))

    for name, span_top, span_bottom in spans:
        canvas.add(
            f'<rect class="activation" x="{_n(lanes[name] - 5)}" y="{_n(span_top)}" '
            f'width="10" height="{_n(span_bottom - span_top)}" rx="3" />'
        )
        canvas.extend(lanes[name] - 5, span_top, lanes[name] + 5, span_bottom)

    for name in order:
        lane_x = lanes[name]
        canvas.add(
            f'<path class="lifeline" d="M {_n(lane_x)} {_n(head_h)} L {_n(lane_x)} {_n(bottom)}" />'
        )
        canvas.add(
            f'<rect class="participant" x="{_n(lane_x - box_w[name] / 2)}" y="0" '
            f'width="{_n(box_w[name])}" height="{_n(head_h)}" rx="6" />'
        )
        canvas.add(text_node(labels[name], lane_x, head_h / 2, size=head_font))
        canvas.extend(lane_x - box_w[name] / 2, 0, lane_x + box_w[name] / 2, head_h)

    for left, box_y, right, note_lines in notes:
        height = len(note_lines) * 17 + 14
        canvas.add(
            f'<rect class="note-box" x="{_n(left)}" y="{_n(box_y)}" width="{_n(right - left)}" '
            f'height="{_n(height)}" rx="6" />'
        )
        for index, item in enumerate(note_lines):
            canvas.add(
                text_node(item, left + 12, box_y + 13 + index * 17, size=label_font, anchor="start")
            )
        canvas.extend(left, box_y, right, box_y + height)

    for event in events:
        if event.kind != "message":
            continue
        y_line = event_y[event.index]
        x1 = lanes[event.src]
        x2 = lanes[event.dst]
        if event.src == event.dst:
            loop = x1 + 36
            points = [(x1 + 5, y_line - 24), (loop, y_line - 24), (loop, y_line + 8), (x1 + 5, y_line + 8)]
            canvas.add(f'<path class="edge edge-{event.style}" d="{rounded_path(points)}" />')
            canvas.add(arrow_head(points[-1], (-1, 0)))
            for point in points:
                canvas.point(*point)
            if event.label:
                text = f"{event.number}. {event.label}" if show_numbers and event.number else event.label
                canvas.add(edge_label(loop + 8, y_line + 18, text, anchor="start"))
                canvas.extend(loop + 8, y_line + 8, loop + 8 + text_px(text, LABEL_FONT), y_line + 28)
            continue
        direction = 1 if x2 > x1 else -1
        start = (x1 + direction * 5, y_line)
        end = (x2 - direction * 8, y_line)
        canvas.add(
            f'<path class="edge edge-{event.style}" d="M {_n(start[0])} {_n(start[1])} '
            f'L {_n(end[0])} {_n(end[1])}" />'
        )
        canvas.add(arrow_head(end, (direction, 0)))
        canvas.point(x1, y_line)
        canvas.point(x2, y_line)
        if event.label:
            text = f"{event.number}. {event.label}" if show_numbers and event.number else event.label
            mid = (x1 + x2) / 2
            label_y = y_line - 12
            width = text_px(text, label_font)
            canvas.add(
                f'<rect class="edge-label-bg" x="{_n(mid - width / 2 - 4)}" y="{_n(label_y - 9)}" '
                f'width="{_n(width + 8)}" height="14" rx="4" />'
            )
            canvas.add(
                text_node(text, mid, label_y - 1, size=label_font, cls="edge-label", fill=MUTED)
            )
            canvas.extend(mid - width / 2, label_y - 12, mid + width / 2, label_y + 10)

    used_tabs: list[list[float]] = []
    for fragment in sorted(fragments, key=lambda item: item.depth):
        if not fragment.branches:
            continue
        spans: list[tuple[str, float, float]] = []
        for kind_label, start_index, end_index in fragment.branches:
            if start_index < len(events) and events[start_index].kind == "message":
                top_y = event_y[events[start_index].index] - 26
            else:
                top_y = top - 8
            if end_index < len(events) and events[end_index].kind == "message":
                bottom_y = event_y[events[end_index].index] - 26
            else:
                bottom_y = bottom
            spans.append((kind_label, top_y, max(bottom_y, top_y + 40)))
        # A nested fragment steps inwards so its tab clears the one it sits in.
        indent = fragment.depth * 18
        left = min(lanes[name] for name in order) - 74 + indent
        right = max(lanes[name] for name in order) + 74 - indent
        tab_y = spans[0][1] - 22
        frame_top = tab_y
        for index, (kind_label, top_y, bottom_y) in enumerate(spans):
            tab_y = max(tab_y, top_y - 22)
            tab_w = text_px(kind_label, LABEL_FONT) + 18
            while any(
                box[0] < left + tab_w and left < box[2] and box[1] < tab_y + 17 and tab_y < box[3]
                for box in used_tabs
            ):
                tab_y += 18
            canvas.add(
                f'<rect class="frag-tab" x="{_n(left)}" y="{_n(tab_y)}" width="{_n(tab_w)}" '
                f'height="17" rx="4" />'
            )
            canvas.add(
                text_node(kind_label, left + 9, tab_y + 8.5, size=LABEL_FONT, anchor="start", cls="frag-label")
            )
            used_tabs.append([left, tab_y, left + tab_w, tab_y + 17])
            canvas.extend(left, tab_y, left + tab_w, tab_y + 17)
            canvas.add(
                f'<path class="frag-divider" d="M {_n(left)} {_n(bottom_y)} L {_n(right)} {_n(bottom_y)}" />'
            )
            tab_y += 18
        frame_bottom = max(item[2] for item in spans)
        canvas.add(
            f'<rect class="frag" x="{_n(left)}" y="{_n(frame_top)}" width="{_n(right - left)}" '
            f'height="{_n(frame_bottom - frame_top)}" rx="8" />'
        )
        canvas.extend(left, frame_top, right, frame_bottom)

    if math.isfinite(canvas.max_x):
        canvas.max_x = max(canvas.max_x, lanes[order[-1]] + box_w[order[-1]] / 2 + margin)
    return canvas.render(f"{title} sequence diagram")


# --------------------------------------------------------------------------- #
# tree
# --------------------------------------------------------------------------- #
def render_tree(text: str, args: list[str], line: int, title: str = "Tree") -> str:
    if args:
        raise DraftError(
            f"unknown tree argument `{args[0]}`",
            line,
            "tree",
            "```tree\nrepo\n  module\n    file.py\n```",
        )
    example = "```tree\nrepo\n  skills\n    html-brief\n      SKILL.md\n```"
    rows: list[tuple[int, str]] = []
    for offset, raw in enumerate(text.split("\n"), start=1):
        if not raw.strip():
            continue
        label = raw.strip().replace("│", "").strip()
        if not label:
            raise DraftError("a tree line needs a label", line + offset, "tree", example)
        depth = len(raw) - len(raw.expandtabs(2).lstrip(" "))
        rows.append((depth, label))
    if not rows:
        raise DraftError("tree diagram is empty", line, "tree", example)

    indent = 22.0
    row_h = 30.0
    box_h = 24.0
    canvas = Canvas()
    positions: list[tuple[float, float, float]] = []
    y = box_h / 2 + 6
    for level, label in rows:
        lines = wrap_text(label, FONT, 320.0)
        width = max(text_px(item, FONT) for item in lines) + 26
        positions.append((6.0 + level * indent, y, width))
        y += row_h
    bottom = y

    children: dict[int, list[int]] = {}
    for index in range(1, len(rows)):
        depth = rows[index][0]
        parent = None
        for back in range(index - 1, -1, -1):
            if rows[back][0] < depth:
                parent = back
                break
            if rows[back][0] == depth:
                break
        if parent is None:
            continue
        children.setdefault(parent, []).append(index)

    for parent, indexes in children.items():
        parent_x, parent_y, _width = positions[parent]
        spine_x = parent_x + 14
        last_cy = positions[indexes[-1]][1]
        canvas.add(
            f'<path class="edge edge-solid" d="M {_n(spine_x)} {_n(parent_y + box_h / 2)} '
            f'L {_n(spine_x)} {_n(last_cy)}" />'
        )
        canvas.point(spine_x, parent_y + box_h / 2)
        canvas.point(spine_x, last_cy)
        for child in indexes:
            child_x, child_y, _child_w = positions[child]
            canvas.add(
                f'<path class="edge edge-solid" d="M {_n(spine_x)} {_n(child_y)} L {_n(child_x)} {_n(child_y)}" />'
            )
            canvas.point(spine_x, child_y)
            canvas.point(child_x, child_y)

    for index, (x, cy, width) in enumerate(positions):
        cls = "node node-tree-root" if index == 0 else "node"
        canvas.add(
            f'<rect class="{cls}" x="{_n(x)}" y="{_n(cy - box_h / 2)}" width="{_n(width)}" '
            f'height="{_n(box_h)}" rx="5" />'
        )
        lines = wrap_text(rows[index][1], FONT, 320.0)
        start = cy - (len(lines) - 1) * LINE_H / 2
        for line_index, item in enumerate(lines):
            canvas.add(text_node(item, x + 13, start + line_index * LINE_H, anchor="start"))
        canvas.extend(x, cy - box_h / 2, x + width, cy + box_h / 2)

    canvas.max_y = max(canvas.max_y, bottom)
    return canvas.render(f"{title} tree")


# --------------------------------------------------------------------------- #
# timeline
# --------------------------------------------------------------------------- #
def render_timeline(text: str, args: list[str], line: int, title: str = "Timeline") -> str:
    if args:
        raise DraftError(
            f"unknown timeline argument `{args[0]}`",
            line,
            "timeline",
            "```timeline\n2024-01 | First release | solo\n```",
        )
    example = "```timeline\n2024-01 | First release | solo project\n*2025-06 | GA | 10k installs\n```"
    entries: list[tuple[str, str, str, bool]] = []
    for offset, raw in enumerate(text.split("\n"), start=1):
        if not raw.strip():
            continue
        line_text = raw.strip()
        highlight = line_text.startswith("*")
        if highlight:
            line_text = line_text[1:].strip()
        parts = [item.strip() for item in line_text.split("|")]
        if len(parts) == 1:
            parts = ["", parts[0], ""]
        if len(parts) != 3:
            raise DraftError(
                "a timeline line is `date | title | description`",
                line + offset,
                "timeline",
                example,
            )
        entries.append((parts[0], parts[1], parts[2], highlight))
    if not entries:
        raise DraftError("timeline is empty", line, "timeline", example)

    canvas = Canvas()
    date_w = max([text_px(item[0], LABEL_FONT) for item in entries] + [40.0])
    spine_x = date_w + 34
    card_x = spine_x + 26
    widest = max([text_px(item[1], FONT) for item in entries] + [0.0])
    widest = max(widest, max([text_px(item[2], FONT) for item in entries] + [0.0]))
    card_w = max(240.0, min(460.0, widest + 34))
    card_gap = 18.0
    y = 16.0
    for date, heading, description, highlight in entries:
        cls = "tl-card tl-card-hl" if highlight else "tl-card"
        dot = "tl-dot tl-dot-hl" if highlight else "tl-dot"
        lines = wrap_text(description, LABEL_FONT, card_w - 26) if description else []
        card_h = 30.0 + (len(lines) * 16 if lines else 0)
        canvas.add(
            f'<rect class="{cls}" x="{_n(card_x)}" y="{_n(y)}" width="{_n(card_w)}" '
            f'height="{_n(card_h)}" rx="7" />'
        )
        canvas.add(text_node(heading, card_x + 13, y + 16, anchor="start"))
        for index, item in enumerate(lines):
            canvas.add(
                text_node(item, card_x + 13, y + 30 + index * 16, size=LABEL_FONT, anchor="start", cls="tl-desc")
            )
        if date:
            canvas.add(
                text_node(date, spine_x - 22, y + card_h / 2, size=LABEL_FONT, anchor="end", cls="tl-date")
            )
            canvas.extend(spine_x - 22 - text_px(date, LABEL_FONT), y, spine_x - 22, y + card_h)
        canvas.add(f'<circle class="{dot}" cx="{_n(spine_x)}" cy="{_n(y + card_h / 2)}" r="5" />')
        canvas.extend(card_x, y, card_x + card_w, y + card_h)
        canvas.extend(spine_x - 22, y, spine_x, y + card_h)
        y += card_h + card_gap
    spine_bottom = y - card_gap + 16

    canvas.add(
        f'<path class="tl-spine" d="M {_n(spine_x)} 16 L {_n(spine_x)} {_n(spine_bottom)}" />'
    )
    canvas.point(spine_x, 16)
    canvas.point(spine_x, spine_bottom)
    return canvas.render(f"{title} timeline")