import os
import platform
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from .constants import CACHE_DIR


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


def download_love_binary(version: str) -> Path:
    os_name, arch = get_platform_info()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if os_name == "win":
        asset_name = f"love-{version}-win{64 if arch == 'x64' else 32}.zip"
    elif os_name == "macos":
        asset_name = f"love-{version}-macos.zip"
    else:
        asset_name = f"love-{version}-x86_64.tar.gz"

    url = f"https://github.com/love2d/love/releases/download/{version}/{asset_name}"
    target_extract = CACHE_DIR / f"love-{version}-{os_name}-{arch}"
    if target_extract.exists():
        print(f"[CACHE] Using existing LÖVE {version} runtime binary.")
        return target_extract

    print(f"\n[FETCH] Downloading LÖVE {version} ({os_name}-{arch})...")
    print(f"        Source: {url}")
    archive_path = CACHE_DIR / asset_name
    try:
        urllib.request.urlretrieve(url, archive_path)
    except Exception as error:
        print(f"[ERROR] Failed to download binaries: {error}")
        sys.exit(1)

    print("[EXTRACT] Unpacking runtime environment...")
    target_extract.mkdir(parents=True, exist_ok=True)
    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(target_extract)
    else:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(target_extract)
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
    print(f"\n[FUSING] Building standalone executable ({os_name.upper()})...")

    if os_name == "win":
        love_exe = next(binary_dir.rglob("love.exe"), None)
        if not love_exe:
            raise FileNotFoundError("Could not locate love.exe in binary cache.")
        exe_out_dir = dist_dir / f"{game_name}-win"
        if exe_out_dir.exists():
            shutil.rmtree(exe_out_dir)
        shutil.copytree(love_exe.parent, exe_out_dir)
        target_exe = exe_out_dir / f"{game_name}.exe"
        with target_exe.open("wb") as output:
            output.write(love_exe.read_bytes())
            output.write(love_file.read_bytes())
        (exe_out_dir / "love.exe").unlink(missing_ok=True)
        print(f"[SUCCESS] Windows build output: {exe_out_dir.relative_to(root_dir)}")
    elif os_name == "linux":
        love_bin = next(binary_dir.rglob("love"), None)
        if not love_bin:
            raise FileNotFoundError("Could not locate love binary in binary cache.")
        target_bin = dist_dir / game_name
        target_bin.write_bytes(love_bin.read_bytes() + love_file.read_bytes())
        target_bin.chmod(0o755)
        print(f"[SUCCESS] Linux build output: {target_bin.relative_to(root_dir)}")
    else:
        love_app = next(binary_dir.rglob("love.app"), None)
        if not love_app:
            raise FileNotFoundError("Could not locate love.app in binary cache.")
        target_app = dist_dir / f"{game_name}.app"
        if target_app.exists():
            shutil.rmtree(target_app)
        shutil.copytree(love_app, target_app)
        shutil.copy(love_file, target_app / "Contents" / "Resources" / "game.love")
        print(f"[SUCCESS] macOS App Bundle created: {target_app.relative_to(root_dir)}")
