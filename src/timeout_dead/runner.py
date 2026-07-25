"""Command execution with timeout."""

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
  is_windows,
)


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

  try:
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if is_windows() else 0

    start_new_session = not is_windows()

    process = subprocess.Popen(
      [find_bash(), "-c", command_string],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      creationflags=creationflags,
      start_new_session=start_new_session,
    )

    job_handle = create_kill_on_close_job()

    if job_handle is not None:
      assign_process_to_job(job_handle, process.pid)
      process._job_handle = job_handle  # type: ignore[attr-defined]

    timer = threading.Timer(
      timeout,
      kill_with_timeout,
      args=(process, timeout, signal_num),
    )

    timer.start()

    stdout, stderr = process.communicate()
    timer.cancel()

    if not no_output:
      if stdout:
        print(stdout, end="")

      if stderr:
        print(stderr, end="", file=sys.stderr)

    return process.returncode

  except Exception as e:
    if timer:
      timer.cancel()

    if process and process.poll() is None:
      terminate_process(process)

    print(f"{_Const.MSG_EXEC_ERROR.format(e)}", file=sys.stderr)

    return -1

  finally:
    if job_handle is not None:
      close_job(job_handle)
