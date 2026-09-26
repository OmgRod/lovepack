import re
from pathlib import Path

from PIL import Image, ImageOps

ICON_NAMES = ("game.ico", "love.ico")
ICON_CONFIG_PATTERN = re.compile(
    r"t\.window\.icon\s*=\s*([\"'])(?P<path>.+?)\1"
)


def _configured_icon_path(root_dir: Path, config: dict) -> Path | None:
    game_config = config.get("game", {})
    build_config = config.get("build", {})
    configured = game_config.get("icon") or build_config.get("icon")
    if configured:
        return root_dir / configured

    conf_path = root_dir / "conf.lua"
    if conf_path.exists():
        match = ICON_CONFIG_PATTERN.search(conf_path.read_text(encoding="utf-8"))
        if match:
            return root_dir / match.group("path")
    return None


def _icon_canvas(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    return ImageOps.contain(image, (256, 256), Image.Resampling.LANCZOS)


def generate_windows_icons(root_dir: Path, config: dict, output_dir: Path):
    source_path = _configured_icon_path(root_dir, config)
    if source_path is None:
        return
    if not source_path.exists():
        raise RuntimeError(f"Configured game icon does not exist: {source_path}")

    try:
        with Image.open(source_path) as source:
            icon = _icon_canvas(source)
            for name in ICON_NAMES:
                icon.save(
                    output_dir / name,
                    format="ICO",
                    sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
                )
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Could not convert game icon '{source_path}': {error}") from error

    print(f"            Icons: updated {output_dir.name}/game.ico and love.ico from {source_path.name}")
