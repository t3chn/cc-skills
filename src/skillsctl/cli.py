"""CLI entry point for skillsctl."""

from __future__ import annotations

import argparse
import sys

from .commands import (
    cmd_catalog,
    cmd_doctor,
    cmd_install,
    cmd_remove,
    cmd_set,
    cmd_status,
    cmd_suggest,
    cmd_sync,
)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for skillsctl CLI.

    Args:
        argv: Command line arguments. If None, uses sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        prog="skillsctl",
        description="Skill Manager CLI for Claude Code projects",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # catalog command
    catalog_parser = subparsers.add_parser("catalog", help="List all available skills")
    catalog_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest skills based on query")
    suggest_parser.add_argument("query", help="Search query")
    suggest_parser.add_argument("--limit", type=int, default=10, help="Max results")
    suggest_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # install command
    install_parser = subparsers.add_parser("install", help="Install skills")
    install_parser.add_argument("ids", nargs="+", help="Skill IDs to install")
    install_parser.add_argument("--stage", action="store_true", help="Stage git changes")
    install_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # remove command
    remove_parser = subparsers.add_parser("remove", help="Remove skills")
    remove_parser.add_argument("ids", nargs="+", help="Skill IDs to remove")
    remove_parser.add_argument("--stage", action="store_true", help="Stage git changes")
    remove_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # set command
    set_parser = subparsers.add_parser("set", help="Set exact skill list")
    set_parser.add_argument("ids", nargs="+", help="Skill IDs to set")
    set_parser.add_argument("--stage", action="store_true", help="Stage git changes")
    set_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync skills from manifest")
    sync_parser.add_argument("--stage", action="store_true", help="Stage git changes")

    # status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # doctor command
    subparsers.add_parser("doctor", help="Check environment and configuration")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    # Dispatch commands
    if args.command == "doctor":
        return cmd_doctor()
    elif args.command == "status":
        return cmd_status(as_json=args.json)
    elif args.command == "catalog":
        return cmd_catalog(as_json=args.json)
    elif args.command == "suggest":
        return cmd_suggest(args.query, limit=args.limit, as_json=args.json)
    elif args.command == "install":
        return cmd_install(args.ids, stage=args.stage, yes=args.yes)
    elif args.command == "remove":
        return cmd_remove(args.ids, stage=args.stage, yes=args.yes)
    elif args.command == "set":
        return cmd_set(args.ids, stage=args.stage, yes=args.yes)
    elif args.command == "sync":
        return cmd_sync(stage=args.stage)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
