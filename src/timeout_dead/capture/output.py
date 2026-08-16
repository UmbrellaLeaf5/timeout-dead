"""Final captured output block formatting."""

from timeout_dead.capture.control import write_stdout
from timeout_dead.constants import _Const


# MARK: Block formatting
# ------------------------------------------------


def _format_output_block(title: str, text: str) -> str:
  """Format one final captured output block."""

  block = f"{title}{_Const.CAPTURE_BLOCK_GAP}"

  if not text:
    return block

  suffix = _Const.BLANK_LINE if text.endswith(_Const.NEWLINE) else _Const.CAPTURE_BLOCK_GAP
  return f"{block}{text}{suffix}"


# ------------------------------------------------


def render_final_output(stderr_text: str, stdout_text: str) -> None:
  """Print full captured stderr/stdout blocks."""

  write_stdout(_format_output_block(_Const.STDERR_TITLE, stderr_text))
  write_stdout(_format_output_block(_Const.STDOUT_TITLE, stdout_text))
