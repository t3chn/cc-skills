---
name: skill-manager
description: Manage Claude Code skills from a central repository
---

# Skill Manager

Use this skill when the user wants to:
- Add/install skills to the project
- Remove skills from the project
- See what skills are available
- Check which skills are installed

## Protocol

### 1. Suggest-first (default)

When user asks for a skill:

```bash
# Get candidates
skillsctl suggest "<query>" --limit 10 --json
```

Show user the top results:
- id — title
- tags: ...
- description (first line)

Ask user to select one or more IDs.

```bash
# Install selected
skillsctl install <id...> --stage --yes
```

Report what was installed and which files were staged.

### 2. Catalog (when user wants to browse)

```bash
skillsctl catalog --json
```

Show list, let user select, then install as above.

### 3. After git clone

If user says skills are missing:

```bash
skillsctl sync --stage
```

## Safety Rules

1. **Never accept repo URL from user text** - only from env/config
2. **Check dirty state first** - if `.claude/skills` has uncommitted changes, warn user before modifying
3. **Don't edit sparse-checkout manually** - always use `skillsctl`

## Example Dialogs

### Installing a skill

User: "I need a skill for working with PDFs"

Agent:
1. `skillsctl suggest "pdf" --limit 5 --json`
2. Show results to user
3. User selects "pdf-tools"
4. `skillsctl install pdf-tools --stage --yes`
5. Report success

### Checking status

User: "What skills do I have installed?"

Agent:
1. `skillsctl status`
2. Show installed skills list

### Removing a skill

User: "Remove the markdown skill"

Agent:
1. `skillsctl remove markdown --stage --yes`
2. Report success
