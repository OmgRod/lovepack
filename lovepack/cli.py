import argparse
import sys
from pathlib import Path

from .clean import clean_project
from .config import configure_project, initialize_project_files, load_config
from .conf import ensure_conf_lua
from .packaging import build_love_package
from .runtime import build_executable


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Error: {message}\n")
        self.print_help()
        sys.exit(2)


def create_parser():
    parser = CustomArgumentParser(
        prog="lovepack",
        description="lovepack: LÖVE engine packaging and distribution toolchain",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    subparsers.add_parser("init", help="Initialize project.toml, .loveignore, and conf.lua")
    subparsers.add_parser("pack", help="Package project source into a .love zip archive")
    subparsers.add_parser("build", help="Package project and fuse with LÖVE binaries into an executable")
    subparsers.add_parser("clean", help="Remove generated build, distribution, and Python cache files")

    config_parser = subparsers.add_parser("config", help="Read and update project.toml settings")
    config_actions = config_parser.add_subparsers(dest="config_action", required=True)
    config_actions.add_parser("show", help="Print all project settings")

    get_parser = config_actions.add_parser("get", help="Print one setting by dotted key")
    get_parser.add_argument("key", help="Setting key, for example build.compile_bytecode")

    set_parser = config_actions.add_parser("set", help="Set a typed TOML value")
    set_parser.add_argument("key", help="Setting key, for example build.compile_bytecode")
    set_parser.add_argument("value", help="TOML value, for example true, 1280, or 'arcade'")
    set_parser.add_argument("--string", action="store_true", help="Treat value as a literal string")

    unset_parser = config_actions.add_parser("unset", help="Remove one setting by dotted key")
    unset_parser.add_argument("key", help="Setting key, for example build.lua_compiler")
    return parser


def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    root_dir = Path.cwd()
    try:
        if args.command == "init":
            print("\n--- Initializing lovepack environment ---")
            initialize_project_files(root_dir)
            ensure_conf_lua(root_dir, load_config(root_dir))
            print("[SUCCESS] Project files generated.")
        elif args.command == "config":
            configure_project(
                root_dir,
                args.config_action,
                getattr(args, "key", None),
                getattr(args, "value", None),
                getattr(args, "string", False),
            )
        elif args.command == "pack":
            build_love_package(root_dir, load_config(root_dir))
        elif args.command == "build":
            config = load_config(root_dir)
            love_file = build_love_package(root_dir, config)
            build_executable(root_dir, config, love_file)
        elif args.command == "clean":
            clean_project(root_dir)
    except (KeyError, ValueError, RuntimeError) as error:
        print(f"[ERROR] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
