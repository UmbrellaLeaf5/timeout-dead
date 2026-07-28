"""Captured output rendering helpers."""

import sys
import threading
from queue import Queue
from typing import TextIO


# MARK: Helpers
# ------------------------------------------------


def _write_stdout(text: str) -> None:
  """Write text directly to stdout and flush immediately."""

  sys.stdout.write(text)
  sys.stdout.flush()


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


def _finish_stream_block(has_output: bool, last_char: str | None) -> None:
  """End a streamed block with exactly one blank line after content."""

  if not has_output:
    return

  if last_char == "\n":
    _write_stdout("\n")

  else:
    _write_stdout("\n\n")


# ------------------------------------------------


def _stream_captured_output_plain(
  output_queue: Queue[tuple[str, str | None]],
  thread_count: int,
) -> None:
  """Stream captured output sequentially for non-TTY stdout."""

  current_title = "Err:"
  current_has_output = False
  current_last_char: str | None = None
  finished_count = 0
  out_title_printed = False

  _write_stdout("Err:\n\n")

  while finished_count < thread_count:
    title, chunk = output_queue.get()

    if chunk is None:
      finished_count += 1

      continue

    if title != current_title:
      _finish_stream_block(current_has_output, current_last_char)
      _write_stdout(f"{title}\n\n")
      current_title = title
      current_has_output = False
      current_last_char = None

      if title == "Out:":
        out_title_printed = True

    _write_stdout(chunk)
    current_has_output = True
    current_last_char = chunk[-1]

  _finish_stream_block(current_has_output, current_last_char)

  if not out_title_printed:
    _write_stdout("Out:\n\n")


# ------------------------------------------------


def _live_render_captured_output(stderr_text: str, stdout_text: str, rendered_lines: int) -> int:
  """Redraw captured output blocks and return rendered line count."""

  if rendered_lines:
    _write_stdout(f"\x1b[{rendered_lines}F\x1b[J")

  rendered = f"Err:\n\n{stderr_text}\nOut:\n\n{stdout_text}"
  _write_stdout(rendered)

  return rendered.count("\n") + 1


# ------------------------------------------------


def _stream_captured_output_live(
  output_queue: Queue[tuple[str, str | None]],
  thread_count: int,
) -> None:
  """Stream captured output by redrawing Err/Out blocks on a TTY."""

  stderr_text = ""
  stdout_text = ""
  rendered_lines = 0
  finished_count = 0

  rendered_lines = _live_render_captured_output(stderr_text, stdout_text, rendered_lines)

  while finished_count < thread_count:
    title, chunk = output_queue.get()

    if chunk is None:
      finished_count += 1

      continue

    if title == "Err:":
      stderr_text += chunk

    else:
      stdout_text += chunk

    rendered_lines = _live_render_captured_output(stderr_text, stdout_text, rendered_lines)

  _write_stdout("\n")


# MARK: Public API
# ------------------------------------------------


def stream_captured_output(stdout_stream: TextIO, stderr_stream: TextIO) -> None:
  """Stream captured stderr/stdout to stdout with labels."""

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

  if sys.stdout.isatty():
    _stream_captured_output_live(output_queue, len(threads))

  else:
    _stream_captured_output_plain(output_queue, len(threads))

  for thread in threads:
    thread.join()
