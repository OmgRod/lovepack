import argparse
import fnmatch
import os
import platform
import shutil
import sys
import tarfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_PROJECT_TOML = """[game]
name = "MyLoveGame"
version = "0.1.0"
author = "Developer"

[love]
version = "11.5"

[build]
output_dir = "build"
love_filename = "game.love"
"""

DEFAULT_LOVEIGNORE = """# Git & Dev Files
.git*
.vscode/
.idea/
*.md
project.toml
.loveignore

# Build Artifacts
build/
dist/
*.love
*.exe
"""

CACHE_DIR = Path.home() / ".cache" / "lovepack"


def get_platform_info():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        os_name = "win"
        arch = "x64" if machine in ["amd64", "x86_64"] else "x86"
    elif system == "darwin":
        os_name = "macos"
        arch = "universal"
    elif system == "linux":
        os_name = "linux"
        arch = "x86_64" if machine in ["amd64", "x86_64"] else "i686"
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")
        
    return os_name, arch


def load_config(root_dir: Path) -> dict:
    config_path = root_dir / "project.toml"
    if not config_path.exists():
        print("No project.toml found. Initializing defaults...")
        return {
            "game": {"name": root_dir.name, "version": "0.1.0"},
            "love": {"version": "11.5"},
            "build": {"output_dir": "build", "love_filename": f"{root_dir.name}.love"}
        }
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_ignore_patterns(root_dir: Path) -> list[str]:
    ignore_path = root_dir / ".loveignore"
    patterns = [".git*", "build/*", ".loveignore"]
    if ignore_path.exists():
        with open(ignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(rel_path: Path, patterns: list[str]) -> bool:
    path_str = str(rel_path).replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(rel_path.name, pattern):
            return True
        if pattern.endswith("/") and fnmatch.fnmatch(path_str + "/", pattern):
            return True
    return False


def build_love_package(root_dir: Path, config: dict) -> Path:
    build_dir = root_dir / config.get("build", {}).get("output_dir", "build")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    game_name = config.get("game", {}).get("name", root_dir.name)
    love_filename = config.get("build", {}).get("love_filename", f"{game_name}.love")
    out_love_path = build_dir / love_filename
    
    patterns = load_ignore_patterns(root_dir)
    print(f"Packaging '{game_name}' into {out_love_path.relative_to(root_dir)}...")

    packed_count = 0
    with zipfile.ZipFile(out_love_path, "w", zipfile.ZIP_DEFLATED) as love_zip:
        for file_path in root_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(root_dir)
                if build_dir in file_path.parents or file_path == out_love_path:
                    continue
                if not is_ignored(rel_path, patterns):
                    love_zip.write(file_path, rel_path)
                    packed_count += 1

    print(f"Success! Packed {packed_count} files.")
    return out_love_path


def download_love_binary(version: str) -> Path:
    os_name, arch = get_platform_info()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if os_name == "win":
        asset_name = f"love-{version}-win{64 if arch == 'x64' else 32}.zip"
    elif os_name == "macos":
        asset_name = f"love-{version}-macos.zip"
    elif os_name == "linux":
        asset_name = f"love-{version}-x86_64.tar.gz"

    url = f"https://github.com/love2d/love/releases/download/{version}/{asset_name}"
    target_extract = CACHE_DIR / f"love-{version}-{os_name}-{arch}"
    
    if target_extract.exists():
        return target_extract

    print(f"Downloading LÖVE binaries ({version}) from GitHub Releases...")
    print(f"URL: {url}")
    
    archive_path = CACHE_DIR / asset_name
    try:
        urllib.request.urlretrieve(url, archive_path)
    except Exception as e:
        print(f"Failed to download LÖVE binaries: {e}")
        sys.exit(1)

    print("Extracting binary runtime...")
    target_extract.mkdir(parents=True, exist_ok=True)
    
    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(target_extract)
    elif asset_name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(target_extract)

    archive_path.unlink()
    return target_extract


def build_executable(root_dir: Path, config: dict, love_file: Path):
    version = config.get("love", {}).get("version", "11.5")
    binary_dir = download_love_binary(version)
    os_name, _ = get_platform_info()
    
    build_dir = root_dir / config.get("build", {}).get("output_dir", "build")
    game_name = config.get("game", {}).get("name", "Game")
    dist_dir = build_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fusing standalone executable for {os_name.upper()}...")

    if os_name == "win":
        love_exe = next(binary_dir.rglob("love.exe"), None)
        if not love_exe:
            raise FileNotFoundError("Could not locate love.exe in downloaded binary cache.")
        
        exe_out_dir = dist_dir / f"{game_name}-win"
        if exe_out_dir.exists():
            shutil.rmtree(exe_out_dir)
        
        shutil.copytree(love_exe.parent, exe_out_dir)
        target_exe = exe_out_dir / f"{game_name}.exe"
        
        with open(target_exe, "wb") as out_f:
            with open(love_exe, "rb") as in_exe:
                out_f.write(in_exe.read())
            with open(love_file, "rb") as in_love:
                out_f.write(in_love.read())
                
        (exe_out_dir / "love.exe").unlink(missing_ok=True)
        print(f"Standalone Windows distribution created: {exe_out_dir}")

    elif os_name == "linux":
        love_bin = next(binary_dir.rglob("love"), None)
        if not love_bin:
            raise FileNotFoundError("Could not locate love binary in downloaded cache.")

        target_bin = dist_dir / game_name
        with open(target_bin, "wb") as out_f:
            with open(love_bin, "rb") as in_bin:
                out_f.write(in_bin.read())
            with open(love_file, "rb") as in_love:
                out_f.write(in_love.read())

        target_bin.chmod(0o755)
        print(f"Standalone Linux executable created: {target_bin}")

    elif os_name == "macos":
        love_app = next(binary_dir.rglob("love.app"), None)
        if not love_app:
            raise FileNotFoundError("Could not locate love.app in downloaded cache.")

        target_app = dist_dir / f"{game_name}.app"
        if target_app.exists():
            shutil.rmtree(target_app)
            
        shutil.copytree(love_app, target_app)
        resources_dir = target_app / "Contents" / "Resources"
        shutil.copy(love_file, resources_dir / "game.love")
        print(f"Standalone macOS Application Bundle created: {target_app}")


def init_project(root_dir: Path):
    toml_path = root_dir / "project.toml"
    ignore_path = root_dir / ".loveignore"

    if not toml_path.exists():
        toml_path.write_text(DEFAULT_PROJECT_TOML, encoding="utf-8")
        print("Created project.toml")

    if not ignore_path.exists():
        ignore_path.write_text(DEFAULT_LOVEIGNORE, encoding="utf-8")
        print("Created .loveignore")

    print("Initialized lovepack environment!")


def main():
    parser = argparse.ArgumentParser(description="lovepack: LÖVE engine packager & binary fusion utility")
    parser.add_argument("command", choices=["init", "pack", "build"], help="Command to run")
    args = parser.parse_args()

    root_dir = Path.cwd()

    if args.command == "init":
        init_project(root_dir)
    elif args.command == "pack":
        config = load_config(root_dir)
        build_love_package(root_dir, config)
    elif args.command == "build":
        config = load_config(root_dir)
        love_file = build_love_package(root_dir, config)
        build_executable(root_dir, config, love_file)


if __name__ == "__main__":
    main()