"""Process termination and signal handling."""

import os
import signal
import subprocess
import sys
import time
from ctypes.wintypes import HANDLE

from timeout_dead.constants import _Const
from timeout_dead.platform.windows import close_job


# MARK: Helpers
# ------------------------------------------------


def _taskkill_tree(pid: int) -> None:
  """Kill *pid* and all its descendants via taskkill (Windows)."""

  try:
    subprocess.run(
      [
        _Const.TASKKILL_EXECUTABLE,
        _Const.TASKKILL_TREE_FLAG,
        _Const.TASKKILL_FORCE_FLAG,
        _Const.TASKKILL_PID_FLAG,
        str(pid),
      ],
      capture_output=True,
      check=False,
      timeout=_Const.TASKKILL_TIMEOUT_S,
    )

  except (OSError, subprocess.TimeoutExpired):
    pass


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
        # Kill the whole tree FIRST, while bash is still alive, so /T can
        # enumerate and kill children that escaped the Job Object (race
        # between Popen and AssignProcessToJobObject).
        _taskkill_tree(process.pid)

        job_handle: HANDLE | None = getattr(process, _Const.PROCESS_JOB_HANDLE_ATTR, None)

        if job_handle is not None:
          close_job(job_handle)
          setattr(process, _Const.PROCESS_JOB_HANDLE_ATTR, None)

        # Kill the main process directly (belt).
        try:
          process.kill()

        except OSError:
          pass

        return

      windows_signal_map: dict[int | None, int] = {
        signal.SIGINT: getattr(signal, _Const.WINDOWS_CTRL_C_EVENT, signal.SIGINT),
      }
      process.send_signal(
        windows_signal_map.get(
          signal_num,
          getattr(signal, _Const.WINDOWS_CTRL_BREAK_EVENT, signal.SIGTERM),
        )
      )

    else:
      pgid = os.getpgid(process.pid)  # pyright: ignore[reportAttributeAccessIssue]

      unix_signal = (
        getattr(signal, _Const.UNIX_SIGKILL, signal.SIGTERM) if signal_num is None else signal_num
      )
      os.killpg(pgid, unix_signal)  # pyright: ignore[reportAttributeAccessIssue]

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
