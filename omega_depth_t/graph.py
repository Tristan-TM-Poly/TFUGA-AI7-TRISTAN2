from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping
from xml.sax.saxutils import escape

from .model import NodeContract


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    node_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "node_id": self.node_id, "message": self.message}


class DepthGraph:
    """Validated parent-child graph for recursive Tristan creations."""

    def __init__(self, nodes: Iterable[NodeContract] = ()) -> None:
        self._nodes: dict[str, NodeContract] = {}
        self._children: dict[str, list[str]] = defaultdict(list)
        for node in nodes:
            self.add(node)

    def add(self, node: NodeContract) -> None:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        if node.parent_id is not None and node.parent_id not in self._nodes:
            raise ValueError(f"parent must be added first: {node.parent_id}")
        if node.parent_id is not None:
            parent = self._nodes[node.parent_id]
            if node.depth != parent.depth + 1:
                raise ValueError(
                    f"depth mismatch for {node.id}: expected {parent.depth + 1}, got {node.depth}"
                )
            if not node.path.startswith(parent.path.rstrip("/") + "/"):
                raise ValueError(f"path of {node.id} must descend from parent path")
            self._children[node.parent_id].append(node.id)
        self._nodes[node.id] = node
        self._children.setdefault(node.id, [])

    @property
    def nodes(self) -> Mapping[str, NodeContract]:
        return self._nodes

    @property
    def roots(self) -> tuple[NodeContract, ...]:
        return tuple(node for node in self._nodes.values() if node.parent_id is None)

    @property
    def maximum_observed_depth(self) -> int:
        return max((node.depth for node in self._nodes.values()), default=0)

    def __len__(self) -> int:
        return len(self._nodes)

    def get(self, node_id: str) -> NodeContract:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"unknown node: {node_id}") from exc

    def children(self, node_id: str) -> tuple[NodeContract, ...]:
        self.get(node_id)
        return tuple(self._nodes[item] for item in self._children[node_id])

    def ancestors(self, node_id: str) -> tuple[NodeContract, ...]:
        current = self.get(node_id)
        result: list[NodeContract] = []
        while current.parent_id is not None:
            current = self.get(current.parent_id)
            result.append(current)
        result.reverse()
        return tuple(result)

    def descendants(self, node_id: str) -> tuple[NodeContract, ...]:
        self.get(node_id)
        result: list[NodeContract] = []
        queue: deque[str] = deque(self._children[node_id])
        while queue:
            current_id = queue.popleft()
            result.append(self._nodes[current_id])
            queue.extend(self._children[current_id])
        return tuple(result)

    def leaves(self) -> tuple[NodeContract, ...]:
        return tuple(node for node in self._nodes.values() if not self._children[node.id])

    def nodes_at_depth(self, depth: int) -> tuple[NodeContract, ...]:
        if depth < 0:
            raise ValueError("depth cannot be negative")
        return tuple(node for node in self._nodes.values() if node.depth == depth)

    def iter_depth_first(self, root_id: str | None = None) -> Iterator[NodeContract]:
        roots = [self.get(root_id)] if root_id else list(self.roots)
        stack = list(reversed(roots))
        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed(self.children(node.id)))

    def validate(self) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        if not self._nodes:
            issues.append(ValidationIssue("empty_graph", "", "graph has no nodes"))
            return tuple(issues)

        root_ids = {node.id for node in self.roots}
        if not root_ids:
            issues.append(ValidationIssue("missing_root", "", "graph has no root"))
        for node in self._nodes.values():
            if node.depth == 0 and node.parent_id is not None:
                issues.append(
                    ValidationIssue("root_has_parent", node.id, "depth-zero node has a parent")
                )
            if node.depth > 0 and node.parent_id not in self._nodes:
                issues.append(
                    ValidationIssue("missing_parent", node.id, f"missing parent {node.parent_id}")
                )
            if node.parent_id is not None:
                parent = self._nodes.get(node.parent_id)
                if parent and node.depth != parent.depth + 1:
                    issues.append(
                        ValidationIssue(
                            "invalid_depth",
                            node.id,
                            f"expected depth {parent.depth + 1}, got {node.depth}",
                        )
                    )
                if parent and node.root_creation != parent.root_creation:
                    issues.append(
                        ValidationIssue(
                            "root_mismatch",
                            node.id,
                            "child and parent have different root_creation",
                        )
                    )

        for node in self._nodes.values():
            seen: set[str] = set()
            current = node
            while current.parent_id is not None:
                if current.id in seen:
                    issues.append(
                        ValidationIssue("cycle", node.id, "cycle detected in parent chain")
                    )
                    break
                seen.add(current.id)
                parent = self._nodes.get(current.parent_id)
                if parent is None:
                    break
                current = parent

        reached = {node.id for node in self.iter_depth_first()}
        for orphan in sorted(set(self._nodes) - reached):
            issues.append(
                ValidationIssue("unreachable", orphan, "node is not reachable from any root")
            )
        return tuple(issues)

    def summary(self) -> dict[str, Any]:
        by_depth = {
            str(depth): len(self.nodes_at_depth(depth))
            for depth in range(self.maximum_observed_depth + 1)
        }
        status_counts: dict[str, int] = defaultdict(int)
        for node in self._nodes.values():
            status_counts[node.oak_status.value] += 1
        return {
            "node_count": len(self),
            "root_count": len(self.roots),
            "leaf_count": len(self.leaves()),
            "maximum_observed_depth": self.maximum_observed_depth,
            "nodes_by_depth": by_depth,
            "oak_status_counts": dict(sorted(status_counts.items())),
            "validation_issue_count": len(self.validate()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega-depth-t-r0.1",
            "summary": self.summary(),
            "nodes": [node.to_dict() for node in self.iter_depth_first()],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DepthGraph":
        return cls(NodeContract.from_dict(item) for item in payload.get("nodes", []))

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination

    @classmethod
    def read_json(cls, path: str | Path) -> "DepthGraph":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(payload)

    def write_jsonl(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for node in self.iter_depth_first():
                handle.write(json.dumps(node.to_dict(), ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return destination

    def markdown_tree(self, root_id: str | None = None) -> str:
        lines: list[str] = []
        for node in self.iter_depth_first(root_id):
            indent = "  " * node.depth
            lines.append(
                f"{indent}- `{node.id}` — **{node.name}** "
                f"(n={node.depth}, OAK={node.oak_status.value})"
            )
        return "\n".join(lines) + "\n"

    def write_markdown_tree(self, path: str | Path, root_id: str | None = None) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.markdown_tree(root_id), encoding="utf-8")
        return destination

    def write_graphml(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="name" for="node" attr.name="name" attr.type="string"/>',
            '  <key id="depth" for="node" attr.name="depth" attr.type="int"/>',
            '  <key id="oak_status" for="node" attr.name="oak_status" attr.type="string"/>',
            '  <graph id="omega-depth" edgedefault="directed">',
        ]
        for node in self.iter_depth_first():
            lines.extend(
                [
                    f'    <node id="{escape(node.id)}">',
                    f'      <data key="name">{escape(node.name)}</data>',
                    f'      <data key="depth">{node.depth}</data>',
                    f'      <data key="oak_status">{escape(node.oak_status.value)}</data>',
                    "    </node>",
                ]
            )
        for node in self._nodes.values():
            if node.parent_id is not None:
                edge_id = f"{node.parent_id}__{node.id}"
                lines.append(
                    f'    <edge id="{escape(edge_id)}" '
                    f'source="{escape(node.parent_id)}" target="{escape(node.id)}"/>'
                )
        lines.extend(["  </graph>", "</graphml>"])
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return destination

    def write_bundle(self, output_dir: str | Path) -> dict[str, str]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        artifacts = {
            "json": str(self.write_json(output / "depth-graph.json")),
            "jsonl": str(self.write_jsonl(output / "nodes.jsonl")),
            "markdown": str(self.write_markdown_tree(output / "tree.md")),
            "graphml": str(self.write_graphml(output / "depth-graph.graphml")),
        }
        report = {
            **self.summary(),
            "validation_issues": [issue.to_dict() for issue in self.validate()],
            "artifacts": artifacts,
            "boundary": (
                "maximum_observed_depth describes this finite artifact; "
                "it is not a permanent architecture ceiling."
            ),
        }
        report_path = output / "oak-report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifacts["report"] = str(report_path)
        return artifacts
