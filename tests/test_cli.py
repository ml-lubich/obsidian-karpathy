from pathlib import Path

from typer.testing import CliRunner

from obsidian_karpathy.cli import app


def test_build_and_stats_commands(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Home.md").write_text("# Home\n\nLinks to [[Second]]. #tag", encoding="utf-8")
    (vault / "Second.md").write_text("# Second\n\nBack to [[Home]].", encoding="utf-8")
    output = tmp_path / "graph.json"

    runner = CliRunner()
    build_result = runner.invoke(app, ["build", str(vault), "--output", str(output)])
    stats_result = runner.invoke(app, ["stats", str(vault)])

    assert build_result.exit_code == 0
    assert output.exists()
    assert "nodes" in output.read_text(encoding="utf-8")
    assert stats_result.exit_code == 0
    assert "Notes" in stats_result.output


def test_version_command() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "obsidian-karpathy" in result.output
