"""Command execution with timeout."""

import ctypes
import os
import shutil
import signal
import subprocess
import sys
import threading
from ctypes.wintypes import HANDLE

from timeout_dead.constants import _Const
from timeout_dead.process import find_bash, kill_with_timeout, terminate_process
from timeout_dead.win32 import (
  assign_process_to_job,
  close_job,
  create_kill_on_close_job,
)


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


def _stdin_is_console() -> bool:
  """Return True iff stdin is a real Windows console (not a pipe / redirection)."""

  if not _Const.IS_WINDOWS:
    return False

  try:
    return _is_console_handle(sys.stdin.fileno())

  except (OSError, ValueError, AttributeError):
    return False


def _stdout_is_console() -> bool:
  """Return True iff stdout is a real Windows console."""

  if not _Const.IS_WINDOWS:
    return False

  try:
    return _is_console_handle(sys.stdout.fileno())

  except (OSError, ValueError, AttributeError):
    return False


# MARK: Public API
# ------------------------------------------------


def run_command(
  command_string: str,
  timeout: float = _Const.DEFAULT_TIMEOUT_S,
  signal_name: str = "TERM",
  no_output: bool = False,
) -> int:
  """
  Run a command with timeout via bash.

  Args:
    command_string (str): command to execute
    timeout (float): timeout in seconds
    signal_name (str): signal name for graceful termination
    no_output (bool): suppress normal output

  Returns:
    int: process return code (-1 on launch error)
  """

  signal_num = _Const.SIGNAL_MAP.get(signal_name, signal.SIGTERM)
  process: subprocess.Popen[bytes] | subprocess.Popen[str] | None = None
  timer: threading.Timer | None = None
  job_handle: HANDLE | None = None
  con_in_fd: int | None = None
  job_closed: bool = False

  try:
    # Create kill-on-close Job Object BEFORE starting the process so the race
    # window between Popen() and AssignProcessToJobObject() is as small as
    # possible.
    job_handle = create_kill_on_close_job()

    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if _Const.IS_WINDOWS else 0

    stdin: int | None = subprocess.DEVNULL if no_output else None
    cmd: list[str] = [find_bash(), "-c", command_string]

    if _Const.IS_WINDOWS and not no_output and _stdin_is_console() and _stdout_is_console():
      winpty = shutil.which("winpty")

      if winpty is not None:
        cmd = [winpty, "--", *cmd]

      else:
        try:
          con_in_fd = os.open("CONIN$", os.O_RDONLY | getattr(os, "O_BINARY", 0))
          stdin = con_in_fd

        except OSError:
          pass

    process = subprocess.Popen(
      cmd,
      stdin=stdin,
      stdout=subprocess.DEVNULL if no_output else None,
      stderr=subprocess.DEVNULL if no_output else None,
      creationflags=creationflags,
      preexec_fn=getattr(os, "setpgrp", None) if not _Const.IS_WINDOWS else None,
    )

    if job_handle is not None:
      assign_process_to_job(job_handle, process.pid)
      process._job_handle = job_handle  # type: ignore[attr-defined]

    timer = threading.Timer(
      timeout,
      kill_with_timeout,
      args=(process, timeout, signal_num),
    )

    timer.start()
    process.wait()
    timer.cancel()
    timer.join()

    return process.returncode

  except Exception as e:
    if timer:
      timer.cancel()
      timer.join()

    if process and process.poll() is None:
      terminate_process(process, signal_num=None)

    print(f"{_Const.msg_exec_error(e)}", file=sys.stderr)

    return -1

  finally:
    if con_in_fd is not None:
      os.close(con_in_fd)

    if job_handle is not None and not job_closed:
      # If terminate_process already closed the handle (via the timer thread),
      # this is a harmless double-close (CloseHandle returns FALSE, no crash).
      close_job(job_handle)
      job_closed = True
