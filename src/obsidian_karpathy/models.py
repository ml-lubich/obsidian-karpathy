from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

NodeKind = Literal["note", "tag", "missing"]
EdgeKind = Literal["wiki", "markdown", "tag"]


@dataclass(slots=True)
class Note:
    id: str
    title: str
    path: str
    body: str
    summary: str
    tags: set[str] = field(default_factory=set)
    wiki_links: list[str] = field(default_factory=list)
    markdown_links: list[str] = field(default_factory=list)
    word_count: int = 0


@dataclass(slots=True)
class Node:
    id: str
    title: str
    short_label: str
    kind: NodeKind
    path: str | None = None
    summary: str = ""
    markdown: str = ""
    markdown_length: int = 0
    tags: list[str] = field(default_factory=list)
    word_count: int = 0
    backlinks: int = 0
    outlinks: int = 0


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    kind: EdgeKind
    label: str = ""


@dataclass(slots=True)
class KnowledgeGraph:
    nodes: list[Node]
    edges: list[Edge]
    stats: dict[str, int | float | str]

    def to_dict(self) -> dict[str, object]:
        return {
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
            "stats": self.stats,
        }
