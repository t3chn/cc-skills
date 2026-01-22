"""CLI entry point for skillsctl."""

import argparse
import sys


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
    install_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    # remove command
    remove_parser = subparsers.add_parser("remove", help="Remove skills")
    remove_parser.add_argument("ids", nargs="+", help="Skill IDs to remove")
    remove_parser.add_argument("--stage", action="store_true", help="Stage git changes")
    remove_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    # set command
    set_parser = subparsers.add_parser("set", help="Set exact skill list")
    set_parser.add_argument("ids", nargs="+", help="Skill IDs to set")
    set_parser.add_argument("--stage", action="store_true", help="Stage git changes")
    set_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

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

    # TODO: Implement command handlers
    print(f"Command '{args.command}' not yet implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
