"""Constants and configuration for timeout-dead."""

import ctypes
import os
import signal
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version


# MARK: Constants
# ------------------------------------------------


class _Const:
  DEFAULT_TIMEOUT_S: float = 60.0
  GRACE_PERIOD_S: float = 1.0
  SEPARATOR: str = "-" * 50

  MSG_NO_COMMAND: str = "Error: no command specified"
  MSG_BASH_NOT_FOUND: str = "bash not found in PATH"
  MSG_TIMEOUT_POSITIVE: str = "Error: timeout must be positive"

  @staticmethod
  def msg_timeout(timeout_s: float) -> str:
    return f"Timeout exceeded {timeout_s}s"

  # ------------------------------------------------

  @staticmethod
  def msg_exec_error(error: object) -> str:
    return f"Execution error: {error}"

  # ------------------------------------------------

  @staticmethod
  def msg_process_not_found(pid: int) -> str:
    return f"Process already gone (pid {pid}), nothing to terminate"

  # ------------------------------------------------

  @staticmethod
  def msg_terminate_failed(pid: int, exc: Exception) -> str:
    return f"Failed to terminate process pid {pid}: {exc}"

  SIGNAL_NAMES: tuple[str, ...] = ("TERM", "KILL", "HUP", "INT")

  SIGNAL_MAP: dict[str, int] = {
    "TERM": signal.SIGTERM,
    "KILL": getattr(signal, "SIGKILL", signal.SIGTERM),
    "HUP": getattr(signal, "SIGHUP", signal.SIGTERM),
    "INT": signal.SIGINT,
  }

  # Platform
  IS_WINDOWS: bool = os.name == "nt"
  _WINDLL = getattr(ctypes, "windll", None)
  KERNEL32 = _WINDLL.kernel32 if _WINDLL is not None else None

  # Windows Job Object
  JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: int = 0x00002000
  JOB_OBJECT_EXTENDED_LIMIT_INFORMATION: int = 9
  PROCESS_SET_QUOTA: int = 0x0100
  PROCESS_TERMINATE: int = 0x0001

  try:
    PROJECT_VERSION = _get_version("timeout-dead")

  except PackageNotFoundError:
    PROJECT_VERSION = "unknown"
