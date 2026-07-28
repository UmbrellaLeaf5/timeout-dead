#!/usr/bin/env python3

"""Lightweight command timeout utility — CLI entry point."""

import argparse
import sys

from timeout_dead.constants import _Const
from timeout_dead.runner import run_command


# MARK: Private Helpers
# ------------------------------------------------


def _has_priority_option(argv: list[str], options: tuple[str, ...]) -> bool:
  """Return True if a priority option appears before COMMAND starts."""

  skip_next = False

  for arg in argv:
    if skip_next:
      skip_next = False

    elif arg == "--":
      return False

    elif arg in options:
      return True

    elif arg in ("--sec", "--signal"):
      skip_next = True

    elif arg.startswith("--sec=") or arg.startswith("--signal="):
      pass

    elif arg in ("--no-output", "--capture-output", "-c"):
      pass

    elif not arg.startswith("-"):
      return False

  return False


# ------------------------------------------------


def _write_stdout(text: str) -> None:
  """Write text directly to stdout and flush immediately."""

  sys.stdout.write(text)
  sys.stdout.flush()


# ------------------------------------------------


# MARK: Public API
# ------------------------------------------------


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
  """Parse command-line arguments."""

  argument_list = sys.argv[1:] if argv is None else argv
  parser = argparse.ArgumentParser(
    description="Lightweight command timeout utility.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=(
      "Flag priority:\n"
      "  -h/--help and -v/--version exit immediately and ignore all other arguments.\n"
      "  --sec and --signal apply before output mode selection.\n"
      "  --no-output suppresses normal output and overrides --capture-output.\n"
      "  COMMAND is required unless -h/--help or -v/--version is used."
    ),
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
    help="suppress normal output and override --capture-output",
  )

  parser.add_argument(
    "-c",
    "--capture-output",
    action="store_true",
    default=False,
    help="capture and format stdout/stderr blocks (default: interactive mode)",
  )

  parser.add_argument(
    "command",
    nargs=argparse.REMAINDER,
    help="command to execute (required unless -h/--help or -v/--version is used)",
    metavar="COMMAND",
  )

  if _has_priority_option(argument_list, ("-h", "--help")):
    parser.parse_args(["--help"])

  if _has_priority_option(argument_list, ("-v", "--version")):
    parser.parse_args(["--version"])

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
  capture_output = args.capture_output

  if args.no_output and capture_output:
    print(_Const.MSG_CAPTURE_IGNORED, file=sys.stderr)
    capture_output = False

  if not args.no_output:
    _write_stdout(f"Running: {command_string}\n")
    _write_stdout(f"Timeout: {args.sec} seconds\n\n")

    if not capture_output:
      _write_stdout("Out:\n\n")

  return_code = run_command(
    command_string,
    timeout=args.sec,
    signal_name=args.signal,
    no_output=args.no_output,
    capture_output=capture_output,
  )

  if not args.no_output:
    if not capture_output:
      _write_stdout("\n")

    _write_stdout(f"Exit code: {return_code}\n\n")

  sys.exit(return_code)


if __name__ == "__main__":
  main()
