from pathlib import Path

from obsidian_knowledge_base.parser import note_id_for, parse_note, slugify


def test_parse_note_extracts_metadata_links_tags_and_summary(tmp_path: Path) -> None:
    note_path = tmp_path / "Projects" / "Graph Explorer.md"
    note_path.parent.mkdir()
    note_path.write_text(
        """---
title: Graph Explorer
tags: [project, ui]
---

# Graph Explorer

This is the first durable sentence with [[Home]] and [[Areas/Writing|Writing]].

See [Embeddings](../Resources/Embeddings.md) and #systems.
""",
        encoding="utf-8",
    )

    note = parse_note(tmp_path, note_path)

    assert note.id == "projects-graph-explorer"
    assert note.title == "Graph Explorer"
    assert note.path == "Projects/Graph Explorer.md"
    assert note.summary.startswith("Graph Explorer")
    assert note.tags == {"project", "ui", "systems"}
    assert note.wiki_links == ["Home", "Areas/Writing"]
    assert note.markdown_links == ["../Resources/Embeddings"]
    assert note.word_count > 10


def test_slugify_and_note_id_have_stable_fallbacks(tmp_path: Path) -> None:
    note_path = tmp_path / "A Strange Note!.md"
    note_path.write_text("Plain body", encoding="utf-8")

    assert slugify("A Strange Note!") == "a-strange-note"
    assert slugify("!!!") == "untitled"
    assert note_id_for(tmp_path, note_path) == "a-strange-note"


def test_parse_note_uses_heading_then_stem_for_title(tmp_path: Path) -> None:
    with_heading = tmp_path / "with-heading.md"
    with_heading.write_text("# Real Title\n\nBody", encoding="utf-8")
    without_heading = tmp_path / "daily-note.md"
    without_heading.write_text("Just body", encoding="utf-8")

    assert parse_note(tmp_path, with_heading).title == "Real Title"
    assert parse_note(tmp_path, without_heading).title == "Daily Note"
