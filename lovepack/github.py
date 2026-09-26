from pathlib import Path

DEFAULT_WORKFLOW_NAME = "lovepack-build.yml"

GITHUB_ACTION_WORKFLOW = """name: Build LÖVE game

on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    name: Build (${{ matrix.name }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - name: windows
            os: windows-latest
          - name: linux
            os: ubuntu-latest
          - name: macos
            os: macos-latest

    steps:
      - name: Check out project
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install LuaJIT on Windows
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            irm get.scoop.sh | iex
          }
          scoop install lua luajit
          echo "$env:USERPROFILE\\scoop\\shims" >> $env:GITHUB_PATH

      - name: Install LuaJIT on Linux
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y luajit

      - name: Install LuaJIT on macOS
        if: runner.os == 'macOS'
        run: |
          brew list luajit >/dev/null 2>&1 || brew install luajit
          echo "$(brew --prefix luajit)/bin" >> "$GITHUB_PATH"

      - name: Install lovepack
        run: python -m pip install --upgrade lovepack

      - name: Build game
        run: lovepack build

      - name: Upload game artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.name }}-build
          path: build/dist/
          if-no-files-found: error
"""


def setup_github_action(root_dir: Path, filename=DEFAULT_WORKFLOW_NAME, force=False):
    workflow_dir = root_dir / ".github" / "workflows"
    workflow_path = workflow_dir / filename
    existed = workflow_path.exists()
    if existed and not force:
        raise RuntimeError(
            f"Workflow already exists: {workflow_path.relative_to(root_dir)}. "
            "Use --force to replace it."
        )

    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(GITHUB_ACTION_WORKFLOW, encoding="utf-8")
    action = "replaced" if force and existed else "created"
    print(f"[SUCCESS] GitHub Actions workflow {action}: {workflow_path.relative_to(root_dir)}")
