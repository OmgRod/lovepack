import sys

import pytest

from lovepack import clean, cli, github


def test_cli_parser_has_test_command():
    args = cli.create_parser().parse_args(["test"])
    assert args.command == "test"


def test_cli_test_builds_then_runs(monkeypatch, tmp_path):
    calls = []
    archive = tmp_path / "build" / "game.love"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["lovepack", "test"])
    monkeypatch.setattr(cli, "load_config", lambda root: {"game": {"name": "Demo"}})
    monkeypatch.setattr(cli, "build_love_package", lambda root, settings: calls.append(("build", root, settings)) or archive)
    monkeypatch.setattr(cli, "run_love_game", lambda root, love: calls.append(("run", root, love)))

    cli.main()
    assert [call[0] for call in calls] == ["build", "run"]
    assert calls[1][2] == archive


def test_clean_project_removes_generated_directories(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "dist").mkdir()
    cache = tmp_path / "source" / "__pycache__"
    cache.mkdir(parents=True)
    clean.clean_project(tmp_path)
    assert not (tmp_path / "build").exists()
    assert not (tmp_path / "dist").exists()
    assert not cache.exists()


def test_clean_refuses_root(tmp_path):
    with pytest.raises(RuntimeError, match="unsafe"):
        clean._remove_directory(tmp_path, tmp_path, "root")


def test_github_workflow_creation_and_collision(tmp_path):
    github.setup_github_action(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "lovepack-build.yml"
    assert workflow.exists()
    assert "actions/checkout@v4" in workflow.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="already exists"):
        github.setup_github_action(tmp_path)
    github.setup_github_action(tmp_path, force=True)


def test_cli_reports_runtime_errors(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["lovepack", "test"])
    monkeypatch.setattr(cli, "load_config", lambda root: {})
    monkeypatch.setattr(cli, "build_love_package", lambda root, settings: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert "boom" in capsys.readouterr().out
