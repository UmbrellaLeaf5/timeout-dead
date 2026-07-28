"""Command execution with timeout."""

import os
import shutil
import signal
import subprocess
import sys
import threading
from ctypes.wintypes import HANDLE
from typing import TextIO, cast

from timeout_dead.capture import stream_captured_output
from timeout_dead.console import stdin_is_console, stdout_is_console
from timeout_dead.constants import _Const
from timeout_dead.process import find_bash, kill_with_timeout, terminate_process
from timeout_dead.win32 import (
  assign_process_to_job,
  close_job,
  create_kill_on_close_job,
)


# MARK: Public API
# ------------------------------------------------


def run_command(
  command_string: str,
  timeout: float = _Const.DEFAULT_TIMEOUT_S,
  signal_name: str = "TERM",
  no_output: bool = False,
  capture_output: bool = False,
) -> int:
  """
  Run a command with timeout via bash.

  Args:
    command_string (str): command to execute
    timeout (float): timeout in seconds
    signal_name (str): signal name for graceful termination
    no_output (bool): suppress normal output
    capture_output (bool): capture and format stdout/stderr

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

    if capture_output and not no_output:
      stdout_target: int | None = subprocess.PIPE
      stderr_target: int | None = subprocess.PIPE

    else:
      stdout_target = subprocess.DEVNULL if no_output else None
      stderr_target = subprocess.DEVNULL if no_output else None

    if (
      _Const.IS_WINDOWS
      and not capture_output
      and not no_output
      and stdin_is_console()
      and stdout_is_console()
    ):
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
      stdout=stdout_target,
      stderr=stderr_target,
      text=capture_output,
      encoding="utf-8" if capture_output else None,
      errors="backslashreplace" if capture_output else None,
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

    if capture_output and not no_output:
      stream_captured_output(
        cast(TextIO, process.stdout),
        cast(TextIO, process.stderr),
      )
      process.wait()

    else:
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
