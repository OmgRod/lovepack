import json
from copy import deepcopy
from pathlib import Path


LOVE_CONF_DEFAULTS = {
    "identity": None,
    "appendidentity": False,
    "version": "11.5",
    "console": False,
    "accelerometerjoystick": True,
    "externalstorage": False,
    "gammacorrect": False,
    "audio": {
        "mic": False,
        "mixwithsystem": True,
    },
    "window": {
        "title": "Untitled",
        "icon": None,
        "width": 800,
        "height": 600,
        "borderless": False,
        "resizable": False,
        "minwidth": 1,
        "minheight": 1,
        "fullscreen": False,
        "fullscreentype": "desktop",
        "vsync": 1,
        "msaa": 0,
        "depth": None,
        "stencil": None,
        "display": 1,
        "highdpi": False,
        "usedpiscale": True,
        "x": None,
        "y": None,
    },
    "modules": {
        "audio": True,
        "data": True,
        "event": True,
        "font": True,
        "graphics": True,
        "image": True,
        "joystick": True,
        "keyboard": True,
        "math": True,
        "mouse": True,
        "physics": True,
        "sound": True,
        "system": True,
        "thread": True,
        "timer": True,
        "touch": True,
        "video": True,
        "window": True,
    },
}


def _lua_value(value):
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Unsupported conf.lua value type: {type(value).__name__}")


def conf_values(config: dict) -> dict:
    values = deepcopy(LOVE_CONF_DEFAULTS)
    values["identity"] = config.get("game", {}).get("name", values["identity"])
    values["version"] = config.get("love", {}).get("version", values["version"])
    return values


def render_conf_lua(config: dict) -> str:
    lines = ["function love.conf(t)"]
    for key, value in conf_values(config).items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                lines.append(f"    t.{key}.{nested_key} = {_lua_value(nested_value)}")
        else:
            lines.append(f"    t.{key} = {_lua_value(value)}")
    lines.append("end")
    return "\n".join(lines) + "\n"


def ensure_conf_lua(root_dir: Path, config: dict):
    conf_path = root_dir / "conf.lua"
    build_config = config.get("build", {})
    generate_conf = bool(build_config.get("generate_conf_lua", True))
    overwrite_conf = bool(build_config.get("overwrite_conf_lua", False))
    existed = conf_path.exists()

    if existed and not overwrite_conf:
        print("            conf.lua: existing file preserved")
        return
    if not generate_conf and not existed:
        print("            conf.lua: generation disabled; no file included")
        return

    conf_path.write_text(render_conf_lua(config), encoding="utf-8")
    action = "overwritten" if existed else "generated"
    print(f"            conf.lua: {action}")
