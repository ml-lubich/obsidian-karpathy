from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt

from obsidian_karpathy.models import Note

FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<meta>.*?)\n---\s*\n?", re.DOTALL)
WIKI_LINK_RE = re.compile(r"\[\[(?P<target>[^\]#|]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((?P<target>[^)#?]+(?:\.md)?)[^)]*\)")
TAG_RE = re.compile(r"(?<![\w/])#(?P<tag>[A-Za-z0-9][A-Za-z0-9_/-]*)")
WORD_RE = re.compile(r"\b[\w'-]+\b")

_markdown = MarkdownIt("commonmark")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def note_id_for(root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(root).with_suffix("").as_posix()
    return slugify(relative)


def parse_note(root: Path, file_path: Path) -> Note:
    text = file_path.read_text(encoding="utf-8")
    metadata, body = _split_frontmatter(text)
    relative = file_path.relative_to(root).as_posix()

    title = (
        metadata.get("title")
        or _first_heading(body)
        or file_path.stem.replace("-", " ").title()
    )
    tags = set(_metadata_tags(metadata)) | set(_body_tags(body))
    wiki_links = [match.strip() for match in WIKI_LINK_RE.findall(body)]
    markdown_links = [_clean_markdown_target(match) for match in MARKDOWN_LINK_RE.findall(body)]

    return Note(
        id=note_id_for(root, file_path),
        title=title,
        path=relative,
        body=body,
        summary=_summary(body),
        tags={slugify(tag) for tag in tags},
        wiki_links=wiki_links,
        markdown_links=markdown_links,
        word_count=len(WORD_RE.findall(_plain_text(body))),
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group("meta").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")
    return metadata, text[match.end() :]


def _metadata_tags(metadata: dict[str, str]) -> list[str]:
    raw = metadata.get("tags") or metadata.get("tag") or ""
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [
        item.strip().strip('"').strip("'").lstrip("#")
        for item in re.split(r"[, ]+", raw)
        if item
    ]


def _body_tags(body: str) -> list[str]:
    stripped = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("# "))
    return [match.group("tag") for match in TAG_RE.finditer(stripped)]


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line.lstrip("#").strip()
    return None


def _summary(body: str, limit: int = 180) -> str:
    for line in _plain_text(body).splitlines():
        sentence = line.strip()
        if sentence and not sentence.startswith("#"):
            return sentence[:limit].rstrip()
    return ""


def _plain_text(body: str) -> str:
    tokens = _markdown.parse(body)
    parts: list[str] = []
    for token in tokens:
        if token.type in {"inline", "text"} and token.content:
            parts.append(token.content)
    return "\n".join(parts) or body


def _clean_markdown_target(target: str) -> str:
    path = target.strip()
    if path.startswith(("http://", "https://", "mailto:")):
        return ""
    return path.removeprefix("./").removesuffix(".md")
