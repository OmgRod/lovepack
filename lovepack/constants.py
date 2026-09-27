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
compile_bytecode = false
lua_compiler = "luajit"
generate_conf_lua = true
overwrite_conf_lua = false

[external]
enabled = false
directory = "external"
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
external/
"""

CACHE_DIR = Path.home() / ".cache" / "lovepack"
