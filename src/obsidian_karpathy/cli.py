from __future__ import annotations

import json
import shutil
import webbrowser
from importlib.resources import as_file, files
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from obsidian_karpathy import __version__
from obsidian_karpathy.graph import build_graph
from obsidian_karpathy.web import create_app

app = typer.Typer(
    name="okg",
    help="Build and explore a Karpathy-inspired graph from any Obsidian Markdown vault.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"obsidian-karpathy {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, help="Show the installed version."),
    ] = False,
) -> None:
    return None


@app.command()
def build(
    vault: Annotated[Path, typer.Argument(help="Path to an Obsidian vault or Markdown folder.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Where to write graph JSON."),
    ] = Path("graph.json"),
) -> None:
    """Write a graph JSON file."""
    graph = build_graph(vault)
    output.write_text(json.dumps(graph.to_dict(), indent=2), encoding="utf-8")
    console.print(
        f"[green]Wrote[/green] {output} with "
        f"{len(graph.nodes)} nodes and {len(graph.edges)} edges."
    )


@app.command()
def stats(
    vault: Annotated[Path, typer.Argument(help="Path to an Obsidian vault or Markdown folder.")],
) -> None:
    """Print a compact vault summary."""
    graph = build_graph(vault)
    table = Table(title=f"{graph.stats['vault']} graph")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in graph.stats.items():
        table.add_row(str(key).replace("_", " ").title(), str(value))
    console.print(table)


@app.command()
def serve(
    vault: Annotated[Path, typer.Argument(help="Path to an Obsidian vault or Markdown folder.")],
    host: Annotated[str, typer.Option("--host", help="Host for the web UI.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port for the web UI.")] = 8765,
    open_browser: Annotated[
        bool,
        typer.Option("--open/--no-open", help="Open the UI in a browser."),
    ] = True,
) -> None:
    """Serve the interactive graph UI."""
    url = f"http://{host}:{port}"
    if open_browser:
        webbrowser.open(url)
    console.print(f"[bold]Serving[/bold] {vault} at [cyan]{url}[/cyan]")
    uvicorn.run(create_app(vault), host=host, port=port)


@app.command("init-demo")
def init_demo(
    destination: Annotated[
        Path,
        typer.Argument(help="Directory where the sample vault should be copied."),
    ] = Path("demo-vault"),
) -> None:
    """Copy a small sample vault for instant exploration."""
    if destination.exists():
        raise typer.BadParameter(f"Destination already exists: {destination}")
    with as_file(files("obsidian_karpathy").joinpath("demo_vault")) as source:
        shutil.copytree(source, destination)
    console.print(f"[green]Created[/green] {destination}. Try: okg serve {destination}")
