"""Tests for CLI module."""

from skillsctl.cli import main


def test_main_no_args() -> None:
    """Test main with no arguments shows help."""
    result = main([])
    assert result == 1


def test_main_version() -> None:
    """Test --version flag."""
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0


def test_main_status() -> None:
    """Test status command runs (may fail without git repo)."""
    # Status should work even without full config
    result = main(["status"])
    assert result == 0


def test_main_status_json() -> None:
    """Test status command with JSON output."""
    result = main(["status", "--json"])
    assert result == 0
