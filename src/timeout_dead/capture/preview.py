"""Live captured output preview rendering."""

import shutil

from timeout_dead.capture.control import write_stdout
from timeout_dead.constants import _Const


# MARK: Text shaping
# ------------------------------------------------


def _last_lines(text: str, count: int = _Const.TAIL_LINE_COUNT) -> str:
  """Return the last *count* logical lines from text."""

  if not text:
    return ""

  lines = text.splitlines()

  if not lines:
    return ""

  tail = _Const.NEWLINE.join(lines[-count:])

  if text.endswith(_Const.NEWLINE):
    return f"{tail}{_Const.NEWLINE}"

  return tail


# ------------------------------------------------


def _terminal_preview_width() -> int:
  """Return a safe line width for live preview text."""

  terminal_width = shutil.get_terminal_size(
    (_Const.DEFAULT_TERMINAL_COLUMNS, _Const.DEFAULT_TERMINAL_LINES)
  ).columns

  return max(_Const.MIN_PREVIEW_WIDTH, terminal_width - _Const.TERMINAL_WIDTH_PADDING)


# ------------------------------------------------


def _truncate_preview_line(line: str, width: int) -> str:
  """Truncate one preview line so it does not wrap in the terminal."""

  if len(line) <= width:
    return line

  if width <= _Const.ELLIPSIS_WIDTH:
    return line[:width]

  return f"{line[: width - _Const.ELLIPSIS_WIDTH]}{_Const.ELLIPSIS}"


# ------------------------------------------------


def _preview_lines(text: str, width: int) -> list[str]:
  """Return exactly TAIL_LINE_COUNT width-limited preview lines."""

  tail = _last_lines(text)

  lines = [] if not tail else [_truncate_preview_line(line, width) for line in tail.splitlines()]

  missing_count = _Const.TAIL_LINE_COUNT - len(lines)

  return [*lines[-_Const.TAIL_LINE_COUNT :], *("" for _ in range(missing_count))]


# MARK: Frame rendering
# ------------------------------------------------


def _format_frame_line(text: str = "") -> str:
  """Format one preview frame line with clear-to-end."""

  return f"{text}{_Const.CLEAR_LINE}"


# ------------------------------------------------


def format_preview_frame(stderr_text: str, stdout_text: str, width: int) -> str:
  """Format one fixed-height live preview frame."""

  lines = [
    _format_frame_line(_Const.STDERR_TITLE),
    _format_frame_line(),
    _format_frame_line(),
    *(_format_frame_line(line) for line in _preview_lines(stderr_text, width)),
    _format_frame_line(),
    _format_frame_line(),
    _format_frame_line(_Const.STDOUT_TITLE),
    _format_frame_line(),
    _format_frame_line(),
    *(_format_frame_line(line) for line in _preview_lines(stdout_text, width)),
    _format_frame_line(),
    _format_frame_line(),
  ]

  return _Const.NEWLINE.join(lines) + _Const.NEWLINE


# ------------------------------------------------


def render_live_tail(stderr_text: str, stdout_text: str, rendered_lines: int) -> int:
  """Redraw captured output tail blocks and return rendered line count."""

  width = _terminal_preview_width()
  frame = format_preview_frame(stderr_text, stdout_text, width)
  prefix = _Const.ANSI_CURSOR_UP.format(line_count=rendered_lines) if rendered_lines else ""

  write_stdout(f"{prefix}{frame}")

  return _Const.PREVIEW_FRAME_LINES


# ------------------------------------------------


def clear_live_tail(rendered_lines: int) -> None:
  """Clear the previously rendered TTY preview."""

  if not rendered_lines:
    return

  blank_frame = "".join(f"{_Const.CLEAR_LINE}{_Const.NEWLINE}" for _ in range(rendered_lines))
  cursor_up = _Const.ANSI_CURSOR_UP.format(line_count=rendered_lines)
  write_stdout(f"{cursor_up}{blank_frame}{cursor_up}")
