"""CLI stdout helpers."""

import sys

from timeout_dead.constants import _Const
from timeout_dead.platform.console import stream_supports_ansi


# MARK: Public API
# ------------------------------------------------


def write_stdout(text: str) -> None:
  """Write text directly to stdout and flush immediately."""

  sys.stdout.write(text)
  sys.stdout.flush()


# ------------------------------------------------


def write_stderr(text: str) -> None:
  """Write text directly to stderr and flush immediately."""

  sys.stderr.write(text)
  sys.stderr.flush()


# ------------------------------------------------


def write_status(message: str, color: str) -> None:
  """Write a final CLI status, colored only on supported terminals."""

  text = message

  if stream_supports_ansi(sys.stderr):
    text = f"{color}{message}{_Const.ANSI_RESET}"

  write_stderr(f"{text}{_Const.NEWLINE}")
