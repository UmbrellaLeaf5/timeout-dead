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
  print(_Const.SEPARATOR)


# ------------------------------------------------


def print_footer(return_code: int) -> None:
  """Print execution footer."""

  print(_Const.SEPARATOR)
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
