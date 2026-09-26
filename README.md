# lovepack

`lovepack` packages LÖVE projects into `.love` archives and standalone builds.

## Configuration

Initialize a project with a lovepack `project.toml`, `.loveignore`, and a
complete generated `conf.lua`:

```text
lovepack init
```

Inspect or update lovepack settings using dotted keys. Values are parsed as
TOML, so booleans, numbers, arrays, and quoted strings are supported:

```text
lovepack config show
lovepack config set build.compile_bytecode true
lovepack config set build.lua_compiler luajit --string
lovepack config get build.compile_bytecode
lovepack config unset build.lua_compiler
```

Build-only settings belong under `[build]`. Lua bytecode compilation is
disabled by default. When enabled, lovepack uses a local LuaJIT executable and
its `-b` mode, which produces bytecode compatible with Love2D:

```toml
[build]
compile_bytecode = true
lua_compiler = "luajit"
generate_conf_lua = true
overwrite_conf_lua = false
```

Love2D runtime settings belong in your own `conf.lua`. `lovepack init` creates
a complete file containing every documented LÖVE 11.5 root, audio, window, and
module option if it is missing. Packaging preserves an existing `conf.lua` by
default; set `build.overwrite_conf_lua = true` to replace it with the generated
complete file. Set `build.generate_conf_lua = false` to disable generation when
no `conf.lua` exists.

`project.toml` is a lovepack build manifest, not a Love2D runtime configuration
file. Bytecode is written into the archive under the same `.lua` paths, which
keeps `require` and `main.lua` resolution compatible.

## Build Commands

Remove generated Love2D builds, wheel distributions, and Python cache folders:

```powershell
poetry run lovepack clean
```

On Windows, `release.bat` runs clean, builds the current wheel, and
force-reinstalls it into the active pip environment:

```powershell
.\release.bat
```

For a globally available command without publishing a package, install this
checkout in editable mode:

```powershell
py -m pip install --user --editable C:\path\to\lovepack
lovepack build
```