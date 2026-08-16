"""Terminal control helpers for captured output preview."""

import sys

from timeout_dead.cli.output import write_stdout
from timeout_dead.constants import _Const
from timeout_dead.platform.console import stream_supports_ansi


def hide_cursor() -> None:
  """Hide the terminal cursor during live preview redraws."""

  write_stdout(_Const.HIDE_CURSOR)


# ------------------------------------------------


def show_cursor() -> None:
  """Restore the terminal cursor after live preview redraws."""

  write_stdout(_Const.SHOW_CURSOR)


def supports_live_preview() -> bool:
  """Return True when stdout can handle ANSI redraw safely."""

  return stream_supports_ansi(sys.stdout)
