"""Console detection helpers."""

import ctypes
import importlib
import sys
from typing import TextIO

from timeout_dead.constants import _Const


# MARK: Helpers
# ------------------------------------------------


def _is_console_handle(fd: int) -> bool:
  """Return True iff *fd* is backed by a real Windows console."""

  try:
    msvcrt = importlib.import_module(_Const.MSVCRT_MODULE)
    get_osf_handle = getattr(msvcrt, _Const.GET_OSF_HANDLE, None)

    if get_osf_handle is None:
      return False

    handle = get_osf_handle(fd)
    mode = ctypes.c_uint32()
    get_console_mode = getattr(_Const.KERNEL32, _Const.GET_CONSOLE_MODE, None)

    if get_console_mode is not None:
      return bool(get_console_mode(handle, ctypes.byref(mode)))

    return False

  except (OSError, ValueError, ImportError):
    return False


# ------------------------------------------------


def _enable_windows_virtual_terminal(fd: int) -> bool:
  """Enable ANSI processing for one real Windows console stream."""

  if not _Const.IS_WINDOWS:
    return True

  try:
    msvcrt = importlib.import_module(_Const.MSVCRT_MODULE)
    get_osf_handle = getattr(msvcrt, _Const.GET_OSF_HANDLE, None)

    if get_osf_handle is None:
      return False

    handle = get_osf_handle(fd)
    mode = ctypes.c_uint32()
    get_console_mode = getattr(_Const.KERNEL32, _Const.GET_CONSOLE_MODE, None)
    set_console_mode = getattr(_Const.KERNEL32, _Const.SET_CONSOLE_MODE, None)

    if get_console_mode is None or set_console_mode is None:
      return False

    if not get_console_mode(handle, ctypes.byref(mode)):
      return False

    next_mode = mode.value | _Const.ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return bool(set_console_mode(handle, next_mode))

  except (OSError, ValueError, ImportError):
    return False


# ------------------------------------------------


def stream_supports_ansi(stream: TextIO) -> bool:
  """Return True when a stream is a TTY with ANSI support."""

  if not stream.isatty():
    return False

  if not _Const.IS_WINDOWS:
    return True

  try:
    return _enable_windows_virtual_terminal(stream.fileno())

  except (OSError, ValueError, AttributeError):
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
