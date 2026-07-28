"""Tests for captured output preview rendering."""

from queue import Queue

import pytest

from timeout_dead import capture
from timeout_dead.capture import control, preview, stream


# MARK: Capture rendering tests
# ------------------------------------------------


class TestCaptureRendering:
  def test_preview_frame_keeps_titles_on_separate_lines(self) -> None:
    frame = capture.format_preview_frame(
      "err-without-newline",
      "out-without-newline",
      80,
    )
    lines = frame.splitlines()
    assert lines[0] == f"Err:{capture.CLEAR_LINE}"
    assert lines[2] == f"err-without-newline{capture.CLEAR_LINE}"
    assert lines[8] == f"Out:{capture.CLEAR_LINE}"
    assert lines[10] == f"out-without-newline{capture.CLEAR_LINE}"
    assert len(lines) == capture.PREVIEW_FRAME_LINES

  # ------------------------------------------------

  def test_preview_frame_limits_tail_lines_and_width(self) -> None:
    text = "\n".join(
      [
        "line-1",
        "line-2",
        "line-3",
        "line-4",
        "line-5",
        "line-6",
        "line-7-with-long-suffix",
      ]
    )
    frame = capture.format_preview_frame(text, "", 12)
    assert "line-1" not in frame
    assert "line-2" not in frame
    assert "line-3" in frame
    assert "line-6" in frame
    assert "line-7-wi..." in frame
    assert "\x1b[J" not in frame

    for line in frame.splitlines():
      assert len(line.removesuffix(capture.CLEAR_LINE)) <= 12

  # ------------------------------------------------

  def test_live_preview_redraw_uses_one_atomic_write(
    self,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    writes: list[str] = []
    monkeypatch.setattr(preview, "write_stdout", writes.append)
    rendered_lines = capture.render_live_tail("err", "out", capture.PREVIEW_FRAME_LINES)
    assert rendered_lines == capture.PREVIEW_FRAME_LINES
    assert len(writes) == 1
    assert writes[0].startswith(f"\x1b[{capture.PREVIEW_FRAME_LINES}FErr:")
    assert "\x1b[J" not in writes[0]

  # ------------------------------------------------

  def test_live_preview_throttles_character_redraws(
    self,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    output_queue: Queue[tuple[str, str | None]] = Queue()

    for char in "abcdef":
      output_queue.put(("Out:", char))

    output_queue.put(("Out:", None))
    output_queue.put(("Err:", None))

    writes: list[str] = []
    monkeypatch.setattr(control, "write_stdout", writes.append)
    monkeypatch.setattr(preview, "write_stdout", writes.append)
    monkeypatch.setattr(stream.time, "monotonic", lambda: 1.0)
    stderr_text, stdout_text = capture.collect_captured_output(
      output_queue,
      2,
      live_preview=True,
    )
    redraw_count = sum("Err:" in write for write in writes)
    assert stderr_text == ""
    assert stdout_text == "abcdef"
    assert redraw_count == 1
    assert capture.HIDE_CURSOR in writes
    assert writes[-1] == capture.SHOW_CURSOR

  # ------------------------------------------------

  def test_live_preview_restores_cursor_after_error(
    self,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    output_queue: Queue[tuple[str, str | None]] = Queue()
    writes: list[str] = []
    monkeypatch.setattr(control, "write_stdout", writes.append)
    monkeypatch.setattr(preview, "write_stdout", writes.append)
    monkeypatch.setattr(output_queue, "get", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError):
      capture.collect_captured_output(
        output_queue,
        2,
        live_preview=True,
      )

    assert capture.HIDE_CURSOR in writes
    assert writes[-1] == capture.SHOW_CURSOR
