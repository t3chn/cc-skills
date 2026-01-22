# skillsctl

Skill Manager CLI for Claude Code projects.

## Quick Start

### 1. Configure skills repository

Set environment variable:

```bash
export SKILLS_REPO_URL=https://github.com/your-org/skills-repo.git
```

Or create `.claude/skills.config.json`:

```json
{
  "repo_url": "https://github.com/your-org/skills-repo.git",
  "branch": "main"
}
```

### 2. Install skills

```bash
# Search for skills
skillsctl suggest "pdf"

# Install specific skills
skillsctl install pdf-tools markdown-helper --yes

# List installed skills
skillsctl status
```

### 3. After git clone

```bash
skillsctl sync
```

## Commands

| Command | Description |
|---------|-------------|
| `catalog` | List all available skills |
| `suggest <query>` | Search for skills matching query |
| `install <id...>` | Install skills by ID |
| `remove <id...>` | Remove installed skills |
| `set <id...>` | Set exact skill list |
| `sync` | Restore skills from manifest |
| `status` | Show current installation status |
| `doctor` | Check environment and configuration |

### Common flags

- `--json` - Output as JSON (catalog, suggest, status)
- `--stage` - Stage git changes after operation
- `--yes, -y` - Skip confirmation prompts

## How It Works

1. Skills are stored in a central repository with `catalog/skills.json`
2. The repository is added as a git submodule at `.claude/skills/`
3. Only selected skills are checked out using `git sparse-checkout`
4. Installed skills are tracked in `.claude/skills.manifest`

## Development

### Setup

```bash
# Install dependencies
uv sync --dev

# Install pre-commit hooks
uvx pre-commit install
```

### Running tests

```bash
PYTHONPATH=src uvx pytest tests/ -v
```

### Linting

```bash
uvx ruff check src/ tests/
uvx ruff format src/ tests/
uvx mypy src/
```

## Troubleshooting

### "No skills repository URL configured"

Set `SKILLS_REPO_URL` environment variable or create `.claude/skills.config.json`.

### "Submodule has uncommitted changes"

Commit or discard changes in `.claude/skills/` before modifying skill selection.

### Skills not showing after clone

Run `skillsctl sync` to restore sparse-checkout state from manifest.

### Git version issues

Requires Git 2.25+ for sparse-checkout cone mode. Run `skillsctl doctor` to check.
