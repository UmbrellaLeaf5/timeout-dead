"""Console detection helpers."""

import ctypes
import sys

from timeout_dead.constants import _Const


# MARK: Helpers
# ------------------------------------------------


def _is_console_handle(fd: int) -> bool:
  """Return True iff *fd* is backed by a real Windows console."""

  try:
    import msvcrt  # noqa: PLC0415  — Windows-only, imported lazily

    handle = msvcrt.get_osfhandle(fd)  # pyright: ignore[reportAttributeAccessIssue]
    mode = ctypes.c_uint32()
    get_console_mode = getattr(_Const.KERNEL32, "GetConsoleMode", None)

    if get_console_mode is not None:
      return bool(get_console_mode(handle, ctypes.byref(mode)))

    return False

  except (OSError, ValueError, ImportError):
    return False


# MARK: Public API
# ------------------------------------------------


def stdin_is_console() -> bool:
  """Return True iff stdin is a real Windows console (not a pipe / redirection)."""

  if not _Const.IS_WINDOWS:
    return False

  try:
    return _is_console_handle(sys.stdin.fileno())

  except (OSError, ValueError, AttributeError):
    return False


# ------------------------------------------------


def stdout_is_console() -> bool:
  """Return True iff stdout is a real Windows console."""

  if not _Const.IS_WINDOWS:
    return False

  try:
    return _is_console_handle(sys.stdout.fileno())

  except (OSError, ValueError, AttributeError):
    return False
