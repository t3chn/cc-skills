"""Tests for config module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from skillsctl.config import Config, ConfigError


def test_config_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading config from environment."""
    monkeypatch.setenv("SKILLS_REPO_URL", "https://github.com/test/skills.git")
    monkeypatch.setenv("SKILLS_REPO_BRANCH", "develop")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config.load(Path(tmpdir))
        assert config.repo_url == "https://github.com/test/skills.git"
        assert config.branch == "develop"


def test_config_load_from_file() -> None:
    """Test loading config from project config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".claude"
        config_dir.mkdir()

        config_file = config_dir / "skills.config.json"
        with open(config_file, "w") as f:
            json.dump({"repo_url": "https://github.com/project/skills.git", "branch": "main"}, f)

        # Clear env vars
        env_backup = os.environ.get("SKILLS_REPO_URL")
        if "SKILLS_REPO_URL" in os.environ:
            del os.environ["SKILLS_REPO_URL"]

        try:
            config = Config.load(Path(tmpdir))
            assert config.repo_url == "https://github.com/project/skills.git"
            assert config.branch == "main"
        finally:
            if env_backup:
                os.environ["SKILLS_REPO_URL"] = env_backup


def test_config_env_overrides_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override file config."""
    monkeypatch.setenv("SKILLS_REPO_URL", "https://github.com/env/skills.git")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".claude"
        config_dir.mkdir()

        config_file = config_dir / "skills.config.json"
        with open(config_file, "w") as f:
            json.dump({"repo_url": "https://github.com/file/skills.git"}, f)

        config = Config.load(Path(tmpdir))
        # Env should take precedence
        assert config.repo_url == "https://github.com/env/skills.git"


def test_config_load_missing() -> None:
    """Test loading config when nothing is configured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Clear env vars
        env_backup = os.environ.get("SKILLS_REPO_URL")
        if "SKILLS_REPO_URL" in os.environ:
            del os.environ["SKILLS_REPO_URL"]

        try:
            with pytest.raises(ConfigError, match="No skills repository URL"):
                Config.load(Path(tmpdir))
        finally:
            if env_backup:
                os.environ["SKILLS_REPO_URL"] = env_backup


def test_config_save() -> None:
    """Test saving config to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(
            repo_url="https://github.com/test/skills.git",
            branch="feature",
        )
        config.save(Path(tmpdir))

        config_file = Path(tmpdir) / ".claude" / "skills.config.json"
        assert config_file.exists()

        with open(config_file) as f:
            data = json.load(f)
        assert data["repo_url"] == "https://github.com/test/skills.git"
        assert data["branch"] == "feature"
