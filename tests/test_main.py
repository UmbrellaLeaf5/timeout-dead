"""Tests for direct main() invocation."""

import pytest

import timeout_dead.main as main_module
from timeout_dead.constants import _Const
from timeout_dead.main import main


# MARK: No-output tests
# ------------------------------------------------


class TestNoOutput:
  def test_header_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit):
      main(["echo", "hello"])
    captured = capsys.readouterr()
    assert "Running:" in captured.out

  # ------------------------------------------------

  def test_footer_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit):
      main(["echo", "hello"])
    captured = capsys.readouterr()
    assert "Exit code" in captured.out


# MARK: Main tests
# ------------------------------------------------


class TestMain:
  def test_main_no_command_prints_error(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["--sec", "10"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert _Const.MSG_NO_COMMAND in captured.err

  # ------------------------------------------------

  def test_main_success(
    self,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    def run_command(*args: object, **kwargs: object) -> tuple[int, bool]:
      print("hello")
      return 0, False

    monkeypatch.setattr(main_module, "run_command", run_command)

    with pytest.raises(SystemExit) as exc_info:
      main(["echo", "hello"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "hello" in captured.out
    assert "hello\n\n\nExit code: 0" in captured.out
    assert _Const.STATUS_SUCCESS in captured.err

  # ------------------------------------------------

  def test_main_no_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["--no-output", "echo", "hidden"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "hidden" not in captured.out
    assert "Running:" not in captured.out
    assert "Exit code: 0" in captured.out
    assert _Const.STATUS_SUCCESS in captured.err

  # ------------------------------------------------

  def test_main_no_output_still_shows_timeout(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit):
      main(["--no-output", "--sec", "1", "sleep", "10"])
    captured = capsys.readouterr()
    assert "Timed out after 1.0 seconds" in captured.err
    assert "Exit code:" in captured.out

  # ------------------------------------------------

  def test_main_failure_exit_code(self) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["exit", "7"])
    assert exc_info.value.code == 7

  # ------------------------------------------------

  def test_main_with_signal_option(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["--signal", "KILL", "--sec", "2", "echo", "ok"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "ok" in captured.out

  # ------------------------------------------------

  def test_main_zero_timeout_exits_with_error(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["--sec", "0", "echo", "hello"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert _Const.MSG_TIMEOUT_POSITIVE in captured.err

  # ------------------------------------------------

  def test_main_negative_timeout_exits_with_error(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["--sec", "-5", "echo", "hello"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert _Const.MSG_TIMEOUT_POSITIVE in captured.err
