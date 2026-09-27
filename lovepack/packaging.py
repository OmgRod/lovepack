import fnmatch
import shutil
import subprocess
import tempfile
from pathlib import Path
import zipfile

from .conf import ensure_conf_lua


def load_ignore_patterns(root_dir: Path, config: dict) -> list[str]:
    ignore_path = root_dir / ".loveignore"
    patterns = [".git*", "build/*", ".loveignore", "external/*"]
    external_directory = config.get("external", {}).get("directory", "external")
    patterns.append(f"{external_directory.rstrip('/\\')}/*")
    if ignore_path.exists():
        for line in ignore_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_ignored(rel_path: Path, patterns: list[str]) -> bool:
    path_str = rel_path.as_posix()
    return any(
        fnmatch.fnmatch(path_str, pattern)
        or fnmatch.fnmatch(rel_path.name, pattern)
        or (pattern.endswith("/") and fnmatch.fnmatch(path_str + "/", pattern))
        for pattern in patterns
    )


def find_luajit(configured_compiler: str) -> str:
    configured_path = shutil.which(configured_compiler)
    candidates = [configured_path] if configured_path else []
    candidates.append(shutil.which("luajit"))
    for candidate in candidates:
        if not candidate or "luajit" not in Path(candidate).stem.lower():
            continue
        result = subprocess.run([candidate, "-v"], capture_output=True, text=True)
        version = f"{result.stdout}\n{result.stderr}"
        if result.returncode == 0 and "luajit" in version.lower():
            return candidate
    raise RuntimeError(
        "Lua bytecode requires LuaJIT for Love2D compatibility, but no local "
        "LuaJIT executable was found. Install LuaJIT on PATH and retry."
    )


def compile_lua_file(source: Path, target: Path, compiler: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [compiler, "-b", str(source), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            f"LuaJIT bytecode compiler '{compiler}' was not found. "
            "Install LuaJIT on PATH or set build.lua_compiler to its executable."
        ) from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or "unknown compiler error"
        raise RuntimeError(f"Lua bytecode compilation failed for {source}: {detail}") from error


def build_love_package(root_dir: Path, config: dict) -> Path:
    build_config = config.get("build", {})
    build_dir = root_dir / build_config.get("output_dir", "build")
    build_dir.mkdir(parents=True, exist_ok=True)

    game_name = config.get("game", {}).get("name", root_dir.name)
    love_filename = build_config.get("love_filename", f"{game_name}.love")
    out_love_path = build_dir / love_filename
    ensure_conf_lua(root_dir, config)

    patterns = load_ignore_patterns(root_dir, config)
    compile_bytecode = bool(build_config.get("compile_bytecode", False))
    lua_compiler = find_luajit(build_config.get("lua_compiler", "luajit")) if compile_bytecode else None
    if lua_compiler:
        print(f"            Compiler: {lua_compiler} (LuaJIT)")
    print(f"\n[PACKAGING] Project: '{game_name}'")
    print(f"            Target:  {out_love_path.relative_to(root_dir)}")

    packed_count = 0
    with tempfile.TemporaryDirectory(prefix="lovepack-") as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(out_love_path, "w", zipfile.ZIP_DEFLATED) as love_zip:
            for file_path in root_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                rel_path = file_path.relative_to(root_dir)
                if build_dir in file_path.parents or file_path == out_love_path:
                    continue
                if is_ignored(rel_path, patterns):
                    continue

                package_path = file_path
                if compile_bytecode and file_path.suffix == ".lua":
                    package_path = temp_root / rel_path
                    compile_lua_file(file_path, package_path, lua_compiler)
                love_zip.write(package_path, rel_path)
                packed_count += 1

    print(f"[SUCCESS] Packed {packed_count} files into '{out_love_path.name}'.")
    return out_love_path
