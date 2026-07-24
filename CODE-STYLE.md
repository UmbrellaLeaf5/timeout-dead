# CODE-STYLE.md

All code-writing rules for Python projects.

---

## Indentation & Layout

- **2-space indentation** everywhere (Python, JSON, TOML, YAML, Markdown, pyproject.toml, all config files).
- **Line length**: 100 characters.
- **Hanging indentation** for long signatures and calls:

  ```python
  def my_func(
    arg1: str,
    arg2: int,
  ) -> ReturnType:
    ...
  ```

- Formatting and linting are governed by `ruff` (configured via `ruff.toml`). `ruff` is the single source of truth — no `black`, no `isort`, no `flake8`. Run `ruff check . && ruff format --check .` to verify.

- **0 warnings required.** Ruff must return zero errors and zero warnings on every commit. Never suppress or skip a ruff rule without an explicit instruction from the user. No `# noqa`, no `per-file-ignores`, no rule exclusions unless the user explicitly requests it.

## Language Usage

### Type Annotations

- **Every function must have parameter types and a return type annotation** (`-> None` for void).
- **pyright runs in `basic` mode** — all type errors are blockers.

  ```python
  def get_user(user_id: str) -> User:
    ...

  # ------------------------------------------------

  def process(items: list[Item]) -> None:
    ...
  ```

- Use `T | None` instead of `Optional[T]` (Python 3.10+).
- Avoid `Any` — prefer `object`, `type`, or a `Protocol`/`ABC` when the exact type varies.
- Use `pathlib.Path` for all file path arguments and returns, never raw `str`.

  ```python
  from pathlib import Path


  def load_config(path: Path) -> Config:
    ...
  ```

- Use `dataclasses.dataclass` or `pydantic.BaseModel` for structured data.

  ```python
  from dataclasses import dataclass
  from uuid import UUID


  @dataclass
  class Order:
    id: UUID
    user_id: UUID
    total: float
    status: str
  ```

### String Usage

- Use **f-strings** for all string formatting — never `%` or `.format()`.

  ```python
  msg = f"User {user_id} not found in group {group_name}"
  ```

- Use `repr()` or `!r` in f-strings when the exact value matters for debugging.

  ```python
  logger.debug("Raw input: %r", raw_input)
  # or:
  logger.debug(f"Raw input: {raw_input!r}")
  ```

### Context Managers

- Use `with` for all resource management — file handles, network connections, locks.

  ```python
  with path.open("r") as f:
    data = json.load(f)

  with lock:
    shared_state.update(value)
  ```

- For custom resources, implement `__enter__` and `__exit__` or use `contextlib.contextmanager`.

### Control flow & idioms

- Use `for` for all loops. `while` is permitted only when iteration depends on mutable state or complex conditions.

  ```python
  for item in items:
    if item.is_active:
      process(item)
  ```

- Use comprehensions for simple transformations — but avoid nested comprehensions deeper than 2 levels.

  ```python
  # Good — simple comprehension
  active = [item for item in items if item.is_active]

  # Good — two-level is acceptable
  pairs = [(a, b) for a in as_list for b in bs_list]

  # Bad — too deep to read
  result = [x for sub in nested for x in sub.filter() if x.ok]
  ```

- Use generator expressions for lazy iteration over large datasets.

  ```python
  total = sum(item.cost for item in order.items)
  ```

- Prefer `pathlib.Path` over `os.path` for all path operations.

  ```python
  config_dir = Path.home() / ".config" / "myapp"
  config_dir.mkdir(parents=True, exist_ok=True)
  ```

- Use `dataclasses.dataclass` for data containers, `pydantic.BaseModel` for validated configuration.

- **Shebangs**: executable scripts start with `#!/usr/bin/env python3` when the project uses `.venv` or `uv`.

  ```python
  #!/usr/bin/env python3
  ```

- **Programmatic entry**: use `if __name__ == "__main__"` for scripts meant to be both importable and executable.

  ```python
  if __name__ == "__main__":
    main()
  ```

### Enums

- Use `enum.Enum` or `enum.IntEnum` for enumerations instead of string constants.

  ```python
  from enum import Enum


  class OrderStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
  ```

### Frozen Dataclasses

- Use `frozen=True` for dataclasses that should be immutable.

  ```python
  @dataclass(frozen=True)
  class Config:
    timeout_s: int
    retry_count: int
  ```

### Protocol (Structural Subtyping)

- Use `typing.Protocol` for structural interfaces (duck typing).

  ```python
  from typing import Protocol


  class Processor(Protocol):
    def process(self, data: str) -> str: ...
  ```

### Logging

- Use the `logging` module, never `print()` in production code.
- Configure levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- Prefer structured logging with `%`-style formatting.

  ```python
  import logging

  logger = logging.getLogger(__name__)

  logger.info("Processing item: %s", item_id)
  logger.debug("Raw input: %r", raw_data)
  ```

## Imports

- **Ordering**: stdlib → third‑party → project (local). Ruff's `I` rule handles this.
- After editing imports, run `ruff check --fix .` to sort them.
- Never use `from module import *` in production code (exception: `__init__.py` re-exports guided by `__all__`).
- Avoid circular imports — restructure code if you find one. Use lazy imports (`import foo` inside a function) only as a last resort.

```python
# stdlib
import os
from pathlib import Path
from typing import TypeVar

# third-party
import typer
from pydantic import BaseModel

# local
from myproject.core import UserService
from myproject.config import settings
```

### Exports

- In `__init__.py` files, declare the public API with `__all__`. Ruff respects `__all__`, so you don't need `import X as X` or `# noqa` comments.

```python
# myproject/core/__init__.py
__all__ = ["UserService", "OrderService", "User", "Order"]
```

## Naming Conventions

- **Functions, variables, methods, fields** → `snake_case` (e.g. `get_user()`, `total_count`, `action_logger`)
- **Classes, dataclasses, exceptions** → `PascalCase` (e.g. `UserService`, `OrderResponse`, `NotFoundException`)
- **Constants** → `SCREAMING_SNAKE_CASE` (e.g. `MAX_RETRIES`, `DEFAULT_TIMEOUT_S`)
- **Private / internal** → `_` prefix for module-internal functions, variables, and methods (e.g. `_cache`, `_build_response()`, `_InternalType`)
- **Type variables** → `PascalCase` with `T` prefix when generic (e.g. `T`, `TItem`, `TResponse`)
- **JSON keys** → `camelCase` or `snake_case` depending on API conventions. Be consistent within a project.

- Prefer specific, descriptive names. Avoid ambiguous abbreviations:
  - `resolved_api_key` rather than `key` when multiple keys exist.
  - `user_preferences` not `prefs`.

## Blank Lines

- Use blank lines to separate logical sections of code. Avoid excessive blank lines that create visual noise.

- **2 blank lines** between top-level definitions (functions, classes).
- **2 blank lines** after the last import.
- **1 blank line** between class methods.

- **Important:** Blank line rules may overlap. When multiple rules require a blank line at the same position, use exactly **one blank line**. Never use two or more consecutive blank lines.

  Blank line **needed** — when switching between different variables / logical groups:

  ```python
  selected_item.status = ItemStatus.BUSY
  selected_item.updated_at = clock.now()
  _repository.save(selected_item)

  order.assigned_item_id = selected_item_id
  order.status = OrderStatus.PENDING
  order.is_locked = False
  ```

  Blank line **not needed** — sequential calls on the same object or related group:

  ```python
  order.start_lat = motion.start_lat
  order.start_lon = motion.start_lon
  order.start_height = motion.start_height
  order.direction_lat = motion.direction_lat
  order.direction_lon = motion.direction_lon
  ```

- Between peer-level definitions (top-level functions, member methods), use one of the following:
  - A separator line (`# ------------------------------------------------`) alone — for trivial methods or private helpers
  - A MARK comment with a separator line — for important methods
  - A MARK comment for a group, with separator lines between methods within the group

  No naked blank lines between peer-level definitions — always use a separator or MARK.

  ```python
  def compute_full(request: CalculationRequest) -> CalculationPlan | None:
    ...

  # ------------------------------------------------

  def _compute_new_plan(
    request: CalculationRequest,
    max_radius: float,
  ) -> CalculationPlan | None:
    ...

  # MARK: Time-to-interaction calculation
  # ------------------------------------------------

  def _calculate_interaction_time(
    item: ItemState,
    target: TargetState,
    max_radius: float,
  ) -> float | None:
    ...
  ```

  After a closing `# ------------------------------------------------` or `# MARK:` section header — a blank line before the next statement.

  ```python
  # MARK: Private Helpers
  # ------------------------------------------------

  def _build_response(input: Any) -> Response:
    ...
  ```

- **1 blank line** after class header between `__init__` parameters and the first method.

  ```python
  @dataclass
  class CalculationService(
    # repositories:
    item_repository: ItemRepository,
    result_repository: ResultRepository,

    # services:
    state_service: StateService,
    persistence_service: PersistenceService,
  ):

    # MARK: calculateAndPersist
    # ------------------------------------------------

    def calculate_and_persist(
      entity: OrderEntity,
      item: ItemEntity | None,
      time: datetime,
    ) -> CalculationState:
      ...
  ```

  **Note:** The blank line after the class header is the required 1 blank line. The MARK comment follows immediately after it. These blank lines between `__init__`/class param groups are mandatory. When blank line rules overlap, use only one blank line.

- **Blank line before control flow** — insert a blank line before every `if`, `elif`, `else`, `for`, `while`, `try`, `except`, `finally`, `with`, `raise`, `assert`, `return`, `continue` that sits at the same indentation level as its containing block.

  ```python
  result = compute()

  if result is None:
    return

  for item in items:
    process(item)
  ```

- Deeply nested one‑liners may omit the extra blank line before control flow:

  ```python
  for item in items:
    if item.is_active:
      process(item)
  ```

- **Before `return`** in a multi-line function — a blank line, except when `return` is in a one-line block, or when it is the only statement in a block.

  ```python
  distance = compute_distance(a, b)

  return distance <= max_radius
  ```

- **After docstrings** — always put a blank line after a function or class docstring before the first statement.

  ```python
  def my_func(arg: str) -> int:
    """Process the argument."""

    value = int(arg)

    return value
  ```

- Inside functions, a blank line is required both **before and after** variable declarations, unless they belong to the same logical group.

  Between `var = Type()` and `var.init(...)` on the next line — **no** blank line because they are one logical group:

  ```python
  processor = DataProcessor()
  processor.init(config)

  handler.receive(processor)
  ```

  Two consecutive variable declarations in a row are also valid without a blank line between them:

  ```python
  radius = input.radius
  status = OrderStatus.of(input.status) if input.status else None
  ```

- Within a class (body fields), blank lines between consecutive fields are **not** needed. A blank line is required only when introducing a new logical group preceded by a comment or annotation.

- When initializing an object field by field — a blank line between declaration and the first assignment (separates declaration from multi-field population). The criterion is that the variable is subsequently used in several independent lines that form a logical block. This differs from the init case where `obj = Type()` and `obj.init(...)` are one inseparable group — there, no blank line is needed because the lines are not separable by meaning.

  ```python
  entity = OrderEntity()

  entity.start_lat = input.lat
  entity.start_lon = input.lon
  entity.speed = input.speed
  ```

- **Between conditional branches** (`if`/`elif`/`else`) — insert a blank line at the start of each new branch when the branch body is multi-line.

  ```python
  if status == OrderStatus.COMPLETED:
    log.info("Order %s completed", order_id)
    return build_terminal_state(input)

  elif status == OrderStatus.IMPOSSIBLE:
    log.warn("Order %s impossible", order_id)
    return build_terminal_state(input)

  else:
    log.debug("Order %s active", order_id)
    return build_active_state(input)
  ```

- **Before `except`/`finally`** — a blank line after the preceding `try` block.

  ```python
  try:
    processor.load_state()

  except Exception:
    logger.warn("Failed to load state, starting fresh")
  ```

- **After a long wrapped line** — a blank line before the next statement.

  ```python
  raise ConflictError(
    "Order " + order_id + " has no persisted state"
  )

  compute_next_state(input)
  ```

## Comments

### MARK comments & section separators

- Use MARK comments and separator lines to organise code into logical groups. Every non-trivial function is preceded by a MARK comment, and all functions are separated by section separator lines.

- **Separator line is exactly 50 characters**: `# ` followed by 48 dashes (`# ------------------------------------------------`). Never use shorter or longer separators — always exactly 50 characters total.

- **Public methods** — Every non-trivial public method must be preceded by a `# MARK:` comment. The comment describes the method's purpose.
  - **Trivial methods** (single expression, one-liner) — a separator line alone is sufficient:

    ```python
    # ------------------------------------------------

    def get_user(user_id: str) -> User:
      return _repository.find_by_id(user_id)
    ```

  - **Non-trivial methods** — require a full MARK comment:

    ```python
    # MARK: calculateAndPersist
    # ------------------------------------------------

    def calculate_and_persist(
      entity: OrderEntity,
      item: ItemEntity | None,
      time: datetime,
    ) -> CalculationState:
      ...
    ```

  - **For endpoint methods** in web applications, the HTTP path may be used:

    ```python
    # MARK: POST /api/order/calculate
    # ------------------------------------------------

    def calculate(order_id: str) -> OrderResponse:
      ...
    ```

  - **Groups of related functions** — a single MARK comment may mark the start of a group instead of annotating each method individually. Use judgement based on context. Between methods within the group, use a separator line:

    ```python
    # MARK: Calculation helpers
    # ------------------------------------------------

    def calculate_time(...) -> float:
      ...

    # ------------------------------------------------

    def calculate_point(...) -> Point:
      ...

    # ------------------------------------------------

    def validate_calculation(...) -> None:
      ...
    ```

- All private helpers must be grouped under a `# MARK: Private Helpers` section marker. Within this section:
  - Most private methods use a separator line (`# ------------------------------------------------`) between them.
  - Important private methods (complex algorithm, critical business logic) may get their own `# MARK:` comment.

  ```python
  # MARK: Private Helpers
  # ------------------------------------------------

  def _build_response(...) -> Response:
    ...

  # ------------------------------------------------

  def _validate_input(...) -> None:
    ...

  # MARK: Complex calculation algorithm
  # ------------------------------------------------

  def _calculate_matrix(...) -> Matrix:
    ...
  ```

- After a closing `# ------------------------------------------------` or `# MARK:` section header — a blank line before the next statement.

  ```python
  # MARK: Private Helpers
  # ------------------------------------------------

  def _build_response(...) -> Response:
    ...
  ```

- After `# MARK:` the text must start with a **capital letter** or be in **ALL CAPS**:
  - `# MARK: POST /api/order/calculate`
  - `# MARK: Private Helpers`
  - `# MARK: Time-to-interaction calculation`

### Docstrings

- Every non-trivial public function must have a multi-line docstring placed immediately before the function body, after the MARK/separator:

  ```python
  # MARK: calculateAndPersist
  # ------------------------------------------------

  def calculate_and_persist(
    entity: OrderEntity,
    item: ItemEntity | None,
    time: datetime,
  ) -> CalculationState:
    """
    Вычисляет и сохраняет состояние для заданной сущности.

    Args:
      entity (OrderEntity): сущность для расчёта
      item (ItemEntity | None): связанный объект или None, если не назначен
      time (datetime): момент времени, на который вычисляется состояние

    Returns:
      CalculationState: результирующее состояние
    """
    ...
  ```

  The docstring block is separated from the MARK/separator by one blank line (the docstring indentation already provides it) and sits directly above the function body with no blank line between docstring closing `"""` and the first statement — if a blank line is needed, place it _after_ the docstring, before the first line of code.

- **Trivial / self-documenting functions** may omit the docstring when:
  - The name fully describes the purpose.
  - The function is a single line.
  - The function is private (`_` prefix).

### Language of comments

- **Docstring labels** (`Args:`, `Returns:`, `Raises:`) — **exclusively in English** (standard Google style).
- **Docstring descriptions** — **Russian preferred**. The summary, param descriptions, and return descriptions should be written in Russian.
- **`# MARK:` comments** — **exclusively in English**.
- **Regular `#` comments** — either English or Russian is acceptable, but **Russian is preferred**. Historic English comments may remain, but new or modified comments should use Russian.
- **Console output (print, logging)** — English (ASCII only).

### Inline comments

- Inline comments use `# ` (space after hash).
- Every data class property must have a short side comment explaining meaning and units where not obvious from naming. Self-explanatory fields (e.g. `user_id`, `item_id`) don't need a comment.

  ```python
  @dataclass
  class FilterConfig:
    id: UUID
    df_hz: float = 0.0  # offset from center, Hz
    a_db: float = 0.0   # relative attenuation, dB
  ```

- Constructor parameters must be grouped with category comments:

  ```python
  class UserService:
    def __init__(
      self,

      # repositories:
      user_repository: UserRepository,

      # mappers:
      user_mapper: UserMapper,

      # services:
      notification_service: NotificationService,
    ) -> None:
      ...
  ```

## Constants

- **No magic values anywhere in code.** This applies to **all** literal types: string literals (`"user"`, `"/config/path"`), numeric constants (`3.14`, `86400`, `4096`), and any other hardcoded value that carries domain meaning. Every shared value must be defined in exactly one central location.

- **The only permissible inline literals** are:
  - Unit conversion factors (`1e6`, `1e-3`, `1000`) — values that only translate between measurement units, never domain logic
  - Precision/sentinel constants (`1e-9`, `-1`) — values that define computational precision or "no value" markers
  - Trivial initialisers (`0`, `1`, `""`) — when semantically obvious and not carrying domain meaning

- All shared strings, magic numbers, regex patterns, and default values live in `constants.py`. Use nested classes to group related values.

- Organize into nested classes: `Math`, `Entity`, `Validation`, `Pattern`.

- Reference constants via `Constants.Class.FIELD` — never inline magic values.

```python
# myproject/constants.py
from math import pi

class Math:
  EARTH_RADIUS_M: float = 6_371_000.0
  DEG_TO_RAD: float = pi / 180.0

# ------------------------------------------------

class Entity:
  USER = "User"
  ORDER = "Order"
  PRODUCT = "Product"

# ------------------------------------------------

class Validation:
  INVALID_EMAIL = "Invalid email format"
  REQUIRED_FIELD = "Required field is missing"

# ------------------------------------------------

class Pattern:
  UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
```

Usage:

```python
from myproject.constants import Math, Entity


earth_r = Math.EARTH_RADIUS_M
entity_user = Entity.USER
```

## Testing

- Use `pytest` as the test framework. Test files are named `test_<module>.py`.
- **Fixtures** — prefer `conftest.py` for shared fixtures. One fixture, one responsibility.
- **Parametrize** — use `@pytest.mark.parametrize` to test multiple inputs without code duplication.
- **Mocking** — use `pytest.MonkeyPatch` for module-level mocks, `unittest.mock` for instance-level mocks.
- **Skipping** — mark tests with `@pytest.mark.skip` or `@pytest.mark.skipif` for environment-specific tests.

```python
import os
import pytest
from uuid import uuid4


@pytest.fixture
def sample_user() -> User:
  return User(id=uuid4(), fullname="Test User", email="test@example.com")

# ------------------------------------------------

@pytest.mark.parametrize("name,valid", [
  ("Alice", True),
  ("", False),
])
def test_validate_name(name: str, valid: bool):
  assert User.is_valid_name(name) == valid

# ------------------------------------------------

@pytest.mark.skipif(not os.getenv("CI"), reason="Requires external service")
def test_external_api():
  ...
```
