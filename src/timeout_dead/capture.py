"""Captured output rendering helpers."""

import ctypes
import shutil
import sys
import threading
import time
from queue import Queue
from typing import TextIO

from timeout_dead.constants import _Const


# MARK: Constants
# ------------------------------------------------


TAIL_LINE_COUNT = 5
LIVE_RENDER_INTERVAL_S = 0.05
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


# MARK: Helpers
# ------------------------------------------------


def _write_stdout(text: str) -> None:
  """Write text directly to stdout and flush immediately."""

  sys.stdout.write(text)
  sys.stdout.flush()


# ------------------------------------------------


def _hide_cursor() -> None:
  """Hide the terminal cursor during live preview redraws."""

  _write_stdout(HIDE_CURSOR)


# ------------------------------------------------


def _show_cursor() -> None:
  """Restore the terminal cursor after live preview redraws."""

  _write_stdout(SHOW_CURSOR)


# ------------------------------------------------


def _read_captured_stream(
  title: str,
  stream: TextIO,
  output_queue: Queue[tuple[str, str | None]],
) -> None:
  """Read one captured stream and enqueue chunks as they arrive."""

  while True:
    chunk = stream.read(1)

    if not chunk:
      break

    output_queue.put((title, chunk))

  output_queue.put((title, None))


# ------------------------------------------------


def _last_lines(text: str, count: int = TAIL_LINE_COUNT) -> str:
  """Return the last *count* logical lines from text."""

  if not text:
    return ""

  lines = text.splitlines()

  if not lines:
    return ""

  tail = "\n".join(lines[-count:])

  if text.endswith("\n"):
    return f"{tail}\n"

  return tail


# ------------------------------------------------


def _terminal_preview_width() -> int:
  """Return a safe line width for live preview text."""

  terminal_width = shutil.get_terminal_size((80, 24)).columns

  return max(20, terminal_width - 1)


# ------------------------------------------------


def _truncate_preview_line(line: str, width: int) -> str:
  """Truncate one preview line so it does not wrap in the terminal."""

  if len(line) <= width:
    return line

  if width <= 3:
    return line[:width]

  return f"{line[: width - 3]}..."


# ------------------------------------------------


def _format_preview_text(text: str, width: int) -> str:
  """Format tail preview text with width-limited lines."""

  tail = _last_lines(text)

  if not tail:
    return ""

  lines = tail.splitlines()
  preview = "\n".join(_truncate_preview_line(line, width) for line in lines)

  if tail.endswith("\n"):
    return f"{preview}\n"

  return preview


# ------------------------------------------------


def _format_preview_block(title: str, text: str, width: int) -> str:
  """Format one live preview block with stable spacing."""

  preview = _format_preview_text(text, width)
  block = f"{title}\n\n"

  if preview:
    block += preview

    if not preview.endswith("\n"):
      block += "\n"

    block += "\n"

  return block


# ------------------------------------------------


def _enable_windows_virtual_terminal() -> bool:
  """Enable ANSI cursor control for a real Windows console."""

  if not _Const.IS_WINDOWS:
    return True

  try:
    import msvcrt  # noqa: PLC0415  — Windows-only, imported lazily

    handle = msvcrt.get_osfhandle(sys.stdout.fileno())
    mode = ctypes.c_uint32()
    get_console_mode = getattr(_Const.KERNEL32, "GetConsoleMode", None)
    set_console_mode = getattr(_Const.KERNEL32, "SetConsoleMode", None)

    if get_console_mode is None or set_console_mode is None:
      return True

    if not get_console_mode(handle, ctypes.byref(mode)):
      return True

    next_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return bool(set_console_mode(handle, next_mode))

  except (OSError, ValueError, ImportError):
    return True


# ------------------------------------------------


def _supports_live_preview() -> bool:
  """Return True when stdout can handle ANSI redraw safely."""

  return sys.stdout.isatty() and _enable_windows_virtual_terminal()


# ------------------------------------------------


def _should_render_live_tail(chunk: str, last_render_time: float) -> bool:
  """Return True when the live preview should be redrawn."""

  if chunk in {"\n", "\r"}:
    return True

  return time.monotonic() - last_render_time >= LIVE_RENDER_INTERVAL_S


# ------------------------------------------------


def _format_output_block(title: str, text: str) -> str:
  """Format one final captured output block."""

  block = f"{title}\n\n"

  if not text:
    return block

  block += text

  if text.endswith("\n"):
    return f"{block}\n"

  return f"{block}\n\n"


# ------------------------------------------------


def _render_final_output(stderr_text: str, stdout_text: str) -> None:
  """Print full captured stderr/stdout blocks."""

  _write_stdout(_format_output_block("Err:", stderr_text))
  _write_stdout(_format_output_block("Out:", stdout_text))


# ------------------------------------------------


def _render_live_tail(stderr_text: str, stdout_text: str, rendered_lines: int) -> int:
  """Redraw captured output tail blocks and return rendered line count."""

  if rendered_lines:
    _write_stdout(f"\x1b[{rendered_lines}F\x1b[J")

  width = _terminal_preview_width()
  rendered = _format_preview_block("Err:", stderr_text, width)
  rendered += _format_preview_block("Out:", stdout_text, width)
  _write_stdout(rendered)

  return rendered.count("\n")


# ------------------------------------------------


def _clear_live_tail(rendered_lines: int) -> None:
  """Clear the previously rendered TTY preview."""

  if rendered_lines:
    _write_stdout(f"\x1b[{rendered_lines}F\x1b[J")


# ------------------------------------------------


def _collect_captured_output(
  output_queue: Queue[tuple[str, str | None]],
  thread_count: int,
  *,
  live_preview: bool,
) -> tuple[str, str]:
  """Collect full captured output and optionally redraw a TTY tail preview."""

  stderr_text = ""
  stdout_text = ""
  rendered_lines = 0
  finished_count = 0
  last_render_time = 0.0

  if live_preview:
    _hide_cursor()
    rendered_lines = _render_live_tail(stderr_text, stdout_text, rendered_lines)
    last_render_time = time.monotonic()

  try:
    while finished_count < thread_count:
      title, chunk = output_queue.get()

      if chunk is None:
        finished_count += 1

        continue

      if title == "Err:":
        stderr_text += chunk

      else:
        stdout_text += chunk

      if live_preview and _should_render_live_tail(chunk, last_render_time):
        rendered_lines = _render_live_tail(stderr_text, stdout_text, rendered_lines)
        last_render_time = time.monotonic()

    return stderr_text, stdout_text

  finally:
    if live_preview:
      _clear_live_tail(rendered_lines)
      _show_cursor()


# MARK: Public API
# ------------------------------------------------


def stream_captured_output(stdout_stream: TextIO, stderr_stream: TextIO) -> None:
  """Stream captured stderr/stdout tail preview, then print full labeled blocks."""

  output_queue: Queue[tuple[str, str | None]] = Queue()
  threads = [
    threading.Thread(
      target=_read_captured_stream,
      args=("Err:", stderr_stream, output_queue),
    ),
    threading.Thread(
      target=_read_captured_stream,
      args=("Out:", stdout_stream, output_queue),
    ),
  ]

  for thread in threads:
    thread.start()

  stderr_text, stdout_text = _collect_captured_output(
    output_queue,
    len(threads),
    live_preview=_supports_live_preview(),
  )

  for thread in threads:
    thread.join()

  _render_final_output(stderr_text, stdout_text)
