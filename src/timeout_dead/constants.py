"""Constants and configuration for timeout-dead."""

import ctypes
import os
import signal
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version


# MARK: Constants
# ------------------------------------------------


class _Const:
  PROJECT_PACKAGE_NAME: str = "timeout-dead"
  UNKNOWN_VERSION: str = "unknown"

  DEFAULT_TIMEOUT_S: float = 60.0
  MIN_TIMEOUT_S: float = 0.0
  GRACE_PERIOD_S: float = 1.0
  EXIT_FAILURE: int = 1
  COUNT_INCREMENT: int = 1
  INITIAL_LINE_COUNT: int = 0
  INITIAL_FINISHED_COUNT: int = 0
  INITIAL_RENDER_TIME: float = 0.0
  NO_FLAGS: int = 0
  SEPARATOR: str = "-" * 50

  NEWLINE: str = "\n"
  CARRIAGE_RETURN: str = "\r"
  BLANK_LINE: str = "\n\n"
  STDERR_TITLE: str = "Err:"
  STDOUT_TITLE: str = "Out:"
  RUNNING_TITLE: str = "Running"
  TIMEOUT_TITLE: str = "Timeout"
  TIMEOUT_UNIT: str = "seconds"
  EXIT_CODE_TITLE: str = "Exit code"
  COMMAND_JOINER: str = " "
  MAIN_MODULE_NAME: str = "__main__"

  MSG_NO_COMMAND: str = "Error: no command specified"
  MSG_BASH_NOT_FOUND: str = "bash not found in PATH"
  MSG_TIMEOUT_POSITIVE: str = "Error: timeout must be positive"
  MSG_CAPTURE_IGNORED: str = "Warning: --capture-output is ignored when --no-output is set"

  CLI_DESCRIPTION: str = "Lightweight command timeout utility."
  CLI_EPILOG: str = (
    "Flag priority:\n"
    "  -h/--help and -v/--version exit immediately and ignore all other arguments.\n"
    "  --sec and --signal apply before output mode selection.\n"
    "  --no-output suppresses normal output and overrides --capture-output.\n"
    "  COMMAND is required unless -h/--help or -v/--version is used."
  )
  CLI_TIMEOUT_METAVAR: str = "SECONDS"
  CLI_SIGNAL_METAVAR: str = "SIGNAL"
  CLI_COMMAND_METAVAR: str = "COMMAND"
  CLI_TIMEOUT_HELP: str = "timeout in seconds (default: {timeout}, must be > 0)"
  CLI_SIGNAL_HELP: str = "signal to send on timeout (default: TERM)"
  CLI_NO_OUTPUT_HELP: str = "suppress normal output and override --capture-output"
  CLI_CAPTURE_OUTPUT_HELP: str = (
    "capture and format stdout/stderr blocks (default: interactive mode)"
  )
  CLI_COMMAND_HELP: str = "command to execute (required unless -h/--help or -v/--version is used)"

  OPT_HELP_SHORT: str = "-h"
  OPT_HELP_LONG: str = "--help"
  OPT_VERSION_SHORT: str = "-v"
  OPT_VERSION_LONG: str = "--version"
  OPT_SEC: str = "--sec"
  OPT_SEC_PREFIX: str = "--sec="
  OPT_SIGNAL: str = "--signal"
  OPT_SIGNAL_PREFIX: str = "--signal="
  OPT_NO_OUTPUT: str = "--no-output"
  OPT_CAPTURE_OUTPUT_SHORT: str = "-c"
  OPT_CAPTURE_OUTPUT_LONG: str = "--capture-output"
  OPT_COMMAND_SEPARATOR: str = "--"
  OPT_PREFIX: str = "-"
  ARG_ACTION_VERSION: str = "version"
  ARG_ACTION_STORE_TRUE: str = "store_true"
  ARG_DEST_COMMAND: str = "command"

  DEFAULT_SIGNAL_NAME: str = "TERM"

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
  JOB_OBJECT_BASIC_LIMIT_INFORMATION_INDEX: int = 1
  STRUCT_BASIC_LIMIT_INFORMATION: str = "BasicLimitInformation"
  STRUCT_BASIC_LIMIT_INFORMATION_SIZE: int = 10
  STRUCT_IO_INFO: str = "IoInfo"
  STRUCT_IO_INFO_SIZE: int = 2
  STRUCT_PROCESS_MEMORY_LIMIT: str = "ProcessMemoryLimit"
  STRUCT_JOB_MEMORY_LIMIT: str = "JobMemoryLimit"
  STRUCT_PEAK_PROCESS_MEMORY_USED: str = "PeakProcessMemoryUsed"
  STRUCT_PEAK_JOB_MEMORY_USED: str = "PeakJobMemoryUsed"

  # Captured output preview
  TAIL_LINE_COUNT: int = 5
  PREVIEW_FRAME_LINES: int = 16
  LIVE_RENDER_INTERVAL_S: float = 0.05
  DEFAULT_TERMINAL_COLUMNS: int = 80
  DEFAULT_TERMINAL_LINES: int = 24
  MIN_PREVIEW_WIDTH: int = 20
  TERMINAL_WIDTH_PADDING: int = 1
  ELLIPSIS: str = "..."
  ELLIPSIS_WIDTH: int = len(ELLIPSIS)
  ENABLE_VIRTUAL_TERMINAL_PROCESSING: int = 0x0004
  HIDE_CURSOR: str = "\x1b[?25l"
  SHOW_CURSOR: str = "\x1b[?25h"
  CLEAR_LINE: str = "\x1b[K"
  ANSI_CURSOR_UP: str = "\x1b[{line_count}F"

  # Subprocess and shell
  BASH_EXECUTABLE: str = "bash"
  BASH_COMMAND_FLAG: str = "-c"
  WINPTY_EXECUTABLE: str = "winpty"
  WINPTY_SEPARATOR: str = "--"
  WINDOWS_CONSOLE_INPUT: str = "CONIN$"
  WINDOWS_BINARY_FLAG: str = "O_BINARY"
  CREATE_NEW_PROCESS_GROUP: str = "CREATE_NEW_PROCESS_GROUP"
  UNIX_SET_PROCESS_GROUP: str = "setpgrp"
  SUBPROCESS_ENCODING: str = "utf-8"
  SUBPROCESS_ERRORS: str = "backslashreplace"
  EXEC_ERROR_RETURN_CODE: int = -1

  # Windows process tree termination
  TASKKILL_EXECUTABLE: str = "taskkill"
  TASKKILL_TREE_FLAG: str = "/T"
  TASKKILL_FORCE_FLAG: str = "/F"
  TASKKILL_PID_FLAG: str = "/PID"
  TASKKILL_TIMEOUT_S: float = 5.0
  PROCESS_JOB_HANDLE_ATTR: str = "_job_handle"
  WINDOWS_CTRL_C_EVENT: str = "CTRL_C_EVENT"
  WINDOWS_CTRL_BREAK_EVENT: str = "CTRL_BREAK_EVENT"
  UNIX_SIGKILL: str = "SIGKILL"
  STREAM_READ_SIZE: int = 1

  # Windows console APIs
  GET_CONSOLE_MODE: str = "GetConsoleMode"
  SET_CONSOLE_MODE: str = "SetConsoleMode"

  try:
    PROJECT_VERSION = _get_version(PROJECT_PACKAGE_NAME)

  except PackageNotFoundError:
    PROJECT_VERSION = UNKNOWN_VERSION
