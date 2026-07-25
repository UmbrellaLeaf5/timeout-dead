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
  HEADER_SEPARATOR: str = "-" * 50

  MSG_NO_COMMAND: str = "Error: no command specified"
  MSG_BASH_NOT_FOUND: str = "bash not found in PATH"
  MSG_TIMEOUT: str = "Timeout exceeded {}s"
  MSG_EXEC_ERROR: str = "Execution error: {}"
  MSG_PROCESS_NOT_FOUND: str = "Process already gone (pid {}), nothing to terminate"
  MSG_TERMINATE_FAILED: str = "Failed to terminate process pid {}: {}"

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
