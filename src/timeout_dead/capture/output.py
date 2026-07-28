"""Final captured output block formatting."""

from timeout_dead.capture.control import write_stdout
from timeout_dead.constants import _Const


# MARK: Block formatting
# ------------------------------------------------


def _format_output_block(title: str, text: str) -> str:
  """Format one final captured output block."""

  block = f"{title}{_Const.BLANK_LINE}"

  if not text:
    return block

  block += text

  if text.endswith(_Const.NEWLINE):
    return f"{block}{_Const.NEWLINE}"

  return f"{block}{_Const.BLANK_LINE}"


# ------------------------------------------------


def render_final_output(stderr_text: str, stdout_text: str) -> None:
  """Print full captured stderr/stdout blocks."""

  write_stdout(_format_output_block(_Const.STDERR_TITLE, stderr_text))
  write_stdout(_format_output_block(_Const.STDOUT_TITLE, stdout_text))
