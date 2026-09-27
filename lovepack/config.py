import json
import tomllib
from pathlib import Path

from .constants import DEFAULT_LOVEIGNORE, DEFAULT_PROJECT_TOML


def default_config(root_dir: Path) -> dict:
    return {
        "game": {"name": root_dir.name, "version": "0.1.0"},
        "love": {"version": "11.5"},
        "build": {
            "output_dir": "build",
            "love_filename": f"{root_dir.name}.love",
            "compile_bytecode": False,
            "lua_compiler": "luajit",
            "generate_conf_lua": True,
            "overwrite_conf_lua": False,
        },
        "external": {
            "enabled": False,
            "directory": "external",
        },
    }


def load_config(root_dir: Path) -> dict:
    config_path = root_dir / "project.toml"
    if not config_path.exists():
        print("[NOTICE] No project.toml found. Initializing defaults...")
        return default_config(root_dir)
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def _toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Unsupported TOML value type: {type(value).__name__}")


def write_config(root_dir: Path, config: dict):
    lines = []

    def write_table(table, prefix=()):
        scalar_items = [(key, value) for key, value in table.items() if not isinstance(value, dict)]
        child_items = [(key, value) for key, value in table.items() if isinstance(value, dict)]
        if prefix:
            lines.append(f"[{'.'.join(prefix)}]")
        for key, value in scalar_items:
            lines.append(f"{key} = {_toml_value(value)}")
        if scalar_items and child_items:
            lines.append("")
        for index, (key, value) in enumerate(child_items):
            write_table(value, prefix + (key,))
            if index != len(child_items) - 1:
                lines.append("")

    write_table(config)
    (root_dir / "project.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _config_parent(config: dict, key: str, create=False):
    parts = key.split(".")
    if any(not part for part in parts):
        raise ValueError("Config keys must use non-empty dotted names")
    current = config
    for part in parts[:-1]:
        if part not in current:
            if not create:
                raise KeyError(key)
            current[part] = {}
        if not isinstance(current[part], dict):
            raise ValueError(f"Config path '{part}' is not a table")
        current = current[part]
    return current, parts[-1]


def parse_config_value(raw_value: str, force_string=False):
    if force_string:
        return raw_value
    try:
        return tomllib.loads(f"value = {raw_value}")["value"]
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Invalid TOML value: {error}") from error


def configure_project(root_dir: Path, action: str, key=None, raw_value=None, force_string=False):
    config = load_config(root_dir)
    if action == "show":
        print(json.dumps(config, indent=2, sort_keys=True))
        return
    if action == "get":
        parent, leaf = _config_parent(config, key)
        if leaf not in parent:
            raise KeyError(key)
        print(json.dumps(parent[leaf], indent=2))
        return
    if action == "set":
        parent, leaf = _config_parent(config, key, create=True)
        parent[leaf] = parse_config_value(raw_value, force_string)
    elif action == "unset":
        parent, leaf = _config_parent(config, key)
        if leaf not in parent:
            raise KeyError(key)
        del parent[leaf]
    else:
        raise ValueError(f"Unknown config action: {action}")
    write_config(root_dir, config)
    print(f"[SUCCESS] Updated project.toml: {key}")


def initialize_project_files(root_dir: Path):
    toml_path = root_dir / "project.toml"
    ignore_path = root_dir / ".loveignore"
    if not toml_path.exists():
        toml_path.write_text(DEFAULT_PROJECT_TOML, encoding="utf-8")
        print("[CREATED] project.toml")
    if not ignore_path.exists():
        ignore_path.write_text(DEFAULT_LOVEIGNORE, encoding="utf-8")
        print("[CREATED] .loveignore")
