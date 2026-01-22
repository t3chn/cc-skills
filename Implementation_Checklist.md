# Implementation Checklist: Skill Manager (v1)
Дата: 2026-01-22  
Цель: реализовать детерминированный менеджер скиллов для проектов (submodule + sparse-checkout + каталог + UX для агентов).

## A. Central skills-repo
- [ ] Принять единую структуру “skill = directory with SKILL.md”
  - [ ] Выбрать канонический префикс, напр. `skills/<id>/SKILL.md`
- [ ] Добавить `catalog/skills.json` (schema v1)
  - [ ] Поля: id, title, description, tags[], paths[], aliases[] (optional)
  - [ ] Убедиться, что `paths` — это директории для sparse-checkout (cone mode)
- [ ] (Опционально) Генератор каталога из frontmatter `SKILL.md` (v2)

## B. User-scoped skill “skill-manager”
### B1. Codex
- [ ] Создать папку `~/.codex/skills/skill-manager/`
- [ ] Добавить `SKILL.md` (инструкции агенту: suggest → choose → install)
- [ ] Добавить `scripts/skillsctl.py`
- [ ] Smoke test: Codex видит skill-manager

### B2. Claude
- [ ] Создать папку `~/.claude/skills/skill-manager/`
- [ ] Либо продублировать `scripts/skillsctl.py`, либо сделать ссылку на общий файл (если допустимо)
- [ ] Smoke test: Claude видит skill-manager

## C. CLI: `skillsctl` (Python 3 + Git)
### C1. Команды
- [ ] `catalog [--json]`
- [ ] `suggest "<query>" [--limit N] [--json]`
- [ ] `install <id...> [--stage] [--yes] [--claude]`
- [ ] `remove <id...> [--stage] [--yes] [--claude]`
- [ ] `set <id...> [--stage] [--yes] [--claude]`
- [ ] `sync [--stage] [--claude]`
- [ ] `status [--json]`
- [ ] `doctor`

### C2. Конфигурация
- [ ] env: `SKILLS_REPO_URL`, `SKILLS_REPO_BRANCH` (optional)
- [ ] project config: `.codex/skills.config.json` (repo_url, branch)

### C3. Project state
- [ ] Создание/обновление `.codex/skills.manifest`
- [ ] Добавление submodule: `.codex/skills` (git submodule add -b branch url path)
- [ ] Инициализация: `git submodule update --init --depth 1 -- .codex/skills`
- [ ] Sparse checkout:
  - [ ] `git -C .codex/skills sparse-checkout init --cone`
  - [ ] `git -C .codex/skills sparse-checkout set --stdin` (dirs = catalog + selected paths)

### C4. Claude export (wrappers)
- [ ] Команда `export-claude` или флаг `--claude`
- [ ] Генерация `.claude/skills/<id>/SKILL.md`
  - [ ] Frontmatter: name, description
  - [ ] Body: ссылка на canonical `.codex/skills/<path>/SKILL.md` + “follow these instructions”
- [ ] При remove/set — удалять/обновлять wrappers.

### C5. Безопасность и стабильность
- [ ] repo URL только из config/env (не из текста пользователя)
- [ ] Блокировать операции изменения sparse-набора, если `.codex/skills` dirty (или добавить `--force` позже)
- [ ] Idempotency: повторные команды безопасны

## D. Тестирование
### D1. Unit tests (если делаете pytest — optional; иначе минимальные self-checks)
- [ ] Парсер каталога (валидный/невалидный)
- [ ] Парсер manifest
- [ ] Скоринг suggest

### D2. Integration tests (обязательно)
- [ ] Временный проект:
  - [ ] install одного скилла
  - [ ] install второго
  - [ ] remove
  - [ ] set
  - [ ] sync после “сломанных” состояний (удаление рабочих папок)
- [ ] Проверка `git status --porcelain` после `--stage`

## E. Документация
- [ ] README для skill-manager: быстрый старт
- [ ] “Troubleshooting”:
  - [ ] нет git / старая версия git / нет sparse-checkout
  - [ ] submodule dirty
  - [ ] конфликтующие `.gitmodules`
- [ ] Примеры диалогов для агентов:
  - [ ] “установи скилл для pdf”
  - [ ] “покажи каталог”
  - [ ] “удали X”

## F. Rollout
- [ ] Добавить в шаблон нового проекта `.codex/skills.config.json` (repo_url)
- [ ] Рекомендовать команду `skillsctl sync` после клона
- [ ] (Опционально) pre-push hook: запрет пуша проекта при dirty `.codex/skills`
