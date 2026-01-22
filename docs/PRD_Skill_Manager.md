# PRD: Skill Manager для проектов (Codex CLI + Claude Code)
Версия: 1.0
Дата: 2026-01-22
Владелец: (заполнить)
Статус: Draft

## 1) Проблема
### 1.1 Текущее поведение
- Есть центральный репозиторий скиллов (далее **skills-repo**).
- Для конкретного проекта берётся **часть** скиллов (1–N) и копируется в папку проекта.
- Во время работы над проектом скиллы улучшаются в копии проекта → затем требуется вручную переносить улучшения назад в skills-repo.

### 1.2 Боль
- Появляются **две копии одного скилла** (central и project), что создаёт:
  - риск расхождения версий,
  - вероятность забыть перенести улучшения,
  - отсутствие детерминированного процесса для AI-агента.

## 2) Цели и нецели
### 2.1 Цели (Goals)
G1. В любом проекте можно установить **ровно нужные** скиллы (вплоть до одного) без копирования.
G2. Улучшения, сделанные в проекте, попадают в **тот же самый** репозиторий-источник (skills-repo).
G3. UX для пользователя: “скажи что нужно” → агент предложил список → пользователь выбрал → агент установил.
G4. UX для агента: минимальный набор детерминированных команд (без «магии» в промпте).
G5. Воспроизводимость: состояние проекта описывается в git (manifest), после клона всё восстанавливается одной командой.

### 2.2 Нецели (Non-goals) — v1
N1. Полноценный “магазин/маркетплейс” скиллов.
N2. Векторный/LLM-поиск по репозиторию (в v1 — лексический ранжировщик по каталогу).
N3. Авто-обновления на “самую свежую версию” без явного действия пользователя.
N4. GUI/TUI. Всё — через CLI + диалог агента.

## 3) Ключевая идея решения
### 3.1 Единый источник истины
Подключаем **skills-repo** в проект как **git submodule** (в `.codex/skills/`), а видимое содержимое ограничиваем через **git sparse-checkout** так, чтобы в проект “попадали” только выбранные скиллы.

Почему `.codex/skills/`:
- Документация Codex рекомендует repo-scoped навыки хранить именно там, чтобы они “путешествовали” вместе с кодом.
  (См. References: OpenAI Codex “Create skills”.)

Почему sparse-checkout:
- sparse-checkout позволяет держать в working tree только подмножество директорий (cone mode) и менять набор без копирования файлов.
  (См. References: git-scm “git sparse-checkout”.)

### 3.2 Manifest как «контракт»
Выбранный набор скиллов хранится в файле проекта `.codex/skills.manifest` (коммитится в git).
Команда `skillsctl sync` восстанавливает sparse-checkout из manifest после клона/восстановления окружения.

> Важно: `git sparse-checkout` хранит правила в `$GIT_DIR/info/sparse-checkout`, т.е. не в репозитории. Поэтому manifest обязателен.

## 4) Пользователи и сценарии
### Persona A: разработчик
- Хочет быстро добавить 1–2 скилла.
- Хочет не думать о переносе улучшений обратно в central.

### Persona B: AI-агент (Codex CLI / Claude Code)
- Хочет стабильный протокол и команды, которые работают одинаково в любом проекте.
- Хочет структурированный каталог вместо “прочитай весь репозиторий”.

### Основные сценарии (User Stories)
US1. “Мне нужен скилл для PDF” → агент предлагает варианты → пользователь выбирает → установка.
US2. “Покажи каталог скиллов” → выбрать → установка.
US3. “Удалить скилл X” → удаление из набора → рабочее дерево обновлено.
US4. “После git clone скиллы не появились” → `sync` → восстановление.

## 5) UX: поведение агента (Protocol)
### 5.1 Общий принцип
Агент:
1) **получает кандидатов** (`suggest`/`catalog`)
2) **показывает пользователю** список (кратко, с id)
3) **получает выбор** (один или несколько id)
4) **применяет** (`install`)
5) сообщает, что изменилось (файлы/статус git)

### 5.2 Поток “suggest → choose → install”
**Input:** “поставь скилл для pdf”
**Agent steps:**
- `skillsctl suggest "pdf" --limit 10 --json`
- Показать пользователю топ-10:
  - `id`, `title`, `tags`, `1-2 строки description`
- Спросить: “какие id поставить?” (если пользователь не сказал “выбирай сам”)
- `skillsctl install <id...> --stage --yes`
- Итог:
  - “Добавлено: …”
  - “Файлы staged: .gitmodules, .codex/skills(manifest/gitlink), .codex/skills.manifest”

### 5.3 Поток “catalog → choose → install”
**Input:** “какие есть скиллы?”
- `skillsctl catalog --json` → вывести список → установка как выше.

### 5.4 Поток “sync”
**Input:** “в проекте не вижу нужные скиллы”
- `skillsctl sync --stage` (stage опционально)
- Сообщить статус.

## 6) Функциональные требования (FR)
### 6.1 Центральный skills-repo
FR-1. В skills-repo должен быть каталог **машиночитаемый**: `catalog/skills.json`.
FR-2. Каждый скилл должен иметь директорию с `SKILL.md` внутри (структура определяется каталогом).
FR-3. Каталог должен содержать минимум:
- `id` (уникальный),
- `title`,
- `description`,
- `tags` (array),
- `paths` (array директорий, которые нужно включить в sparse-checkout при установке),
- (опционально) `aliases` (array строк).

### 6.2 Состояние проекта
FR-4. Submodule в проекте создаётся в `REPO_ROOT/.codex/skills` (repo-scoped skills для Codex).
FR-5. Manifest: `REPO_ROOT/.codex/skills.manifest` (коммитится).
FR-6. Config: `REPO_ROOT/.codex/skills.config.json` (опционально, если не задано env).
FR-7. Sparse-checkout внутри submodule:
- cone-mode,
- всегда включает `catalog/`,
- включает все `paths` выбранных скиллов.

FR-8. Идемпотентность:
- повторный `install` тех же id не ломает состояние,
- `sync` всегда приводит submodule working tree к состоянию manifest.

### 6.3 Утилита управления: `skillsctl`
FR-9. Утилита реализуется как CLI (Python 3 + Git), без сторонних зависимостей.
FR-10. Команды (обязательные):
- `catalog [--json]`
- `suggest "<query>" [--limit N] [--json]`
- `install <id...> [--stage] [--yes] [--claude]`
- `remove <id...> [--stage] [--yes] [--claude]`
- `set <id...> [--stage] [--yes] [--claude]`
- `sync [--stage] [--claude]`
- `status [--json]`
- `doctor` (проверка: git, версия, наличие sparse-checkout; полезно агентам)

FR-11. Вывод:
- По умолчанию — человекочитаемый.
- `--json` — строгий JSON (чтобы агент мог парсить без эвристик).
  - Для `suggest`: массив объектов с `id,title,description,tags,paths,score`.
  - Для `catalog`: массив объектов без `score`.
  - Для `status`: `selected_ids`, `manifest_paths`, `submodule_present`, `submodule_dirty`, `git_version`.

FR-12. Источники конфигурации repo URL:
- `SKILLS_REPO_URL` (env) или
- `.codex/skills.config.json` в проекте.
Если не задано — ошибка с подсказкой как исправить.

FR-13. Поведение `install`:
- если submodule отсутствует → добавить `git submodule add -b <branch> ... .codex/skills`
- затем `git submodule update --init --depth 1 -- .codex/skills`
- обновить manifest
- применить sparse-checkout (`git sparse-checkout init --cone`, `set --stdin`)
- при `--stage` сделать `git add` для:
  - `.gitmodules`
  - `.codex/skills` (gitlink)
  - `.codex/skills.manifest`
  - `.codex/skills.config.json` (если создан/изменён)
  - `.claude/skills/*` wrappers (если `--claude`)

FR-14. Ошибки и безопасность:
- Если текущая директория не git-worktree → ошибка.
- Если в submodule есть незакоммиченные изменения и команда меняет sparse-набор → ошибка (или `--force`, v2).
- repo URL берётся только из trusted config/env (не из текста пользователя).

### 6.4 Интеграция с Claude Code (wrapper-экспорт)
FR-15. Для Claude проектные навыки — `.claude/skills/` (коммитится в проект).
FR-16. В v1 реализовать **wrappers**:
- для каждого выбранного skill id создаётся `.claude/skills/<id>/SKILL.md`, который:
  - содержит frontmatter (`name`, `description`),
  - в теле ссылается на canonical инструкции в `.codex/skills/<path>/SKILL.md` и просит Claude следовать им.
- Wrappers генерируются/обновляются командой `skillsctl export-claude` или автоматически при флаге `--claude`.

> Почему wrappers, а не symlink: symlink-поддержка у Codex документирована, но для Claude лучше не полагаться на неявное поведение; wrappers — детерминированнее.

## 7) Скилл “skill-manager” (персональный)
FR-17. Должен существовать user-scoped скилл `skill-manager`, который:
- доступен в любом проекте,
- умеет запускать `skillsctl`,
- следует UX-протоколу из раздела 5.

Расположение:
- Codex: `~/.codex/skills/skill-manager/` (user-scoped).
- Claude: `~/.claude/skills/skill-manager/` (user-scoped).
(См. References.)

## 8) Алгоритм suggest (v1, детерминированный)
Цель: быстро и предсказуемо ранжировать.

Предлагаемый скоринг:
- Exact match по `id` (case-insensitive): +100
- Prefix match по `id`: +40
- Token match (query разбивается на токены по не-алфанум):
  - в `tags`: +20 за токен
  - в `title`: +10
  - в `description`: +5
- Alias match: как `id` (exact +100, prefix +40)

Сортировка:
1) score desc
2) id asc (для стабильности)

## 9) Нефункциональные требования (NFR)
NFR-1. Минимальные зависимости: Python 3 + Git.
NFR-2. Портируемость: macOS/Linux; Windows best-effort (v1).
NFR-3. Быстродействие: `catalog/suggest` на 1k скиллов < 200ms на локальном JSON.
NFR-4. Надёжность: команды идемпотентны; повторный запуск безопасен.
NFR-5. Явная честность: утилита не “угадывает”, если отсутствует конфиг repo URL.

NFR-6. Sparse-checkout помечен как **EXPERIMENTAL** в официальной документации Git; нужно документировать требование по Git версии и иметь понятную ошибку.
(См. References.)

## 10) Acceptance Criteria (DoD)
AC-1. Новый проект (git init) + настроенный `SKILLS_REPO_URL`:
- `skillsctl install pdfs --stage --yes` создаёт:
  - `.gitmodules`
  - `.codex/skills` submodule
  - `.codex/skills.manifest`
  - sparse-набор содержит `catalog/` и `paths` для `pdfs`.

AC-2. `skillsctl suggest "pdf" --json` возвращает список с score и корректными id.
AC-3. `skillsctl remove pdfs` убирает `paths` из sparse-набора и обновляет manifest.
AC-4. `git clone` проекта + `skillsctl sync` восстанавливает рабочее дерево submodule согласно manifest.
AC-5. `--claude` создаёт/обновляет `.claude/skills/<id>/SKILL.md` wrappers.

## 11) План тестирования
### Unit
- Парсинг `catalog/skills.json` (валидный/невалидный)
- Парсинг manifest (комментарии, пустые строки)
- Скоринг (exact/prefix/tags/title/description)

### Integration (обязательно)
- Временный проект в tmp:
  - install одного скилла
  - install второго
  - remove первого
  - set
  - sync после удаления рабочей директории submodule
- Проверка `git status --porcelain` после `--stage`.

## 12) Риски и меры
R1. Sparse-checkout — experimental → возможны изменения поведения.
Мера: фиксировать минимальную версию Git в README, иметь `doctor`, обеспечить понятное сообщение.

R2. Submodule “dirty” (локальные изменения) может мешать обновлению sparse-набора.
Мера: блокировать операции изменяющие набор, если submodule dirty; добавить подсказки/“что делать”.

R3. Безопасность supply-chain (подмена репозитория).
Мера: repo URL только из trusted config/env; опционально allowlist хостов.

## 13) Rollout / внедрение
- Шаг 1: добавить `catalog/skills.json` в skills-repo и привести структуру скиллов к “директория+SKILL.md”.
- Шаг 2: поставить user-scoped `skill-manager` для Codex/Claude.
- Шаг 3: в каждом проекте: `skillsctl install <id>` вместо копирования.
- Шаг 4: (опционально) pre-push hook на проект, который проверяет “нет ли незакоммиченных изменений в .codex/skills”.

---

## References (нормативные источники)
1) OpenAI Codex — Create a skill (paths for user-scoped and repo-scoped skills, .codex/skills and ~/.codex/skills):
   https://developers.openai.com/codex/skills/create-skill/

2) OpenAI Codex — Skills overview (locations & symlink support):
   https://developers.openai.com/codex/skills/

3) Anthropic Claude Code — Skills (frontmatter, disable-model-invocation, project skills in .claude/skills):
   https://code.claude.com/docs/en/skills

4) Git — git sparse-checkout (cone mode, directories, experimental notice, --stdin supported):
   https://git-scm.com/docs/git-sparse-checkout

5) Git — git submodule (add -b <branch>, --depth <depth>):
   https://git-scm.com/docs/git-submodule
