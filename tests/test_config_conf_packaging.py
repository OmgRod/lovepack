import zipfile
from pathlib import Path

import pytest

from lovepack import conf, config, packaging


def test_config_defaults_round_trip_and_typed_values(tmp_path):
    defaults = config.default_config(tmp_path)
    assert defaults["game"]["name"] == tmp_path.name

    config.write_config(tmp_path, defaults)
    loaded = config.load_config(tmp_path)
    assert loaded == defaults
    assert config.parse_config_value("true") is True
    assert config.parse_config_value("[1, 2]") == [1, 2]
    assert config.parse_config_value("raw", force_string=True) == "raw"
    with pytest.raises(ValueError):
        config.parse_config_value("not valid =")


def test_configure_project_set_get_unset_and_initialize(tmp_path, capsys):
    config.initialize_project_files(tmp_path)
    assert (tmp_path / "project.toml").exists()
    assert (tmp_path / ".loveignore").exists()

    config.configure_project(tmp_path, "set", "build.width", "1280")
    assert config.load_config(tmp_path)["build"]["width"] == 1280
    config.configure_project(tmp_path, "get", "build.width")
    assert "1280" in capsys.readouterr().out
    config.configure_project(tmp_path, "unset", "build.width")
    assert "width" not in config.load_config(tmp_path)["build"]
    with pytest.raises(KeyError):
        config.configure_project(tmp_path, "get", "missing.value")
    with pytest.raises(ValueError):
        config.configure_project(tmp_path, "set", "build..bad", "1")


def test_conf_render_and_preservation(tmp_path):
    settings = config.default_config(tmp_path)
    rendered = conf.render_conf_lua(settings)
    assert "function love.conf(t)" in rendered
    assert 't.window.width = 800' in rendered
    assert f't.identity = "{tmp_path.name}"' in rendered

    conf.ensure_conf_lua(tmp_path, settings)
    original = (tmp_path / "conf.lua").read_text(encoding="utf-8")
    conf.ensure_conf_lua(tmp_path, settings)
    assert (tmp_path / "conf.lua").read_text(encoding="utf-8") == original
    settings["build"]["overwrite_conf_lua"] = True
    conf.ensure_conf_lua(tmp_path, settings)
    assert (tmp_path / "conf.lua").read_text(encoding="utf-8") == rendered


def test_packaging_filters_and_builds_archive(tmp_path):
    (tmp_path / "main.lua").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "notes.md").write_text("ignore me", encoding="utf-8")
    (tmp_path / ".loveignore").write_text("*.md\n", encoding="utf-8")
    settings = config.default_config(tmp_path)
    settings["game"]["name"] = "Demo"
    settings["build"]["love_filename"] = "Demo.love"
    output = packaging.build_love_package(tmp_path, settings)

    assert output == tmp_path / "build" / "Demo.love"
    with zipfile.ZipFile(output) as archive:
        assert "main.lua" in archive.namelist()
        assert "conf.lua" in archive.namelist()
        assert "notes.md" not in archive.namelist()

    patterns = packaging.load_ignore_patterns(tmp_path, settings)
    assert packaging.is_ignored(Path("notes.md"), patterns)
    assert packaging.is_ignored(Path("build/Demo.love"), patterns)
    assert not packaging.is_ignored(Path("main.lua"), patterns)


def test_packaging_luajit_helpers(monkeypatch, tmp_path):
    calls = []

    class Result:
        returncode = 0
        stdout = "LuaJIT 2.1"
        stderr = ""

    monkeypatch.setattr(packaging.shutil, "which", lambda name: "C:/bin/luajit.exe")
    monkeypatch.setattr(packaging.subprocess, "run", lambda *args, **kwargs: Result())
    assert packaging.find_luajit("custom") == "C:/bin/luajit.exe"

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr(packaging.subprocess, "run", fake_run)
    source = tmp_path / "main.lua"
    target = tmp_path / "compiled" / "main.lua"
    source.write_text("return 1", encoding="utf-8")
    packaging.compile_lua_file(source, target, "luajit")
    assert calls[0][0] == ["luajit", "-b", str(source), str(target)]
    assert target.parent.exists()

    monkeypatch.setattr(packaging.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="no local LuaJIT"):
        packaging.find_luajit("missing")
