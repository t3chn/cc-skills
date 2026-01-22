"""Manifest management for skillsctl."""

from __future__ import annotations

from pathlib import Path


class Manifest:
    """Skills manifest manager.

    The manifest file (.claude/skills.manifest) stores the list of installed
    skill IDs, one per line. Comments (lines starting with #) and empty lines
    are ignored.
    """

    def __init__(self, skill_ids: set[str]) -> None:
        """Initialize manifest with skill IDs."""
        self._skill_ids = skill_ids

    @classmethod
    def load(cls, manifest_path: Path) -> Manifest:
        """Load manifest from file.

        Args:
            manifest_path: Path to manifest file.

        Returns:
            Manifest instance. Empty if file doesn't exist.
        """
        if not manifest_path.exists():
            return cls(set())

        skill_ids: set[str] = set()
        with open(manifest_path) as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                skill_ids.add(line)

        return cls(skill_ids)

    def save(self, manifest_path: Path) -> None:
        """Save manifest to file.

        Args:
            manifest_path: Path to manifest file.
        """
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(manifest_path, "w") as f:
            f.write("# Skills manifest - managed by skillsctl\n")
            f.write("# Do not edit manually\n")
            for skill_id in sorted(self._skill_ids):
                f.write(f"{skill_id}\n")

    @property
    def skill_ids(self) -> set[str]:
        """Get installed skill IDs."""
        return self._skill_ids.copy()

    def add(self, skill_id: str) -> None:
        """Add a skill ID to the manifest."""
        self._skill_ids.add(skill_id)

    def remove(self, skill_id: str) -> None:
        """Remove a skill ID from the manifest."""
        self._skill_ids.discard(skill_id)

    def set_skills(self, skill_ids: set[str]) -> None:
        """Set the exact list of skill IDs."""
        self._skill_ids = skill_ids.copy()

    def contains(self, skill_id: str) -> bool:
        """Check if a skill ID is in the manifest."""
        return skill_id in self._skill_ids

    def is_empty(self) -> bool:
        """Check if manifest is empty."""
        return len(self._skill_ids) == 0
