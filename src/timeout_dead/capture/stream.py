"""Captured stream reading and orchestration."""

import threading
import time
from queue import Queue
from typing import TextIO

from timeout_dead.capture.control import hide_cursor, show_cursor, supports_live_preview
from timeout_dead.capture.output import render_final_output
from timeout_dead.capture.preview import clear_live_tail, render_live_tail
from timeout_dead.constants import _Const


# MARK: Readers
# ------------------------------------------------


def _read_captured_stream(
  title: str,
  stream: TextIO,
  output_queue: Queue[tuple[str, str | None]],
) -> None:
  """Read one captured stream and enqueue chunks as they arrive."""

  while True:
    chunk = stream.read(_Const.STREAM_READ_SIZE)

    if not chunk:
      break

    output_queue.put((title, chunk))

  output_queue.put((title, None))


# MARK: Collection
# ------------------------------------------------


def _should_render_live_tail(chunk: str, last_render_time: float) -> bool:
  """Return True when the live preview should be redrawn."""

  if chunk in {_Const.NEWLINE, _Const.CARRIAGE_RETURN}:
    return True

  return time.monotonic() - last_render_time >= _Const.LIVE_RENDER_INTERVAL_S


# ------------------------------------------------


def collect_captured_output(
  output_queue: Queue[tuple[str, str | None]],
  thread_count: int,
  *,
  live_preview: bool,
) -> tuple[str, str]:
  """Collect full captured output and optionally redraw a TTY tail preview."""

  output_by_title = {
    _Const.STDERR_TITLE: "",
    _Const.STDOUT_TITLE: "",
  }
  rendered_lines = _Const.INITIAL_LINE_COUNT
  finished_count = _Const.INITIAL_FINISHED_COUNT
  last_render_time = _Const.INITIAL_RENDER_TIME

  if live_preview:
    hide_cursor()
    rendered_lines = render_live_tail(
      output_by_title[_Const.STDERR_TITLE],
      output_by_title[_Const.STDOUT_TITLE],
      rendered_lines,
    )
    last_render_time = time.monotonic()

  try:
    while finished_count < thread_count:
      title, chunk = output_queue.get()

      if chunk is None:
        finished_count += _Const.COUNT_INCREMENT

        continue

      output_by_title[title] += chunk

      if live_preview and _should_render_live_tail(chunk, last_render_time):
        rendered_lines = render_live_tail(
          output_by_title[_Const.STDERR_TITLE],
          output_by_title[_Const.STDOUT_TITLE],
          rendered_lines,
        )

        last_render_time = time.monotonic()

    return output_by_title[_Const.STDERR_TITLE], output_by_title[_Const.STDOUT_TITLE]

  finally:
    if live_preview:
      clear_live_tail(rendered_lines)
      show_cursor()


# MARK: Public API
# ------------------------------------------------


def stream_captured_output(stdout_stream: TextIO, stderr_stream: TextIO) -> None:
  """Stream captured stderr/stdout tail preview, then print full labeled blocks."""

  output_queue: Queue[tuple[str, str | None]] = Queue()
  threads = [
    threading.Thread(
      target=_read_captured_stream,
      args=(_Const.STDERR_TITLE, stderr_stream, output_queue),
    ),
    threading.Thread(
      target=_read_captured_stream,
      args=(_Const.STDOUT_TITLE, stdout_stream, output_queue),
    ),
  ]

  for thread in threads:
    thread.start()

  stderr_text, stdout_text = collect_captured_output(
    output_queue,
    len(threads),
    live_preview=supports_live_preview(),
  )

  for thread in threads:
    thread.join()

  render_final_output(stderr_text, stdout_text)
