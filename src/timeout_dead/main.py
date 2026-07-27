#!/usr/bin/env python3

"""Lightweight command timeout utility — CLI entry point."""

import argparse
import sys

from timeout_dead.constants import _Const
from timeout_dead.runner import run_command


# MARK: Public API
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
    version=f"timeout-dead {_Const.PROJECT_VERSION}",
  )

  parser.add_argument(
    "--sec",
    type=float,
    default=_Const.DEFAULT_TIMEOUT_S,
    help=f"timeout in seconds (default: {_Const.DEFAULT_TIMEOUT_S}, must be > 0)",
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
    help="suppress normal output (stdout, stderr)",
  )

  parser.add_argument(
    "-c",
    "--capture-output",
    action="store_true",
    default=False,
    help="capture and format stdout/stderr with separators (default: interactive mode)",
  )

  parser.add_argument(
    "command",
    nargs=argparse.REMAINDER,
    help="command to execute",
    metavar="COMMAND",
  )

  return parser.parse_args(argv)


# ------------------------------------------------


def main(argv: list[str] | None = None) -> None:
  """Main entry point."""

  args = parse_arguments(argv)

  if not args.command:
    print(f"{_Const.MSG_NO_COMMAND}", file=sys.stderr)
    sys.exit(1)

  if args.sec <= 0:
    print(_Const.MSG_TIMEOUT_POSITIVE, file=sys.stderr)
    sys.exit(1)

  command_string = " ".join(args.command)

  if not args.no_output:
    print(f"Running: {command_string}")
    print(f"Timeout: {args.sec} seconds")

    print(_Const.SEPARATOR)
    sys.stdout.flush()

    if args.capture_output:
      print()
      sys.stdout.flush()

  return_code = run_command(
    command_string,
    timeout=args.sec,
    signal_name=args.signal,
    no_output=args.no_output,
    capture_output=args.capture_output,
  )

  if not args.no_output:
    if args.capture_output:
      print()
      sys.stdout.flush()

    print(_Const.SEPARATOR)
    sys.stdout.flush()

    print(f"Exit code: {return_code}\n")
    sys.stdout.flush()

  sys.exit(return_code)


if __name__ == "__main__":
  main()
