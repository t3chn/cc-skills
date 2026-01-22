"""Catalog management for skillsctl."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    """Represents a skill in the catalog."""

    id: str
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, str | list[str]]:
        """Convert skill to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "paths": self.paths,
            "aliases": self.aliases,
        }


@dataclass
class ScoredSkill:
    """Skill with search score."""

    skill: Skill
    score: int

    def to_dict(self) -> dict[str, str | list[str] | int]:
        """Convert to dictionary with score."""
        result: dict[str, str | list[str] | int] = {
            "id": self.skill.id,
            "title": self.skill.title,
            "description": self.skill.description,
            "tags": self.skill.tags,
            "paths": self.skill.paths,
            "aliases": self.skill.aliases,
            "score": self.score,
        }
        return result


class Catalog:
    """Skills catalog manager."""

    def __init__(self, skills: list[Skill]) -> None:
        """Initialize catalog with skills list."""
        self.skills = skills
        self._by_id: dict[str, Skill] = {s.id: s for s in skills}

    @classmethod
    def load(cls, catalog_path: Path) -> Catalog:
        """Load catalog from JSON file.

        Args:
            catalog_path: Path to catalog/skills.json file.

        Returns:
            Catalog instance.

        Raises:
            CatalogError: If catalog file is invalid.
        """
        if not catalog_path.exists():
            raise CatalogError(f"Catalog file not found: {catalog_path}")

        try:
            with open(catalog_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CatalogError(f"Invalid JSON in catalog: {e}") from e

        if not isinstance(data, list):
            raise CatalogError("Catalog must be a JSON array")

        skills = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if "id" not in item or "title" not in item:
                continue

            skill = Skill(
                id=item["id"],
                title=item["title"],
                description=item.get("description", ""),
                tags=item.get("tags", []),
                paths=item.get("paths", []),
                aliases=item.get("aliases", []),
            )
            skills.append(skill)

        return cls(skills)

    def get(self, skill_id: str) -> Skill | None:
        """Get skill by ID."""
        return self._by_id.get(skill_id)

    def list_all(self) -> list[Skill]:
        """List all skills."""
        return self.skills

    def suggest(self, query: str, limit: int = 10) -> list[ScoredSkill]:
        """Suggest skills based on query.

        Scoring algorithm (v1, deterministic):
        - Exact match on id (case-insensitive): +100
        - Prefix match on id: +40
        - Token match:
          - in tags: +20 per token
          - in title: +10
          - in description: +5
        - Alias match: same as id (exact +100, prefix +40)

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            List of scored skills, sorted by score descending.
        """
        query_lower = query.lower()
        # Tokenize query by non-alphanumeric characters
        tokens = [t for t in re.split(r"[^a-zA-Z0-9]+", query_lower) if t]

        scored: list[ScoredSkill] = []

        for skill in self.skills:
            score = 0
            id_lower = skill.id.lower()

            # Exact id match
            if id_lower == query_lower:
                score += 100
            # Prefix id match
            elif id_lower.startswith(query_lower):
                score += 40

            # Alias matching
            for alias in skill.aliases:
                alias_lower = alias.lower()
                if alias_lower == query_lower:
                    score += 100
                elif alias_lower.startswith(query_lower):
                    score += 40

            # Token matching
            title_lower = skill.title.lower()
            desc_lower = skill.description.lower()
            tags_lower = [t.lower() for t in skill.tags]

            for token in tokens:
                # Tags
                for tag in tags_lower:
                    if token in tag:
                        score += 20
                        break

                # Title
                if token in title_lower:
                    score += 10

                # Description
                if token in desc_lower:
                    score += 5

            if score > 0:
                scored.append(ScoredSkill(skill=skill, score=score))

        # Sort by score desc, then by id asc for stability
        scored.sort(key=lambda s: (-s.score, s.skill.id))

        return scored[:limit]


class CatalogError(Exception):
    """Catalog-related error."""
