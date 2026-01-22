"""Configuration management for skillsctl."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class Config:
    """Configuration for skillsctl."""

    repo_url: str
    branch: str = "main"
    skills_dir: str = ".claude/skills"
    manifest_path: str = ".claude/skills.manifest"
    config_path: str = ".claude/skills.config.json"

    @classmethod
    def load(cls, project_root: Path | None = None) -> Self:
        """Load configuration from environment and project config file.

        Priority:
        1. Environment variables (SKILLS_REPO_URL, SKILLS_REPO_BRANCH)
        2. Project config file (.claude/skills.config.json)

        Args:
            project_root: Project root directory. If None, uses current directory.

        Returns:
            Config instance.

        Raises:
            ConfigError: If no repo URL is configured.
        """
        if project_root is None:
            project_root = Path.cwd()

        # Start with defaults
        repo_url = os.environ.get("SKILLS_REPO_URL", "")
        branch = os.environ.get("SKILLS_REPO_BRANCH", "main")

        # Try to load from project config
        config_file = project_root / ".claude" / "skills.config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)
                if not repo_url and "repo_url" in data:
                    repo_url = data["repo_url"]
                if "branch" in data:
                    branch = data["branch"]
            except (json.JSONDecodeError, OSError):
                pass  # Ignore invalid config file

        if not repo_url:
            raise ConfigError(
                "No skills repository URL configured.\n"
                "Set SKILLS_REPO_URL environment variable or create "
                ".claude/skills.config.json with 'repo_url' field."
            )

        return cls(repo_url=repo_url, branch=branch)

    def save(self, project_root: Path) -> None:
        """Save configuration to project config file.

        Args:
            project_root: Project root directory.
        """
        config_dir = project_root / ".claude"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "skills.config.json"
        data = {
            "repo_url": self.repo_url,
            "branch": self.branch,
        }

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")


class ConfigError(Exception):
    """Configuration error."""
