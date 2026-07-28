# AGENTS.md

## Project & Profile

`timeout-dead` — lightweight command timeout utility with zero external dependencies. Runs any shell command with a configurable timeout and signal, terminating the process if it exceeds the limit. Works on Unix (Linux/macOS) and Windows (with Git Bash or WSL).

### Code style

You MUST strictly follow the project's coding standards, naming conventions, and language-specific rules.

Before generating, refactoring, or modifying any code, you are REQUIRED to read and apply the guidelines defined in the external style guide:

- **File Path:** [`./CODE-STYLE.md`](./CODE-STYLE.md)

_Instruction for Agent:_ If you haven't read `./CODE-STYLE.md` in the current session, use your file-reading tool to fetch its content before writing any code. Do not hallucinate styles.

## Operational Rules & Critical Restrictions

**UNDER NO CIRCUMSTANCES may you commit, push, amend, rebase, or modify the git history without an EXPLICIT instruction to do so.** This is the most important rule in this document. Violating it may result in lost work and broken branches.

This specifically includes:

- `git commit` / `git commit --amend` / `git commit -m "..."`
- `git push` / `git push --force` / `git push --force-with-lease`
- `git add` (stage for commit — prefer working-tree-only edits)
- `git rebase` / `git reset` / `git checkout` (to modify branches)
- Any other command that creates or alters commits

**NEVER commit while Git is in detached `HEAD` state.** Before any commit, verify that the repository is on the intended working branch (for example with `git branch --show-current` or `git status`). If the current branch is empty, ambiguous, or not clearly the user's active working branch, stop and ask the user which branch to use before committing.

If the user asks "what should the commit message be?" — **suggest a message but do NOT commit**. Wait for an explicit directive such as:

- "commit"
- "commit and push"
- "stage and commit"

**If the user says "update AGENTS.md" or similar — this is NOT a commit instruction. Do NOT add or commit files unless told to.**

## Workflow & Verification Commands

### Setup

```bash
uv tool install timeout-dead
```

If already installed — verify it works:

```bash
time-d --version
```

### Time limit (HARD REQUIREMENT)

**Every non-interactive bash command MUST complete within 60 seconds.** All non-interactive commands must be invoked through the timeout wrapper with captured output:

```bash
time-d -c "<your command>"
```

Use `time-d -c` by default for every non-interactive command. Use plain `time-d` without `-c` only for genuinely interactive commands that require a TTY, such as `vim`, `python -i`, REPLs, or terminal UI tools.

For commands that are expected to legitimately take longer than 60 seconds (full builds, full test suites, dependency syncs, large format/lint runs), use an explicit timeout:

```bash
time-d -c --sec <seconds> "<your command>"
```

Choose the smallest reasonable timeout for the command. Do not use a longer timeout to hide a hung process.

Long-running daemons must use `nohup ... >/dev/null 2>&1 &` so the wrapper returns immediately.

### Install dependencies

```bash
time-d -c --sec 300 "uv sync"
```

### Verify after changes

Run **all** checks in this order — treat errors as blockers:

```bash
time-d -c "ruff check ."
time-d -c "ruff format --check ."
time-d -c "pyright ."
time-d -c --sec 300 "python -m pytest tests/ -v"
```

### Fix formatting & imports

```bash
time-d -c "ruff check --fix . && ruff format ."
```

**LSP is mandatory.** Configure `pyright-langserver` and `ruff server` in your editor. After every change, confirm lint, format, and type-check show **0 errors**. `ruff format` is the single source of truth for formatting — no `black`, no `isort`.

### Run a single test

```bash
time-d -c "python -m pytest tests/test_file.py::test_name -v"
```

### Mandatory testing

**Every change must be verified by running the test suite.** No exceptions. If any test fails, fix the issue before considering the change complete.

## Software Architecture & Design Patterns

### Documentation

- **Standalone Markdown documentation pages** → `SCREAMING_SNAKE_CASE` names (e.g., `CONFIG.md`, `ARCHITECTURE.md`, `CODE-STYLE.md`). Keep conventional repository files such as `README.md` unchanged unless explicitly requested.

### Package Layout

- Source code lives under `src/<project_name>/` (or directly in `<project_name>/` depending on preference). Choose one convention and stick to it.
- Separate packages by concern — do not dump all classes in a single flat directory.
- Example layout for a typical project:

```
src/myproject/
  __init__.py           ← exports public API via __all__
  core/                 ← domain logic, entities, services
  cli/                  ← CLI entry points (typer/click)
  api/                  ← HTTP API layer (if applicable)
  config/               ← configuration models (pydantic/dataclass)
  constants.py          ← shared constants
  utils/                ← shared utility functions
```

- **Never create a `model.py` dumping ground.** Split types into explicit purpose modules (e.g., `entities.py`, `dto.py`, `enums.py`).

### Separation of Concerns

- **Core logic** lives in `core/` and has zero dependencies on CLI, HTTP, or file I/O. Pure domain logic only.
- **CLI layer** delegates to core services — never contains business logic.
- **Configuration** uses `pydantic.BaseModel` or `dataclasses.dataclass` for typed, validated settings loaded from environment, config files, or CLI arguments.

### Dependency Management

- Use **`uv`** for dependency management (recommended). Alternatives: `pip` with `requirements.txt`.
- **Never edit `uv.lock` manually.** It is regenerated by `uv lock` or `uv sync` when dependencies change.
- Dependencies are declared in `pyproject.toml`.

### CLI Design

- Use `typer` or `click` for CLI tools. For web APIs, use `fastapi` or `flask`.
- Each command groups related operations — use subcommands for modularity.
- CLI entry points handle argument parsing, then delegate to core services.
- For CLI testing, use the appropriate test harness (e.g., `CliRunner`) and verify that output is captured correctly.

```python
# src/myproject/cli/main.py
import typer


app = typer.Typer()

# --------------------------------------------------

@app.command()
def process(file: str):
  """Process a file."""
  result = service.process(file)
  print(result)
```

### Exceptions

- Define a custom exception hierarchy rooted in a `BaseError` (or use a library like `pydantic_core` for validation errors).
- For HTTP APIs: return structured error responses, never let bare tracebacks leak to clients.
- CLI entry points catch exceptions, log the error, and return a non-zero exit code.

```python
class BaseError(Exception):
  """Base exception for application errors."""

# --------------------------------------------------

class NotFoundError(BaseError):
  """Resource not found."""

# --------------------------------------------------

class ConflictError(BaseError):
  """Resource conflict."""
```

## Testing Strategy

- Use `pytest` as the test framework. See [`./CODE-STYLE.md`](./CODE-STYLE.md) for style rules (fixtures, parametrize, mocking, skipping, naming).

### Unit Tests

- Tests live in `tests/` mirroring the source structure.
- Run unit tests: `time-d -c --sec 300 "pytest tests/ -v --ignore=tests/integration"`.

### Integration Tests

- Place integration tests in `tests/integration/`. Use `@pytest.mark.integration` marker.
- Run integration tests: `time-d -c --sec 300 "pytest tests/integration/ -v -m \"integration\""`.
- Run unit tests only: `time-d -c --sec 300 "pytest tests/ -v -m \"not integration\""`.

### Coverage

- Aim for high coverage of core business logic. Use `pytest-cov` to measure:
  ```bash
  time-d -c --sec 300 "pytest tests/ --cov=src/timeout_dead --cov-report=term-missing"
  ```

## Environment & Configuration

- Use `pydantic.BaseModel` or `dataclasses.dataclass` for typed configuration classes. Use `pydantic-settings` to load `.env` into typed models.
- Load settings from environment variables (`.env`) — never hardcode environment-specific values.
- Absolute paths are forbidden in code under all circumstances. Never hardcode machine-specific paths such as `/home/user/project`, `C:\\Users\\user\\project`, or `/tmp/data.csv` in source code, tests, notebooks, configs generated by code, or examples intended to be copied into code. Build paths from relative paths, `Path.cwd()`, environment variables, CLI arguments, or configuration values instead. Absolute paths are allowed only in console commands or shell snippets that a user runs manually.
- `.env.example` is a **committed template** — never use it directly in scripts or at runtime. It exists solely as documentation for developers.
- `.env` is the **actual runtime file** (git-ignored). Developers copy `.env.example` to `.env` and fill in their local values.

```python
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
  url: str
  pool_size: int = 10

# --------------------------------------------------

class AppConfig(BaseModel):
  db: DatabaseConfig
  log_level: str = "INFO"
```
