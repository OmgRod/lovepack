from pathlib import Path

import pytest
from PIL import Image

from lovepack import external, icons, runtime


def test_external_files_copy_by_platform(tmp_path):
    source = tmp_path / "external" / "windows" / "data" / "license.txt"
    source.parent.mkdir(parents=True)
    source.write_text("license", encoding="utf-8")
    output = tmp_path / "output"
    config = {"external": {"enabled": True}}

    external.copy_external_files(tmp_path, "win", output, config)
    assert (output / "data" / "license.txt").read_text(encoding="utf-8") == "license"
    assert external.PLATFORM_EXTERNAL_DIRS["macos"] == ("mac", "macos")


def test_icons_are_generated_and_invalid_paths_fail(tmp_path):
    image_path = tmp_path / "icon.png"
    Image.new("RGBA", (32, 16), (255, 0, 0, 255)).save(image_path)
    output = tmp_path / "dist"
    output.mkdir()
    config = {"game": {"icon": "icon.png"}}

    icons.generate_windows_icons(tmp_path, config, output)
    assert (output / "game.ico").exists()
    assert (output / "love.ico").exists()
    assert icons._icon_canvas(Image.new("RGB", (2, 4))).size == (128, 256)

    with pytest.raises(RuntimeError, match="does not exist"):
        icons.generate_windows_icons(tmp_path, {"game": {"icon": "missing.png"}}, output)


def test_runtime_platform_and_love_discovery(monkeypatch):
    monkeypatch.setattr(runtime.platform, "system", lambda: "Windows")
    monkeypatch.setattr(runtime.platform, "machine", lambda: "AMD64")
    assert runtime.get_platform_info() == ("win", "x64")
    monkeypatch.setattr(runtime.platform, "system", lambda: "Plan9")
    with pytest.raises(RuntimeError, match="Unsupported"):
        runtime.get_platform_info()

    monkeypatch.setattr(runtime.shutil, "which", lambda name: "/usr/bin/love" if name == "love" else None)
    assert runtime.find_love_executable() == "/usr/bin/love"
    monkeypatch.setattr(runtime.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="Love2D executable"):
        runtime.find_love_executable()


def test_run_love_game_passes_archive_to_love2d(monkeypatch, tmp_path):
    commands = []
    game = tmp_path / "build" / "game.love"
    game.parent.mkdir()
    game.write_bytes(b"archive")
    monkeypatch.setattr(runtime, "find_love_executable", lambda: "love")
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: commands.append((args, kwargs)))

    runtime.run_love_game(tmp_path, game)
    assert commands == [(( ["love", str(game)] ,), {"cwd": tmp_path, "check": True})]


def test_build_executable_linux_copies_love_file(tmp_path, monkeypatch):
    game = tmp_path / "game.love"
    game.write_bytes(b"archive")
    monkeypatch.setattr(runtime, "get_platform_info", lambda: ("linux", "x86_64"))
    runtime.build_executable(tmp_path, {"game": {"name": "Demo"}}, game)
    assert (tmp_path / "build" / "dist" / "Demo.love").read_bytes() == b"archive"
