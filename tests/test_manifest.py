"""Tests for manifest module."""

import tempfile
from pathlib import Path

from skillsctl.manifest import Manifest


def test_manifest_load_empty() -> None:
    """Test loading non-existent manifest returns empty."""
    manifest = Manifest.load(Path("/nonexistent/path"))
    assert manifest.is_empty()
    assert len(manifest.skill_ids) == 0


def test_manifest_load_with_skills() -> None:
    """Test loading manifest with skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "skills.manifest"
        with open(manifest_path, "w") as f:
            f.write("# Comment line\n")
            f.write("\n")  # Empty line
            f.write("skill-1\n")
            f.write("skill-2\n")

        manifest = Manifest.load(manifest_path)
        assert not manifest.is_empty()
        assert manifest.skill_ids == {"skill-1", "skill-2"}


def test_manifest_add_remove() -> None:
    """Test adding and removing skills."""
    manifest = Manifest(set())

    manifest.add("skill-1")
    assert manifest.contains("skill-1")
    assert len(manifest.skill_ids) == 1

    manifest.add("skill-2")
    assert len(manifest.skill_ids) == 2

    manifest.remove("skill-1")
    assert not manifest.contains("skill-1")
    assert manifest.contains("skill-2")


def test_manifest_set_skills() -> None:
    """Test setting exact skill list."""
    manifest = Manifest({"old-1", "old-2"})

    manifest.set_skills({"new-1", "new-2", "new-3"})
    assert manifest.skill_ids == {"new-1", "new-2", "new-3"}


def test_manifest_save_and_load() -> None:
    """Test saving and reloading manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "test.manifest"

        # Create and save
        manifest = Manifest({"skill-a", "skill-b", "skill-c"})
        manifest.save(manifest_path)

        # Reload
        loaded = Manifest.load(manifest_path)
        assert loaded.skill_ids == {"skill-a", "skill-b", "skill-c"}


def test_manifest_remove_nonexistent() -> None:
    """Test removing skill that doesn't exist (should not error)."""
    manifest = Manifest({"skill-1"})
    manifest.remove("nonexistent")  # Should not raise
    assert manifest.skill_ids == {"skill-1"}
