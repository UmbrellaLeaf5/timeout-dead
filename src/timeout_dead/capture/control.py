"""Terminal control helpers for captured output preview."""

import ctypes
import importlib
import sys

from timeout_dead.cli.output import write_stdout
from timeout_dead.constants import _Const


def hide_cursor() -> None:
  """Hide the terminal cursor during live preview redraws."""

  write_stdout(_Const.HIDE_CURSOR)


# ------------------------------------------------


def show_cursor() -> None:
  """Restore the terminal cursor after live preview redraws."""

  write_stdout(_Const.SHOW_CURSOR)


# MARK: Terminal capability
# ------------------------------------------------


def _enable_windows_virtual_terminal() -> bool:
  """Enable ANSI cursor control for a real Windows console."""

  if not _Const.IS_WINDOWS:
    return True

  try:
    msvcrt = importlib.import_module(_Const.MSVCRT_MODULE)
    get_osf_handle = getattr(msvcrt, _Const.GET_OSF_HANDLE, None)

    if get_osf_handle is None:
      return True

    handle = get_osf_handle(sys.stdout.fileno())
    mode = ctypes.c_uint32()
    get_console_mode = getattr(_Const.KERNEL32, _Const.GET_CONSOLE_MODE, None)
    set_console_mode = getattr(_Const.KERNEL32, _Const.SET_CONSOLE_MODE, None)

    if get_console_mode is None or set_console_mode is None:
      return True

    if not get_console_mode(handle, ctypes.byref(mode)):
      return True

    next_mode = mode.value | _Const.ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return bool(set_console_mode(handle, next_mode))

  except (OSError, ValueError, ImportError):
    return True


# ------------------------------------------------


def supports_live_preview() -> bool:
  """Return True when stdout can handle ANSI redraw safely."""

  return sys.stdout.isatty() and _enable_windows_virtual_terminal()
