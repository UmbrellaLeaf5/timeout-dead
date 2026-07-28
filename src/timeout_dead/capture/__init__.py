"""Captured output rendering public API."""

from timeout_dead.capture.control import write_stdout
from timeout_dead.capture.preview import format_preview_frame, render_live_tail
from timeout_dead.capture.stream import collect_captured_output, stream_captured_output
from timeout_dead.constants import _Const


CLEAR_LINE = _Const.CLEAR_LINE
HIDE_CURSOR = _Const.HIDE_CURSOR
LIVE_RENDER_INTERVAL_S = _Const.LIVE_RENDER_INTERVAL_S
PREVIEW_FRAME_LINES = _Const.PREVIEW_FRAME_LINES
SHOW_CURSOR = _Const.SHOW_CURSOR
TAIL_LINE_COUNT = _Const.TAIL_LINE_COUNT

__all__ = [
  "CLEAR_LINE",
  "HIDE_CURSOR",
  "LIVE_RENDER_INTERVAL_S",
  "PREVIEW_FRAME_LINES",
  "SHOW_CURSOR",
  "TAIL_LINE_COUNT",
  "collect_captured_output",
  "format_preview_frame",
  "render_live_tail",
  "stream_captured_output",
  "write_stdout",
]
