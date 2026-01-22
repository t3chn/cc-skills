"""Tests for catalog module."""

import json
import tempfile
from pathlib import Path

import pytest

from skillsctl.catalog import Catalog, CatalogError, ScoredSkill, Skill


def test_skill_to_dict() -> None:
    """Test Skill.to_dict()."""
    skill = Skill(
        id="test-skill",
        title="Test Skill",
        description="A test skill",
        tags=["test", "example"],
        paths=["skills/test"],
        aliases=["ts"],
    )
    result = skill.to_dict()
    assert result["id"] == "test-skill"
    assert result["title"] == "Test Skill"
    assert result["tags"] == ["test", "example"]


def test_scored_skill_to_dict() -> None:
    """Test ScoredSkill.to_dict()."""
    skill = Skill(id="test", title="Test", description="", tags=[], paths=[], aliases=[])
    scored = ScoredSkill(skill=skill, score=50)
    result = scored.to_dict()
    assert result["id"] == "test"
    assert result["score"] == 50


def test_catalog_load_valid() -> None:
    """Test loading valid catalog."""
    catalog_data = [
        {
            "id": "skill-1",
            "title": "Skill One",
            "description": "First skill",
            "tags": ["tag1"],
            "paths": ["skills/one"],
        },
        {
            "id": "skill-2",
            "title": "Skill Two",
            "description": "Second skill",
            "tags": ["tag2"],
            "paths": ["skills/two"],
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog_data, f)

        catalog = Catalog.load(catalog_path)
        assert len(catalog.list_all()) == 2
        assert catalog.get("skill-1") is not None
        assert catalog.get("skill-1").title == "Skill One"


def test_catalog_load_missing_file() -> None:
    """Test loading non-existent catalog."""
    with pytest.raises(CatalogError, match="not found"):
        Catalog.load(Path("/nonexistent/path/skills.json"))


def test_catalog_load_invalid_json() -> None:
    """Test loading invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            f.write("not valid json")

        with pytest.raises(CatalogError, match="Invalid JSON"):
            Catalog.load(catalog_path)


def test_catalog_load_not_array() -> None:
    """Test loading JSON that's not an array."""
    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump({"key": "value"}, f)

        with pytest.raises(CatalogError, match="must be a JSON array"):
            Catalog.load(catalog_path)


def test_catalog_suggest_exact_id_match() -> None:
    """Test suggest with exact ID match."""
    catalog_data = [
        {"id": "pdf", "title": "PDF Tools", "description": "PDF handling", "tags": [], "paths": []},
        {
            "id": "pdf-advanced",
            "title": "Advanced PDF",
            "description": "More PDF",
            "tags": [],
            "paths": [],
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog_data, f)

        catalog = Catalog.load(catalog_path)
        results = catalog.suggest("pdf")

        # Exact match should be first with highest score
        assert len(results) == 2
        assert results[0].skill.id == "pdf"
        assert results[0].score > results[1].score


def test_catalog_suggest_tag_match() -> None:
    """Test suggest with tag matching."""
    catalog_data = [
        {
            "id": "skill-1",
            "title": "Skill One",
            "description": "",
            "tags": ["document", "pdf"],
            "paths": [],
        },
        {"id": "skill-2", "title": "Skill Two", "description": "", "tags": ["image"], "paths": []},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog_data, f)

        catalog = Catalog.load(catalog_path)
        results = catalog.suggest("document")

        assert len(results) == 1
        assert results[0].skill.id == "skill-1"


def test_catalog_suggest_limit() -> None:
    """Test suggest respects limit."""
    catalog_data = [
        {"id": f"skill-{i}", "title": f"Skill {i}", "description": "test", "tags": [], "paths": []}
        for i in range(20)
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog_data, f)

        catalog = Catalog.load(catalog_path)
        results = catalog.suggest("test", limit=5)

        assert len(results) == 5


def test_catalog_suggest_no_match() -> None:
    """Test suggest with no matches."""
    catalog_data = [
        {"id": "skill-1", "title": "Skill", "description": "", "tags": ["tag"], "paths": []},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "skills.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog_data, f)

        catalog = Catalog.load(catalog_path)
        results = catalog.suggest("nonexistent")

        assert len(results) == 0
