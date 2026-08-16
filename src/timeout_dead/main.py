#!/usr/bin/env python3

"""Lightweight command timeout utility CLI entry point."""

import sys

from timeout_dead.cli.arguments import parse_arguments
from timeout_dead.cli.output import format_command_preview, write_status, write_stderr, write_stdout
from timeout_dead.constants import _Const
from timeout_dead.runner import run_command


# MARK: Public API
# ------------------------------------------------


def main(argv: list[str] | None = None) -> None:
  """Main entry point."""

  args = parse_arguments(argv)

  if not args.command:
    write_stderr(f"{_Const.MSG_NO_COMMAND}{_Const.NEWLINE}")
    sys.exit(_Const.EXIT_FAILURE)

  if args.sec <= _Const.MIN_TIMEOUT_S:
    write_stderr(f"{_Const.MSG_TIMEOUT_POSITIVE}{_Const.NEWLINE}")
    sys.exit(_Const.EXIT_FAILURE)

  command_string = " ".join(args.command)
  capture_output = args.capture_output

  if args.no_output and capture_output:
    write_stderr(f"{_Const.MSG_CAPTURE_IGNORED}{_Const.NEWLINE}")
    capture_output = False

  if not args.no_output:
    command_preview = format_command_preview(command_string)
    write_stdout(f"{_Const.RUNNING_TITLE}: {command_preview}{_Const.BLANK_LINE}")
    write_stdout(
      f"{_Const.TIMEOUT_TITLE}: {args.sec} {_Const.TIMEOUT_UNIT}{_Const.CAPTURE_BLOCK_GAP}"
    )

    if not capture_output:
      write_stdout(f"{_Const.STDOUT_TITLE}{_Const.BLANK_LINE}")

  return_code, timed_out = run_command(
    command_string,
    timeout=args.sec,
    signal_name=args.signal,
    no_output=args.no_output,
    capture_output=capture_output,
  )

  if not args.no_output and not capture_output:
    write_stdout(_Const.NEWLINE)

  write_stdout(f"{_Const.EXIT_CODE_TITLE}: {return_code}{_Const.BLANK_LINE}")

  if timed_out:
    write_status(_Const.msg_timeout(args.sec), _Const.ANSI_RED)

  elif return_code == 0:
    write_status(_Const.STATUS_SUCCESS, _Const.ANSI_GREEN)

  sys.exit(return_code)


if __name__ == "__main__":
  main()
