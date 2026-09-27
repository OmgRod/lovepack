import shutil
from pathlib import Path


PLATFORM_EXTERNAL_DIRS = {
    "win": ("win", "windows"),
    "macos": ("mac", "macos"),
    "linux": ("linux",),
}


def copy_external_files(root_dir: Path, platform_name: str, output_dir: Path, config: dict):
    external_config = config.get("external", {})
    if not external_config.get("enabled", False):
        return

    external_root = root_dir / external_config.get("directory", "external")
    platform_dirs = PLATFORM_EXTERNAL_DIRS.get(platform_name, (platform_name,))
    source_dir = next(
        (external_root / name for name in platform_dirs if (external_root / name).is_dir()),
        None,
    )
    if source_dir is None:
        return

    copied_count = 0
    for source_path in source_dir.rglob("*"):
        if not source_path.is_file():
            continue
        relative_path = source_path.relative_to(source_dir)
        destination = output_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        copied_count += 1

    print(
        f"            External files: copied {copied_count} file(s) from "
        f"{source_dir.relative_to(root_dir)}"
    )