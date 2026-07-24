#!/usr/bin/env python3

"""Легковесная утилита для запуска команд с таймаутом."""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time


# MARK: Constants
# ------------------------------------------------


class _Const:
  DEFAULT_TIMEOUT_S: int = 60
  GRACE_PERIOD_S: float = 1.0
  HEADER_SEPARATOR: str = "-" * 60

  MSG_NO_COMMAND: str = "Error: no command specified"
  MSG_BASH_NOT_FOUND: str = "bash not found in PATH — Git Bash is required"
  MSG_TIMEOUT: str = "Timeout exceeded {} seconds"
  MSG_EXEC_ERROR: str = "Execution error: {}"

  SIGNAL_NAMES: tuple[str, ...] = ("TERM", "KILL", "HUP", "INT")

  SIGNAL_MAP: dict[str, int] = {
    "TERM": signal.SIGTERM,
    "KILL": getattr(signal, "SIGKILL", signal.SIGTERM),
    "HUP": getattr(signal, "SIGHUP", signal.SIGTERM),
    "INT": signal.SIGINT,
  }


# MARK: Private Helpers
# ------------------------------------------------


def _is_windows() -> bool:
  return os.name == "nt"


# ------------------------------------------------


def _find_bash() -> str:
  """
  Ищет bash в PATH.

  Returns:
    str: путь к исполняемому файлу bash

  Raises:
    SystemExit: если bash не найден
  """

  bash_path = shutil.which("bash")

  if bash_path is None:
    print(f"\n{_Const.MSG_BASH_NOT_FOUND}", file=sys.stderr)
    sys.exit(1)

  return bash_path


# MARK: Process termination
# ------------------------------------------------


def _terminate_process(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  *,
  force: bool = False,
  signal_num: int = signal.SIGTERM,
) -> None:
  """Завершает процесс — мягко (выбранным сигналом) или жёстко."""

  if process.poll() is not None:
    return

  try:
    if _is_windows():
      if force:
        process.kill()

      elif signal_num == signal.SIGINT:
        process.send_signal(signal.SIGINT)

      else:
        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM)
        process.send_signal(ctrl_break)

    else:
      pgid = os.getpgid(process.pid)  # pyright: ignore[reportAttributeAccessIssue]

      if force:
        os.killpg(pgid, signal.SIGKILL)  # pyright: ignore[reportAttributeAccessIssue]

      else:
        os.killpg(pgid, signal_num)  # pyright: ignore[reportAttributeAccessIssue]

  except (ProcessLookupError, OSError):
    pass


# ------------------------------------------------


def _kill_with_timeout(
  process: subprocess.Popen[bytes] | subprocess.Popen[str],
  timeout: int,
  signal_num: int = signal.SIGTERM,
) -> None:
  """Убивает процесс по таймауту с двухэтапной логикой."""

  if process.poll() is not None:
    return

  _terminate_process(process, signal_num=signal_num)
  time.sleep(_Const.GRACE_PERIOD_S)

  if process.poll() is None:
    _terminate_process(process, force=True)

  print(f"\n{_Const.MSG_TIMEOUT.format(timeout)}", file=sys.stderr)


# MARK: Public API
# ------------------------------------------------


def run_command(
  command_string: str,
  timeout: int = _Const.DEFAULT_TIMEOUT_S,
  signal_name: str = "TERM",
  no_output: bool = False,
) -> int:
  """
  Запускает команду с таймаутом через bash.

  Args:
    command_string (str): команда для выполнения
    timeout (int): таймаут в секундах
    signal_name (str): имя сигнала для мягкого завершения
    no_output (bool): подавлять ли обычный вывод

  Returns:
    int: код возврата процесса (-1 при ошибке запуска)
  """

  signal_num = _Const.SIGNAL_MAP.get(signal_name, signal.SIGTERM)
  process: subprocess.Popen[bytes] | subprocess.Popen[str] | None = None
  timer: threading.Timer | None = None

  try:
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if _is_windows() else 0
    start_new_session = not _is_windows()

    process = subprocess.Popen(
      [_find_bash(), "-c", command_string],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      creationflags=creationflags,
      start_new_session=start_new_session,
    )

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
        _terminate_process(process, force=True)

      except Exception:
        pass

    print(f"{_Const.MSG_EXEC_ERROR.format(e)}", file=sys.stderr)

    return -1


# ------------------------------------------------


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
  """Разбирает аргументы командной строки."""

  parser = argparse.ArgumentParser(
    description="Lightweight command timeout utility.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument(
    "--sec",
    type=int,
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


def print_header(command: str, timeout: int) -> None:
  """Выводит заголовок выполнения."""

  print(f"Running: {command}")
  print(f"Timeout: {timeout} seconds")
  print(_Const.HEADER_SEPARATOR)


# ------------------------------------------------


def print_footer(return_code: int) -> None:
  """Выводит футер выполнения."""

  print(_Const.HEADER_SEPARATOR)
  print(f"Exit code: {return_code}")


# ------------------------------------------------


def main(argv: list[str] | None = None) -> None:
  """Главная точка входа."""

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
