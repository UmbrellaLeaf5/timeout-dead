"""Process termination and signal handling."""

import os
import shutil
import signal
import subprocess
import sys
import time
from ctypes.wintypes import HANDLE

from timeout_dead.constants import _Const
from timeout_dead.win32 import close_job


# MARK: Bash detection
# ------------------------------------------------


def find_bash() -> str:
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


# MARK: Process termination
# ------------------------------------------------


def terminate_process(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  *,
  signal_num: int | None = None,
) -> None:
  """Terminate the process. signal_num=None means force-kill (SIGKILL)."""

  if process.poll() is not None:
    return

  try:
    if _Const.IS_WINDOWS:
      if signal_num is None:
        job_handle: HANDLE | None = getattr(process, "_job_handle", None)

        if job_handle is not None:
          close_job(job_handle)
          process._job_handle = None  # type: ignore[attr-defined]

          return

        process.kill()

        return

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

  except ProcessLookupError:
    print(
      f"\n{_Const.msg_process_not_found(process.pid)}",
      file=sys.stderr,
    )

  except OSError as exc:
    print(
      f"\n{_Const.msg_terminate_failed(process.pid, exc)}",
      file=sys.stderr,
    )


# ------------------------------------------------


def kill_with_timeout(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  timeout: float,
  signal_num: int = signal.SIGTERM,
) -> None:
  """Kill the process after timeout with two-stage logic."""

  if process.poll() is not None:
    return

  terminate_process(process, signal_num=signal_num)
  time.sleep(_Const.GRACE_PERIOD_S)

  if process.poll() is None:
    terminate_process(process)

  print(f"\n{_Const.msg_timeout(timeout)}", file=sys.stderr)
