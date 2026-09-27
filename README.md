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

## External Platform Files

Put release-only files under platform folders in `external/`:

```text
external/
	win/
		README.txt
	mac/
		Contents/Resources/license.txt
	linux/
		launch.sh
```

Enable the feature in `project.toml`:

```toml
[external]
enabled = true
directory = "external"
```

When enabled during `build`, each folder is copied into the root of that platform's output
using its relative paths. `external/win` overlays the Windows runtime folder,
`external/mac` overlays the macOS app bundle, and `external/linux` overlays
`build/dist` beside the `.love` package. The staging folders are excluded from
the `.love` archive.

## Game Icons

Set an icon source in `project.toml`:

```toml
[game]
icon = "assets/icon.png"
```

Or set `t.window.icon = "assets/icon.png"` in an existing `conf.lua`. During a
Windows build, lovepack converts that image to 256px Windows icon files named
`game.ico` and `love.ico` inside `build/dist/<game>-win`, replacing the runtime
bundle's icons without modifying the source image or `.love` archive.

## Build Commands

Run the packaged game locally with the Love2D executable available on your
`PATH`:

```powershell
lovepack test
```

Remove generated Love2D builds, wheel distributions, and Python cache folders:

```powershell
poetry run lovepack clean
```

On Windows, `release.bat` runs clean, builds the current wheel, and
force-reinstalls it into the active pip environment:

```powershell
.\release.bat
```

Create a GitHub Actions workflow that builds Windows, Linux, and macOS
artifacts:

```powershell
lovepack github-action
```

This creates `.github/workflows/lovepack-build.yml`. Use `--force` to replace
an existing generated workflow. The workflow installs LuaJIT, runs
`lovepack build` on each platform, and uploads `build/dist/` as a separate
artifact. Windows uses Scoop for LuaJIT; Linux publishes the `.love` package
because LÖVE 11.5 does not publish a Linux runtime binary; macOS builds the
standalone app bundle. The workflow installs lovepack from its GitHub
repository so it uses the current platform fixes instead of a stale PyPI
release.

For a globally available command without publishing a package, install this
checkout in editable mode:

```powershell
py -m pip install --user --editable C:\path\to\lovepack
lovepack build
```