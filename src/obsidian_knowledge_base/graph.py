from __future__ import annotations

from collections import Counter
from pathlib import Path

from obsidian_knowledge_base.models import Edge, KnowledgeGraph, Node, Note
from obsidian_knowledge_base.parser import parse_note, slugify


def build_graph(vault_path: str | Path) -> KnowledgeGraph:
    root = Path(vault_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Vault path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {root}")

    notes = [parse_note(root, path) for path in _markdown_files(root)]
    aliases = _aliases_for(notes)
    nodes: dict[str, Node] = {
        note.id: Node(
            id=note.id,
            title=note.title,
            short_label=_short_label(note.title),
            kind="note",
            path=note.path,
            summary=note.summary,
            markdown=note.body,
            markdown_length=len(note.body),
            tags=sorted(note.tags),
            word_count=note.word_count,
        )
        for note in notes
    }
    edges: set[Edge] = set()

    for note in notes:
        for tag in sorted(note.tags):
            tag_id = f"tag:{tag}"
            nodes.setdefault(
                tag_id,
                Node(id=tag_id, title=f"#{tag}", short_label=f"#{tag}", kind="tag"),
            )
            edges.add(Edge(source=note.id, target=tag_id, kind="tag", label=tag))

        for target in note.wiki_links:
            target_id = _resolve_target(target, aliases)
            if target_id:
                edges.add(Edge(source=note.id, target=target_id, kind="wiki", label=target))
            else:
                missing_id = f"missing:{slugify(target)}"
                nodes.setdefault(
                    missing_id,
                    Node(
                        id=missing_id,
                        title=target,
                        short_label=_short_label(target),
                        kind="missing",
                    ),
                )
                edges.add(Edge(source=note.id, target=missing_id, kind="wiki", label=target))

        for target in filter(None, note.markdown_links):
            target_id = _resolve_target(target, aliases)
            if target_id:
                edges.add(Edge(source=note.id, target=target_id, kind="markdown", label=target))

    _apply_degrees(nodes, edges)
    sorted_nodes = sorted(
        nodes.values(),
        key=lambda node: (node.kind != "note", node.title.lower()),
    )
    sorted_edges = sorted(edges, key=lambda edge: (edge.source, edge.target, edge.kind))
    return KnowledgeGraph(
        nodes=sorted_nodes,
        edges=sorted_edges,
        stats=_stats(sorted_nodes, sorted_edges, root),
    )


def _markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if ".obsidian" not in path.parts
        and not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def _aliases_for(notes: list[Note]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for note in notes:
        aliases[note.id] = note.id
        aliases[slugify(Path(note.path).stem)] = note.id
        aliases[slugify(Path(note.path).with_suffix("").as_posix())] = note.id
        aliases[slugify(note.title)] = note.id
    return aliases


def _resolve_target(target: str, aliases: dict[str, str]) -> str | None:
    clean = target.strip().removeprefix("./").removesuffix(".md")
    return aliases.get(slugify(clean))


def _apply_degrees(nodes: dict[str, Node], edges: set[Edge]) -> None:
    incoming = Counter(edge.target for edge in edges)
    outgoing = Counter(edge.source for edge in edges)
    for node_id, node in nodes.items():
        node.backlinks = incoming[node_id]
        node.outlinks = outgoing[node_id]


def _stats(nodes: list[Node], edges: list[Edge], root: Path) -> dict[str, int | float | str]:
    note_count = sum(node.kind == "note" for node in nodes)
    tag_count = sum(node.kind == "tag" for node in nodes)
    missing_count = sum(node.kind == "missing" for node in nodes)
    total_words = sum(node.word_count for node in nodes)
    return {
        "vault": root.name,
        "notes": note_count,
        "tags": tag_count,
        "missing": missing_count,
        "edges": len(edges),
        "words": total_words,
        "average_words": round(total_words / note_count, 1) if note_count else 0,
    }


def _short_label(title: str) -> str:
    words = [word for word in title.replace("#", " #").split() if word]
    return " ".join(words[:3]) if words else "Untitled"


def graph_to_jsonable(vault_path: str | Path) -> dict[str, object]:
    return build_graph(vault_path).to_dict()
