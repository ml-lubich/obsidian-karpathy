from pathlib import Path

import pytest

from obsidian_karpathy.graph import build_graph, graph_to_jsonable


def write_note(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_build_graph_resolves_links_tags_missing_and_degrees(tmp_path: Path) -> None:
    write_note(
        tmp_path,
        "Home.md",
        "# Home\n\nLinks to [[Projects/Graph Explorer]], [[Writing]], and [[Missing Note]]. #home",
    )
    write_note(
        tmp_path,
        "Projects/Graph Explorer.md",
        "# Graph Explorer\n\nBack to [[Home]] and [Writing](../Writing.md). #project",
    )
    write_note(tmp_path, "Writing.md", "# Writing\n\nBacklinks are useful. #output")
    write_note(tmp_path, ".obsidian/ignored.md", "# Ignored")
    write_note(tmp_path, ".hidden.md", "# Hidden")

    graph = build_graph(tmp_path)
    data = graph.to_dict()
    node_ids = {node["id"] for node in data["nodes"]}
    edge_tuples = {(edge["source"], edge["target"], edge["kind"]) for edge in data["edges"]}

    assert node_ids >= {
        "home",
        "projects-graph-explorer",
        "writing",
        "tag:home",
        "tag:project",
        "tag:output",
        "missing:missing-note",
    }
    assert ("home", "projects-graph-explorer", "wiki") in edge_tuples
    assert ("home", "writing", "wiki") in edge_tuples
    assert ("projects-graph-explorer", "writing", "markdown") in edge_tuples
    assert ("home", "missing:missing-note", "wiki") in edge_tuples
    assert graph.stats["notes"] == 3
    assert graph.stats["tags"] == 3
    assert graph.stats["missing"] == 1

    writing = next(node for node in graph.nodes if node.id == "writing")
    assert writing.backlinks == 2
    assert writing.outlinks == 1


def test_graph_to_jsonable_returns_plain_dict(tmp_path: Path) -> None:
    write_note(tmp_path, "Home.md", "# Home\n\n#tag")

    data = graph_to_jsonable(tmp_path)

    assert sorted(data) == ["edges", "nodes", "stats"]
    assert data["stats"]["notes"] == 1


def test_build_graph_validates_vault_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_graph(tmp_path / "missing")

    file_path = tmp_path / "file.md"
    file_path.write_text("# File", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        build_graph(file_path)
