#!/usr/bin/env python3

"""Lightweight command timeout utility."""

import argparse
import ctypes
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from ctypes import byref, sizeof, windll
from ctypes.wintypes import HANDLE
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version


# MARK: Constants
# ------------------------------------------------


class _Const:
  DEFAULT_TIMEOUT_S: float = 60.0
  GRACE_PERIOD_S: float = 1.0
  HEADER_SEPARATOR: str = "-" * 50

  MSG_NO_COMMAND: str = "Error: no command specified"
  MSG_BASH_NOT_FOUND: str = "bash not found in PATH"
  MSG_TIMEOUT: str = "Timeout exceeded {}s"
  MSG_EXEC_ERROR: str = "Execution error: {}"

  SIGNAL_NAMES: tuple[str, ...] = ("TERM", "KILL", "HUP", "INT")

  SIGNAL_MAP: dict[str, int] = {
    "TERM": signal.SIGTERM,
    "KILL": getattr(signal, "SIGKILL", signal.SIGTERM),
    "HUP": getattr(signal, "SIGHUP", signal.SIGTERM),
    "INT": signal.SIGINT,
  }

  @staticmethod
  def _resolve_version() -> str:
    try:
      return _get_version("timeout-dead")

    except PackageNotFoundError:
      return "unknown"


_PROJECT_VERSION: str = _Const._resolve_version()


# MARK: Private Helpers
# ------------------------------------------------


def _is_windows() -> bool:
  return os.name == "nt"


# ------------------------------------------------


def _find_bash() -> str:
  """
  Locate bash executable in PATH.

  Returns:
    str: path to the bash executable

  Raises:
    SystemExit: if bash is not found
  """

  bash_path = shutil.which("bash")

  if bash_path is None:
    print(f"\n{_Const.MSG_BASH_NOT_FOUND}", file=sys.stderr)
    sys.exit(1)

  return bash_path


# MARK: Windows Job Object (process tree force-kill)
# ------------------------------------------------


_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
  _fields_ = [
    ("BasicLimitInformation", ctypes.c_ulonglong * 10),
    ("IoInfo", ctypes.c_ulonglong * 2),
    ("ProcessMemoryLimit", ctypes.c_size_t),
    ("JobMemoryLimit", ctypes.c_size_t),
    ("PeakProcessMemoryUsed", ctypes.c_size_t),
    ("PeakJobMemoryUsed", ctypes.c_size_t),
  ]


def _create_kill_on_close_job() -> HANDLE | None:
  """Create a Windows Job Object that kills processes when the handle is closed."""

  if not _is_windows():
    return None

  job = windll.kernel32.CreateJobObjectW(None, None)

  if not job:
    return None

  info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
  info.BasicLimitInformation[1] = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

  ok = windll.kernel32.SetInformationJobObject(
    job,
    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
    byref(info),
    sizeof(info),
  )

  if not ok:
    windll.kernel32.CloseHandle(job)

    return None

  return job


def _assign_process_to_job(job: HANDLE, pid: int) -> bool:
  """Assign a process to a Windows Job Object."""

  proc_handle = windll.kernel32.OpenProcess(
    _PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, pid
  )

  if not proc_handle:
    return False

  ok = windll.kernel32.AssignProcessToJobObject(job, proc_handle)
  windll.kernel32.CloseHandle(proc_handle)

  return bool(ok)


def _close_job(job: HANDLE | None) -> None:
  """Close a Job Object handle, killing all processes in the job."""

  if job is not None:
    windll.kernel32.CloseHandle(job)


# MARK: Process termination
# ------------------------------------------------


def _terminate_process(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  *,
  signal_num: int | None = None,
) -> None:
  """Terminate the process. signal_num=None means force-kill (SIGKILL)."""

  if process.poll() is not None:
    return

  try:
    if _is_windows():
      if signal_num is None:
        job_handle = getattr(process, "_job_handle", None)

        if job_handle is not None:
          _close_job(job_handle)

        else:
          process.kill()

      elif signal_num == signal.SIGINT:
        process.send_signal(signal.SIGINT)

      else:
        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM)
        process.send_signal(ctrl_break)

    else:
      pgid = os.getpgid(process.pid)  # pyright: ignore[reportAttributeAccessIssue]

      if signal_num is None:
        os.killpg(pgid, signal.SIGKILL)  # pyright: ignore[reportAttributeAccessIssue]

      else:
        os.killpg(pgid, signal_num)  # pyright: ignore[reportAttributeAccessIssue]

  except (ProcessLookupError, OSError):
    pass


# ------------------------------------------------


def _kill_with_timeout(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  timeout: float,
  signal_num: int = signal.SIGTERM,
) -> None:
  """Kill the process after timeout with two-stage logic."""

  if process.poll() is not None:
    return

  _terminate_process(process, signal_num=signal_num)
  time.sleep(_Const.GRACE_PERIOD_S)

  if process.poll() is None:
    _terminate_process(process)

  print(f"\n{_Const.MSG_TIMEOUT.format(timeout)}", file=sys.stderr)


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
    creationflags = (
      getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if _is_windows() else 0
    )

    start_new_session = not _is_windows()

    process = subprocess.Popen(
      [_find_bash(), "-c", command_string],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      creationflags=creationflags,
      start_new_session=start_new_session,
    )

    job_handle = _create_kill_on_close_job()

    if job_handle is not None:
      _assign_process_to_job(job_handle, process.pid)
      process._job_handle = job_handle  # type: ignore[attr-defined]

    timer = threading.Timer(
      timeout,
      _kill_with_timeout,
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
      try:
        _terminate_process(process)

      except Exception:
        pass

    print(f"{_Const.MSG_EXEC_ERROR.format(e)}", file=sys.stderr)

    return -1

  finally:
    if job_handle is not None:
      _close_job(job_handle)


# ------------------------------------------------


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
  """Parse command-line arguments."""

  parser = argparse.ArgumentParser(
    description="Lightweight command timeout utility.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"timeout-dead {_PROJECT_VERSION}",
  )

  parser.add_argument(
    "--sec",
    type=float,
    default=_Const.DEFAULT_TIMEOUT_S,
    help=f"timeout in seconds (default: {_Const.DEFAULT_TIMEOUT_S})",
    metavar="SECONDS",
  )

  parser.add_argument(
    "--signal",
    type=str.upper,
    default="TERM",
    choices=list(_Const.SIGNAL_NAMES),
    help="signal to send on timeout (default: TERM)",
    metavar="SIGNAL",
  )

  parser.add_argument(
    "--no-output",
    action="store_true",
    default=False,
    help="suppress normal output (stdout, stderr, header, footer)",
  )

  parser.add_argument(
    "command",
    nargs=argparse.REMAINDER,
    help="command to execute",
    metavar="COMMAND",
  )

  return parser.parse_args(argv)


# ------------------------------------------------


def print_header(command: str, timeout: float) -> None:
  """Print execution header."""

  print(f"Running: {command}")
  print(f"Timeout: {timeout} seconds")
  print(_Const.HEADER_SEPARATOR)


# ------------------------------------------------


def print_footer(return_code: int) -> None:
  """Print execution footer."""

  print(_Const.HEADER_SEPARATOR)
  print(f"Exit code: {return_code}")


# ------------------------------------------------


def main(argv: list[str] | None = None) -> None:
  """Main entry point."""

  args = parse_arguments(argv)

  if not args.command:
    print(f"{_Const.MSG_NO_COMMAND}", file=sys.stderr)
    sys.exit(1)

  command_string = " ".join(args.command)

  if not args.no_output:
    print_header(command_string, args.sec)

  return_code = run_command(
    command_string,
    timeout=args.sec,
    signal_name=args.signal,
    no_output=args.no_output,
  )

  if not args.no_output:
    print_footer(return_code)

  sys.exit(return_code)


if __name__ == "__main__":
  main()
