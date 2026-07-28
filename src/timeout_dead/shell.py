"""Shell executable discovery."""

import shutil
import sys

from timeout_dead.constants import _Const


# MARK: Bash detection
# ------------------------------------------------


def find_bash() -> str:
  """
  Locate bash executable in PATH.

  Returns:
    str: path to the bash executable

  Raises:
    SystemExit: if bash is not found
  """

  bash_path = shutil.which(_Const.BASH_EXECUTABLE)

  if bash_path is None:
    print(f"\n{_Const.MSG_BASH_NOT_FOUND}", file=sys.stderr)
    sys.exit(_Const.EXIT_FAILURE)

  return bash_path
