import shutil
from pathlib import Path

from .config import load_config


def _remove_directory(path: Path, root_dir: Path, label: str):
    resolved = path.resolve()
    root_resolved = root_dir.resolve()
    if resolved == root_resolved or root_resolved not in resolved.parents:
        raise RuntimeError(f"Refusing to clean unsafe path: {path}")
    if path.exists():
        shutil.rmtree(path)
        print(f"[REMOVED] {label}: {path.relative_to(root_dir)}")


def clean_project(root_dir: Path):
    config = load_config(root_dir)
    output_dir = config.get("build", {}).get("output_dir", "build")
    _remove_directory(root_dir / output_dir, root_dir, "Love2D build output")
    _remove_directory(root_dir / "dist", root_dir, "Python distributions")

    for cache_dir in root_dir.rglob("__pycache__"):
        if cache_dir.is_dir():
            _remove_directory(cache_dir, root_dir, "Python cache")

    print("[SUCCESS] Clean complete.")
