"""Tests for CLI module."""

from skillsctl.cli import main


def test_main_no_args() -> None:
    """Test main with no arguments shows help."""
    result = main([])
    assert result == 1


def test_main_doctor() -> None:
    """Test doctor command runs."""
    result = main(["doctor"])
    assert result == 0
