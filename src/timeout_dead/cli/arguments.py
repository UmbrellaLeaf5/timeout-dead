"""CLI argument parsing."""

import argparse
import sys

from timeout_dead.constants import _Const


# MARK: Helpers
# ------------------------------------------------


def _has_priority_option(argv: list[str], options: tuple[str, ...]) -> bool:
  """Return True if a priority option appears before COMMAND starts."""

  skip_next = False

  for arg in argv:
    if skip_next:
      skip_next = False

    elif arg == _Const.OPT_COMMAND_SEPARATOR:
      return False

    elif arg in options:
      return True

    elif arg in (_Const.OPT_SEC, _Const.OPT_SIGNAL):
      skip_next = True

    elif arg.startswith(_Const.OPT_SEC_PREFIX) or arg.startswith(_Const.OPT_SIGNAL_PREFIX):
      pass

    elif arg in (
      _Const.OPT_NO_OUTPUT,
      _Const.OPT_CAPTURE_OUTPUT_LONG,
      _Const.OPT_CAPTURE_OUTPUT_SHORT,
    ):
      pass

    elif not arg.startswith(_Const.OPT_PREFIX):
      return False

  return False


# MARK: Public API
# ------------------------------------------------


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
  """Parse command-line arguments."""

  argument_list = sys.argv[_Const.COUNT_INCREMENT :] if argv is None else argv
  parser = argparse.ArgumentParser(
    description=_Const.CLI_DESCRIPTION,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=_Const.CLI_EPILOG,
  )

  parser.add_argument(
    _Const.OPT_VERSION_SHORT,
    _Const.OPT_VERSION_LONG,
    action=_Const.ARG_ACTION_VERSION,
    version=f"{_Const.PROJECT_PACKAGE_NAME} {_Const.PROJECT_VERSION}",
  )

  parser.add_argument(
    _Const.OPT_SEC,
    type=float,
    default=_Const.DEFAULT_TIMEOUT_S,
    help=_Const.CLI_TIMEOUT_HELP.format(timeout=_Const.DEFAULT_TIMEOUT_S),
    metavar=_Const.CLI_TIMEOUT_METAVAR,
  )

  parser.add_argument(
    _Const.OPT_SIGNAL,
    type=str.upper,
    default=_Const.DEFAULT_SIGNAL_NAME,
    choices=list(_Const.SIGNAL_NAMES),
    help=_Const.CLI_SIGNAL_HELP,
    metavar=_Const.CLI_SIGNAL_METAVAR,
  )

  parser.add_argument(
    _Const.OPT_NO_OUTPUT,
    action=_Const.ARG_ACTION_STORE_TRUE,
    default=False,
    help=_Const.CLI_NO_OUTPUT_HELP,
  )

  parser.add_argument(
    _Const.OPT_CAPTURE_OUTPUT_SHORT,
    _Const.OPT_CAPTURE_OUTPUT_LONG,
    action=_Const.ARG_ACTION_STORE_TRUE,
    default=False,
    help=_Const.CLI_CAPTURE_OUTPUT_HELP,
  )

  parser.add_argument(
    _Const.ARG_DEST_COMMAND,
    nargs=argparse.REMAINDER,
    help=_Const.CLI_COMMAND_HELP,
    metavar=_Const.CLI_COMMAND_METAVAR,
  )

  if _has_priority_option(argument_list, (_Const.OPT_HELP_SHORT, _Const.OPT_HELP_LONG)):
    parser.parse_args([_Const.OPT_HELP_LONG])

  if _has_priority_option(argument_list, (_Const.OPT_VERSION_SHORT, _Const.OPT_VERSION_LONG)):
    parser.parse_args([_Const.OPT_VERSION_LONG])

  return parser.parse_args(argv)
