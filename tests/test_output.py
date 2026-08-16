"""Tests for CLI status output."""

import pytest

from timeout_dead.cli import output
from timeout_dead.constants import _Const


class TestStatusOutput:
  def test_status_has_no_ansi_when_stderr_is_not_supported(
    self,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    monkeypatch.setattr(output, "stream_supports_ansi", lambda stream: False)

    output.write_status(_Const.STATUS_SUCCESS, _Const.ANSI_GREEN)

    captured = capsys.readouterr()
    assert captured.err == f"{_Const.STATUS_SUCCESS}\n"

  # ------------------------------------------------

  def test_status_uses_color_when_stderr_supports_ansi(
    self,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    monkeypatch.setattr(output, "stream_supports_ansi", lambda stream: True)

    output.write_status(_Const.STATUS_SUCCESS, _Const.ANSI_GREEN)

    captured = capsys.readouterr()
    assert captured.err == (f"{_Const.ANSI_GREEN}{_Const.STATUS_SUCCESS}{_Const.ANSI_RESET}\n")
