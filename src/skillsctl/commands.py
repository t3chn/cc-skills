"""Command implementations for skillsctl."""

from __future__ import annotations

import contextlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .catalog import Catalog, CatalogError, Skill
from .config import Config, ConfigError
from .git_ops import GitOps
from .manifest import Manifest


@dataclass
class CommandContext:
    """Context for command execution."""

    project_root: Path
    config: Config | None
    git: GitOps
    catalog: Catalog | None
    manifest: Manifest

    @classmethod
    def create(cls, require_config: bool = True) -> CommandContext:
        """Create command context.

        Args:
            require_config: If True, raise error if config not found.

        Returns:
            CommandContext instance.
        """
        project_root = Path.cwd()
        git = GitOps(project_root)

        # Load config
        config: Config | None = None
        if require_config:
            config = Config.load(project_root)
        else:
            with contextlib.suppress(ConfigError):
                config = Config.load(project_root)

        # Load catalog if config available
        catalog: Catalog | None = None
        if config:
            skills_dir = project_root / config.skills_dir
            catalog_path = skills_dir / "catalog" / "skills.json"
            if catalog_path.exists():
                with contextlib.suppress(CatalogError):
                    catalog = Catalog.load(catalog_path)

        # Load manifest
        manifest_path = project_root / ".claude" / "skills.manifest"
        manifest = Manifest.load(manifest_path)

        return cls(
            project_root=project_root,
            config=config,
            git=git,
            catalog=catalog,
            manifest=manifest,
        )


def cmd_doctor() -> int:
    """Check environment and configuration."""
    project_root = Path.cwd()
    git = GitOps(project_root)
    status = git.get_status()

    print("skillsctl doctor")
    print("=" * 40)

    # Git check
    print(f"\nGit version: {status.git_version}")
    if status.git_version == "not installed":
        print("  ❌ Git is not installed")
        return 1
    print("  ✓ Git is installed")

    # Repository check
    if not status.is_repo:
        print("\n❌ Not a git repository")
        return 1
    print("  ✓ Is a git repository")

    # Sparse-checkout check
    if status.has_sparse_checkout:
        print("  ✓ Sparse-checkout is available")
    else:
        print("  ⚠ Sparse-checkout not initialized (will be set up on install)")

    # Config check
    print("\nConfiguration:")
    try:
        config = Config.load(project_root)
        print(f"  ✓ Repo URL: {config.repo_url}")
        print(f"  ✓ Branch: {config.branch}")
    except ConfigError as e:
        print(f"  ❌ {e}")
        return 1

    # Skills directory check
    skills_dir = project_root / config.skills_dir
    if skills_dir.exists():
        print(f"\n  ✓ Skills directory exists: {config.skills_dir}")

        # Check if it's a submodule
        if git.submodule_exists(Path(config.skills_dir)):
            print("  ✓ Is a git submodule")

            if git.submodule_is_dirty(Path(config.skills_dir)):
                print("  ⚠ Submodule has uncommitted changes")
        else:
            print("  ⚠ Not a git submodule")
    else:
        print(f"\n  ⚠ Skills directory not found: {config.skills_dir}")
        print("    Run 'skillsctl install <id>' to set up")

    # Manifest check
    manifest_path = project_root / ".claude" / "skills.manifest"
    manifest = Manifest.load(manifest_path)
    print("\nManifest:")
    if manifest.is_empty():
        print("  ⚠ No skills installed")
    else:
        print(f"  ✓ {len(manifest.skill_ids)} skill(s) installed:")
        for skill_id in sorted(manifest.skill_ids):
            print(f"    - {skill_id}")

    print("\n✓ All checks passed")
    return 0


def cmd_status(as_json: bool = False) -> int:
    """Show current status."""
    project_root = Path.cwd()
    git = GitOps(project_root)
    git_status = git.get_status()

    # Load config (don't require)
    config: Config | None = None
    with contextlib.suppress(ConfigError):
        config = Config.load(project_root)

    # Load manifest
    manifest_path = project_root / ".claude" / "skills.manifest"
    manifest = Manifest.load(manifest_path)

    # Check submodule
    submodule_present = False
    submodule_dirty = False
    if config:
        skills_dir = Path(config.skills_dir)
        submodule_present = git.submodule_exists(skills_dir)
        if submodule_present:
            submodule_dirty = git.submodule_is_dirty(skills_dir)

    selected_ids = sorted(manifest.skill_ids)

    result = {
        "selected_ids": selected_ids,
        "manifest_path": str(manifest_path),
        "submodule_present": submodule_present,
        "submodule_dirty": submodule_dirty,
        "git_version": git_status.git_version,
        "is_repo": git_status.is_repo,
    }

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print("skillsctl status")
        print("=" * 40)
        print(f"Git version: {git_status.git_version}")
        print(f"Is repository: {git_status.is_repo}")
        print(f"Submodule present: {submodule_present}")
        print(f"Submodule dirty: {submodule_dirty}")
        print(f"\nInstalled skills ({len(selected_ids)}):")
        if selected_ids:
            for skill_id in selected_ids:
                print(f"  - {skill_id}")
        else:
            print("  (none)")

    return 0


def cmd_catalog(as_json: bool = False) -> int:
    """List all available skills."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if ctx.catalog is None:
        print(
            "Error: Catalog not found. Run 'skillsctl sync' first.",
            file=sys.stderr,
        )
        return 1

    skills = ctx.catalog.list_all()

    if as_json:
        print(json.dumps([s.to_dict() for s in skills], indent=2))
    else:
        print(f"Available skills ({len(skills)}):")
        print("-" * 40)
        for skill in skills:
            tags = ", ".join(skill.tags) if skill.tags else "(no tags)"
            print(f"\n{skill.id} — {skill.title}")
            print(f"  tags: {tags}")
            if skill.description:
                # Truncate description to first line
                desc = skill.description.split("\n")[0][:80]
                print(f"  {desc}")

    return 0


def cmd_suggest(query: str, limit: int = 10, as_json: bool = False) -> int:
    """Suggest skills based on query."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if ctx.catalog is None:
        print(
            "Error: Catalog not found. Run 'skillsctl sync' first.",
            file=sys.stderr,
        )
        return 1

    results = ctx.catalog.suggest(query, limit=limit)

    if as_json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        if not results:
            print(f"No skills found matching '{query}'")
            return 0

        print(f"Skills matching '{query}' ({len(results)} results):")
        print("-" * 40)
        for scored in results:
            skill = scored.skill
            tags = ", ".join(skill.tags) if skill.tags else "(no tags)"
            print(f"\n{skill.id} — {skill.title} (score: {scored.score})")
            print(f"  tags: {tags}")
            if skill.description:
                desc = skill.description.split("\n")[0][:80]
                print(f"  {desc}")

    return 0


def cmd_install(
    ids: list[str],
    stage: bool = False,
    yes: bool = False,
) -> int:
    """Install skills."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not ctx.config:
        print("Error: No configuration found", file=sys.stderr)
        return 1

    skills_dir = Path(ctx.config.skills_dir)

    # Check if submodule exists, if not create it
    if not ctx.git.submodule_exists(skills_dir):
        print(f"Setting up skills submodule at {skills_dir}...")
        try:
            ctx.git.submodule_add(
                url=ctx.config.repo_url,
                path=skills_dir,
                branch=ctx.config.branch,
            )
            ctx.git.submodule_init(skills_dir)
            ctx.git.sparse_checkout_init(skills_dir)
        except Exception as e:
            print(f"Error setting up submodule: {e}", file=sys.stderr)
            return 1

    # Check for dirty submodule
    if ctx.git.submodule_is_dirty(skills_dir):
        print(
            "Error: Submodule has uncommitted changes. Commit or discard them first.",
            file=sys.stderr,
        )
        return 1

    # Reload catalog after submodule setup
    catalog_path = ctx.project_root / skills_dir / "catalog" / "skills.json"
    if catalog_path.exists():
        ctx.catalog = Catalog.load(catalog_path)

    if ctx.catalog is None:
        print("Error: Catalog not found in skills repository", file=sys.stderr)
        return 1

    # Validate skill IDs
    valid_ids: list[str] = []
    invalid_ids: list[str] = []
    for skill_id in ids:
        if ctx.catalog.get(skill_id):
            valid_ids.append(skill_id)
        else:
            invalid_ids.append(skill_id)

    if invalid_ids:
        print(f"Error: Unknown skill IDs: {', '.join(invalid_ids)}", file=sys.stderr)
        return 1

    # Get skills to install
    skills_to_install: list[Skill] = []
    for skill_id in valid_ids:
        if not ctx.manifest.contains(skill_id):
            skill = ctx.catalog.get(skill_id)
            if skill:
                skills_to_install.append(skill)
                ctx.manifest.add(skill_id)

    if not skills_to_install:
        print("All specified skills are already installed.")
        return 0

    # Confirm
    if not yes:
        print("Skills to install:")
        for skill in skills_to_install:
            print(f"  - {skill.id}: {skill.title}")
        response = input("\nProceed? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return 1

    # Collect all paths for sparse-checkout
    all_paths = ["catalog"]  # Always include catalog
    for skill_id in ctx.manifest.skill_ids:
        skill = ctx.catalog.get(skill_id)
        if skill:
            all_paths.extend(skill.paths)

    # Update sparse-checkout
    try:
        ctx.git.sparse_checkout_set(skills_dir, all_paths)
    except Exception as e:
        print(f"Error updating sparse-checkout: {e}", file=sys.stderr)
        return 1

    # Save manifest
    manifest_path = ctx.project_root / ".claude" / "skills.manifest"
    ctx.manifest.save(manifest_path)

    print(f"\n✓ Installed {len(skills_to_install)} skill(s)")
    for skill in skills_to_install:
        print(f"  - {skill.id}")

    # Stage files if requested
    if stage:
        files_to_stage = [
            Path(".gitmodules"),
            skills_dir,
            Path(".claude/skills.manifest"),
        ]
        ctx.git.stage_files(files_to_stage)
        print("\n✓ Changes staged")

    return 0


def cmd_remove(
    ids: list[str],
    stage: bool = False,
    yes: bool = False,
) -> int:
    """Remove skills."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not ctx.config:
        print("Error: No configuration found", file=sys.stderr)
        return 1

    skills_dir = Path(ctx.config.skills_dir)

    # Check for dirty submodule
    if ctx.git.submodule_is_dirty(skills_dir):
        print(
            "Error: Submodule has uncommitted changes. Commit or discard them first.",
            file=sys.stderr,
        )
        return 1

    # Check which skills are installed
    skills_to_remove: list[str] = []
    not_installed: list[str] = []
    for skill_id in ids:
        if ctx.manifest.contains(skill_id):
            skills_to_remove.append(skill_id)
        else:
            not_installed.append(skill_id)

    if not_installed:
        print(f"Warning: Not installed: {', '.join(not_installed)}")

    if not skills_to_remove:
        print("No skills to remove.")
        return 0

    # Confirm
    if not yes:
        print("Skills to remove:")
        for skill_id in skills_to_remove:
            print(f"  - {skill_id}")
        response = input("\nProceed? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return 1

    # Remove from manifest
    for skill_id in skills_to_remove:
        ctx.manifest.remove(skill_id)

    # Reload catalog for paths
    if ctx.catalog is None:
        catalog_path = ctx.project_root / skills_dir / "catalog" / "skills.json"
        if catalog_path.exists():
            ctx.catalog = Catalog.load(catalog_path)

    # Update sparse-checkout with remaining skills
    all_paths = ["catalog"]
    if ctx.catalog:
        for skill_id in ctx.manifest.skill_ids:
            skill = ctx.catalog.get(skill_id)
            if skill:
                all_paths.extend(skill.paths)

    try:
        ctx.git.sparse_checkout_set(skills_dir, all_paths)
    except Exception as e:
        print(f"Error updating sparse-checkout: {e}", file=sys.stderr)
        return 1

    # Save manifest
    manifest_path = ctx.project_root / ".claude" / "skills.manifest"
    ctx.manifest.save(manifest_path)

    print(f"\n✓ Removed {len(skills_to_remove)} skill(s)")
    for skill_id in skills_to_remove:
        print(f"  - {skill_id}")

    # Stage files if requested
    if stage:
        files_to_stage = [
            skills_dir,
            Path(".claude/skills.manifest"),
        ]
        ctx.git.stage_files(files_to_stage)
        print("\n✓ Changes staged")

    return 0


def cmd_set(
    ids: list[str],
    stage: bool = False,
    yes: bool = False,
) -> int:
    """Set exact skill list."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not ctx.config:
        print("Error: No configuration found", file=sys.stderr)
        return 1

    skills_dir = Path(ctx.config.skills_dir)

    # Check for dirty submodule
    if ctx.git.submodule_is_dirty(skills_dir):
        print(
            "Error: Submodule has uncommitted changes. Commit or discard them first.",
            file=sys.stderr,
        )
        return 1

    # Check if submodule exists, if not create it
    if not ctx.git.submodule_exists(skills_dir):
        print(f"Setting up skills submodule at {skills_dir}...")
        try:
            ctx.git.submodule_add(
                url=ctx.config.repo_url,
                path=skills_dir,
                branch=ctx.config.branch,
            )
            ctx.git.submodule_init(skills_dir)
            ctx.git.sparse_checkout_init(skills_dir)
        except Exception as e:
            print(f"Error setting up submodule: {e}", file=sys.stderr)
            return 1

    # Reload catalog
    catalog_path = ctx.project_root / skills_dir / "catalog" / "skills.json"
    if catalog_path.exists():
        ctx.catalog = Catalog.load(catalog_path)

    if ctx.catalog is None:
        print("Error: Catalog not found in skills repository", file=sys.stderr)
        return 1

    # Validate skill IDs
    valid_ids: list[str] = []
    invalid_ids: list[str] = []
    for skill_id in ids:
        if ctx.catalog.get(skill_id):
            valid_ids.append(skill_id)
        else:
            invalid_ids.append(skill_id)

    if invalid_ids:
        print(f"Error: Unknown skill IDs: {', '.join(invalid_ids)}", file=sys.stderr)
        return 1

    # Show changes
    current = ctx.manifest.skill_ids
    new_set = set(valid_ids)
    to_add = new_set - current
    to_remove = current - new_set

    if not to_add and not to_remove:
        print("No changes needed.")
        return 0

    # Confirm
    if not yes:
        if to_add:
            print("Skills to add:")
            for skill_id in to_add:
                print(f"  + {skill_id}")
        if to_remove:
            print("Skills to remove:")
            for skill_id in to_remove:
                print(f"  - {skill_id}")
        response = input("\nProceed? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return 1

    # Set manifest
    ctx.manifest.set_skills(new_set)

    # Update sparse-checkout
    all_paths = ["catalog"]
    for skill_id in ctx.manifest.skill_ids:
        skill = ctx.catalog.get(skill_id)
        if skill:
            all_paths.extend(skill.paths)

    try:
        ctx.git.sparse_checkout_set(skills_dir, all_paths)
    except Exception as e:
        print(f"Error updating sparse-checkout: {e}", file=sys.stderr)
        return 1

    # Save manifest
    manifest_path = ctx.project_root / ".claude" / "skills.manifest"
    ctx.manifest.save(manifest_path)

    print("\n✓ Skills set updated")
    if to_add:
        for skill_id in to_add:
            print(f"  + {skill_id}")
    if to_remove:
        for skill_id in to_remove:
            print(f"  - {skill_id}")

    # Stage files if requested
    if stage:
        files_to_stage = [
            Path(".gitmodules"),
            skills_dir,
            Path(".claude/skills.manifest"),
        ]
        ctx.git.stage_files(files_to_stage)
        print("\n✓ Changes staged")

    return 0


def cmd_sync(stage: bool = False) -> int:
    """Sync skills from manifest."""
    try:
        ctx = CommandContext.create(require_config=True)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not ctx.config:
        print("Error: No configuration found", file=sys.stderr)
        return 1

    skills_dir = Path(ctx.config.skills_dir)

    # Initialize submodule if needed
    if not ctx.git.submodule_exists(skills_dir):
        print("Submodule not found. Nothing to sync.")
        return 0

    # Initialize/update submodule
    print("Updating submodule...")
    try:
        ctx.git.submodule_init(skills_dir)
    except Exception as e:
        print(f"Error updating submodule: {e}", file=sys.stderr)
        return 1

    # Initialize sparse-checkout if needed
    submodule_path = ctx.project_root / skills_dir
    sparse_file = submodule_path / ".git" / "info" / "sparse-checkout"
    if not sparse_file.exists():
        ctx.git.sparse_checkout_init(skills_dir)

    # Reload catalog
    catalog_path = ctx.project_root / skills_dir / "catalog" / "skills.json"
    if catalog_path.exists():
        ctx.catalog = Catalog.load(catalog_path)

    # Update sparse-checkout from manifest
    all_paths = ["catalog"]
    if ctx.catalog:
        for skill_id in ctx.manifest.skill_ids:
            skill = ctx.catalog.get(skill_id)
            if skill:
                all_paths.extend(skill.paths)

    try:
        ctx.git.sparse_checkout_set(skills_dir, all_paths)
    except Exception as e:
        print(f"Error updating sparse-checkout: {e}", file=sys.stderr)
        return 1

    print(f"\n✓ Synced {len(ctx.manifest.skill_ids)} skill(s)")
    for skill_id in sorted(ctx.manifest.skill_ids):
        print(f"  - {skill_id}")

    # Stage files if requested
    if stage:
        files_to_stage = [
            skills_dir,
        ]
        ctx.git.stage_files(files_to_stage)
        print("\n✓ Changes staged")

    return 0
