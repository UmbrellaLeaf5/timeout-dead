"""Example script that writes varied interleaved stdout and stderr output."""

import sys
import threading
import time
from typing import TextIO


# MARK: Constants
# ------------------------------------------------


LINE_DELAY_S = 0.08
CHAR_DELAY_S = 0.006
THREAD_CHAR_DELAY_S = 0.004


# MARK: Helpers
# ------------------------------------------------


def _write_line(stream: TextIO, text: str) -> None:
  """Write one line to the given stream and flush it immediately."""

  stream.write(f"{text}\n")
  stream.flush()


# ------------------------------------------------


def _write_section(title: str) -> None:
  """Write a visible section marker to stderr."""

  _write_line(sys.stderr, "")
  _write_line(sys.stderr, f"EXAMPLE: {title}")
  _write_line(sys.stderr, "EXAMPLE: " + "-" * 56)


# ------------------------------------------------


def _write_lines(stream: TextIO, prefix: str, count: int, delay: float) -> None:
  """Write numbered lines with a fixed delay between them."""

  for index in range(1, count + 1):
    _write_line(stream, f"{prefix}: line {index:02d} after {delay:.3f}s delay")
    time.sleep(delay)


# ------------------------------------------------


def _write_with_delay(stream: TextIO, text: str, delay: float) -> None:
  """Write text character-by-character with a small delay."""

  for char in text:
    stream.write(char)
    stream.flush()
    time.sleep(delay)

  _write_line(stream, "")


# ------------------------------------------------


def _thread_writer(stream: TextIO, prefix: str, words: list[str], delay: float) -> None:
  """Write words from a background thread."""

  for index, word in enumerate(words, start=1):
    _write_with_delay(stream, f"{prefix}: threaded chunk {index:02d} -> {word}", delay)
    time.sleep(0.025)


# MARK: Demo Sections
# ------------------------------------------------


def _run_sequential_section() -> None:
  """Write alternating complete lines to stdout and stderr."""

  _write_section("sequential stdout/stderr lines")

  for index in range(1, 7):
    _write_line(sys.stdout, f"STDOUT: sequential message {index:02d}")
    time.sleep(LINE_DELAY_S)
    _write_line(sys.stderr, f"STDERR: sequential message {index:02d}")
    time.sleep(LINE_DELAY_S)


# ------------------------------------------------


def _run_burst_section() -> None:
  """Write short line bursts to both streams."""

  _write_section("short line bursts")
  _write_lines(sys.stdout, "STDOUT: burst A", 5, 0.035)
  _write_lines(sys.stderr, "STDERR: burst B", 5, 0.035)
  _write_lines(sys.stdout, "STDOUT: burst C", 5, 0.035)
  _write_lines(sys.stderr, "STDERR: burst D", 5, 0.035)


# ------------------------------------------------


def _run_slow_character_section() -> None:
  """Write longer messages one character at a time."""

  _write_section("slow character output")
  _write_with_delay(
    sys.stdout,
    "STDOUT: slow output shows how captured text appears while the process is still running.",
    CHAR_DELAY_S,
  )
  time.sleep(0.15)
  _write_with_delay(
    sys.stderr,
    "STDERR: slow error-stream output follows with a different prefix and the same pacing.",
    CHAR_DELAY_S,
  )
  time.sleep(0.15)


# ------------------------------------------------


def _run_threaded_section() -> None:
  """Write from stdout and stderr threads at the same time."""

  _write_section("threaded interleaved output")
  stdout_words = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
  ]
  stderr_words = [
    "india",
    "juliet",
    "kilo",
    "lima",
    "mike",
    "november",
    "oscar",
    "papa",
  ]
  stdout_thread = threading.Thread(
    target=_thread_writer,
    args=(sys.stdout, "STDOUT", stdout_words, THREAD_CHAR_DELAY_S),
  )
  stderr_thread = threading.Thread(
    target=_thread_writer,
    args=(sys.stderr, "STDERR", stderr_words, THREAD_CHAR_DELAY_S),
  )

  stdout_thread.start()
  stderr_thread.start()
  stdout_thread.join()
  stderr_thread.join()


# ------------------------------------------------


def _run_countdown_section() -> None:
  """Write a small countdown to make the total runtime more visible."""

  _write_section("final countdown")

  for seconds_left in range(5, 0, -1):
    _write_line(sys.stdout, f"STDOUT: finishing in {seconds_left}")
    _write_line(sys.stderr, f"STDERR: finishing in {seconds_left}")
    time.sleep(0.12)


# MARK: Public API
# ------------------------------------------------


def main() -> None:
  """Run the stdout/stderr demonstration."""

  _write_line(sys.stderr, "EXAMPLE: stdout/stderr capture demo started")
  _write_line(sys.stdout, "STDOUT: first line")
  _write_line(sys.stderr, "STDERR: first line")
  _run_sequential_section()
  _run_burst_section()
  _run_slow_character_section()
  _run_threaded_section()
  _run_countdown_section()
  _write_line(sys.stdout, "STDOUT: final line")
  _write_line(sys.stderr, "STDERR: final line")
  _write_line(sys.stderr, "EXAMPLE: stdout/stderr capture demo finished")


if __name__ == "__main__":
  main()
