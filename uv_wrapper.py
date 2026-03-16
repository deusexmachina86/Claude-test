#!/usr/bin/env python3
"""CLI wrapper around uv — common Python project workflows in one command."""

import argparse
import subprocess
import sys


def run(cmd: list[str]) -> int:
    result = subprocess.run(cmd)
    return result.returncode


def cmd_init(args):
    """Initialize a new project."""
    return run(["uv", "init", args.name])


def cmd_install(args):
    """Install dependencies (uv sync)."""
    command = ["uv", "sync"]
    if args.no_dev:
        command += ["--no-group", "dev"]
    if args.group:
        for g in args.group:
            command += ["--group", g]
    return run(command)


def cmd_add(args):
    """Add a dependency."""
    command = ["uv", "add"]
    if args.dev:
        command.append("--dev")
    elif args.group:
        command += ["--group", args.group]
    command += args.packages
    return run(command)


def cmd_remove(args):
    """Remove a dependency."""
    command = ["uv", "remove"] + args.packages
    if args.group:
        command += ["--group", args.group]
    return run(command)


def cmd_run(args):
    """Run a command inside the project environment."""
    return run(["uv", "run"] + args.command)


def cmd_upgrade(args):
    """Upgrade dependencies."""
    if args.package:
        return run(["uv", "sync", "--upgrade-package", args.package])
    return run(["uv", "lock", "--upgrade"])


def cmd_python(args):
    """Install a Python version."""
    return run(["uv", "python", "install", args.version])


def cmd_tool(args):
    """Run a disposable tool without installing it."""
    command = ["uv", "tool", "run"]
    if args.from_pkg:
        command += ["--from", args.from_pkg]
    command += args.tool_args
    return run(command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uvw",
        description="CLI wrapper around uv for common Python project workflows.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Create a new project")
    p_init.add_argument("name", help="Project name / directory")
    p_init.set_defaults(func=cmd_init)

    # install
    p_install = sub.add_parser("install", help="Install project dependencies (uv sync)")
    p_install.add_argument("--no-dev", action="store_true", help="Exclude dev dependencies")
    p_install.add_argument("--group", action="append", metavar="GROUP", help="Include a dependency group (repeatable)")
    p_install.set_defaults(func=cmd_install)

    # add
    p_add = sub.add_parser("add", help="Add one or more packages")
    p_add.add_argument("packages", nargs="+", metavar="PACKAGE")
    p_add.add_argument("--dev", action="store_true", help="Add to the dev group")
    p_add.add_argument("--group", metavar="GROUP", help="Add to a named dependency group")
    p_add.set_defaults(func=cmd_add)

    # remove
    p_remove = sub.add_parser("remove", help="Remove one or more packages")
    p_remove.add_argument("packages", nargs="+", metavar="PACKAGE")
    p_remove.add_argument("--group", metavar="GROUP", help="Remove from a named dependency group")
    p_remove.set_defaults(func=cmd_remove)

    # run
    p_run = sub.add_parser("run", help="Run a command in the project environment")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="Command and arguments to run")
    p_run.set_defaults(func=cmd_run)

    # upgrade
    p_upgrade = sub.add_parser("upgrade", help="Upgrade dependencies")
    p_upgrade.add_argument("package", nargs="?", help="Upgrade a specific package (omit for all)")
    p_upgrade.set_defaults(func=cmd_upgrade)

    # python
    p_python = sub.add_parser("python", help="Install a Python version")
    p_python.add_argument("version", help="Python version, e.g. 3.12")
    p_python.set_defaults(func=cmd_python)

    # tool
    p_tool = sub.add_parser("tool", help="Run a disposable CLI tool (uvx)")
    p_tool.add_argument("--from", dest="from_pkg", metavar="PKG", help="Package to import the tool from")
    p_tool.add_argument("tool_args", nargs=argparse.REMAINDER, help="Tool name and arguments")
    p_tool.set_defaults(func=cmd_tool)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
