"""Git operations for skillsctl."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitStatus:
    """Git repository status."""

    is_repo: bool
    is_dirty: bool
    git_version: str
    has_sparse_checkout: bool


class GitOps:
    """Git operations manager."""

    def __init__(self, project_root: Path) -> None:
        """Initialize with project root."""
        self.project_root = project_root

    def _run(
        self,
        args: list[str],
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command.

        Args:
            args: Git command arguments (without 'git').
            cwd: Working directory. Defaults to project root.
            check: Raise on non-zero exit code.

        Returns:
            Completed process.
        """
        if cwd is None:
            cwd = self.project_root

        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
        )

    def get_version(self) -> str:
        """Get git version."""
        try:
            result = self._run(["--version"], check=False)
            if result.returncode == 0:
                # Parse "git version X.Y.Z ..."
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    return parts[2]
            return "unknown"
        except FileNotFoundError:
            return "not installed"

    def is_repo(self) -> bool:
        """Check if project root is a git repository."""
        result = self._run(["rev-parse", "--git-dir"], check=False)
        return result.returncode == 0

    def get_status(self) -> GitStatus:
        """Get comprehensive git status."""
        is_repo = self.is_repo()
        git_version = self.get_version()

        is_dirty = False
        has_sparse_checkout = False

        if is_repo:
            # Check for uncommitted changes
            result = self._run(["status", "--porcelain"], check=False)
            is_dirty = bool(result.stdout.strip())

            # Check if sparse-checkout is available
            result = self._run(["sparse-checkout", "list"], check=False)
            has_sparse_checkout = result.returncode == 0

        return GitStatus(
            is_repo=is_repo,
            is_dirty=is_dirty,
            git_version=git_version,
            has_sparse_checkout=has_sparse_checkout,
        )

    def submodule_add(
        self,
        url: str,
        path: Path,
        branch: str = "main",
    ) -> None:
        """Add a git submodule.

        Args:
            url: Repository URL.
            path: Submodule path relative to project root.
            branch: Branch to track.
        """
        self._run(
            [
                "submodule",
                "add",
                "-b",
                branch,
                url,
                str(path),
            ]
        )

    def submodule_init(self, path: Path, depth: int = 1) -> None:
        """Initialize and update a submodule with shallow clone.

        Args:
            path: Submodule path relative to project root.
            depth: Clone depth (1 for shallow).
        """
        self._run(
            [
                "submodule",
                "update",
                "--init",
                f"--depth={depth}",
                "--",
                str(path),
            ]
        )

    def submodule_exists(self, path: Path) -> bool:
        """Check if a submodule exists at path."""
        gitmodules = self.project_root / ".gitmodules"
        if not gitmodules.exists():
            return False

        # Check if path is in .gitmodules
        content = gitmodules.read_text()
        return f"path = {path}" in content

    def submodule_is_dirty(self, path: Path) -> bool:
        """Check if submodule has uncommitted changes."""
        submodule_path = self.project_root / path
        if not submodule_path.exists():
            return False

        result = self._run(
            ["status", "--porcelain"],
            cwd=submodule_path,
            check=False,
        )
        return bool(result.stdout.strip())

    def sparse_checkout_init(self, path: Path) -> None:
        """Initialize sparse-checkout in cone mode for submodule.

        Args:
            path: Submodule path relative to project root.
        """
        submodule_path = self.project_root / path
        self._run(
            ["sparse-checkout", "init", "--cone"],
            cwd=submodule_path,
        )

    def sparse_checkout_set(self, path: Path, dirs: list[str]) -> None:
        """Set sparse-checkout directories for submodule.

        Args:
            path: Submodule path relative to project root.
            dirs: List of directories to include.
        """
        submodule_path = self.project_root / path
        # Use --stdin to pass directories
        dirs_input = "\n".join(dirs)
        subprocess.run(
            ["git", "sparse-checkout", "set", "--stdin"],
            cwd=submodule_path,
            input=dirs_input,
            capture_output=True,
            text=True,
            check=True,
        )

    def stage_files(self, files: list[Path]) -> None:
        """Stage files for commit.

        Args:
            files: List of file paths relative to project root.
        """
        str_files = [str(f) for f in files]
        self._run(["add", *str_files])


class GitError(Exception):
    """Git operation error."""
