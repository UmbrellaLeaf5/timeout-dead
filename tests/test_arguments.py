"""Tests for CLI parsing and constants."""

import os
from pathlib import Path

import pytest

from timeout_dead.cli.arguments import parse_arguments
from timeout_dead.constants import _Const
from timeout_dead.shell import find_bash


# MARK: Argument parsing tests
# ------------------------------------------------


class TestParseArguments:
  def test_defaults(self) -> None:
    args = parse_arguments(["echo", "hello"])
    assert args.sec == 60.0
    assert args.signal == "TERM"
    assert args.no_output is False
    assert args.capture_output is False
    assert args.command == ["echo", "hello"]

  # ------------------------------------------------

  def test_custom_timeout(self) -> None:
    args = parse_arguments(["--sec", "120", "echo", "hello"])
    assert args.sec == 120.0

  # ------------------------------------------------

  def test_float_timeout(self) -> None:
    args = parse_arguments(["--sec", "2.5", "echo", "hello"])
    assert args.sec == 2.5

  # ------------------------------------------------

  def test_subsecond_timeout(self) -> None:
    args = parse_arguments(["--sec", "0.3", "sleep", "1"])
    assert args.sec == 0.3

  # ------------------------------------------------

  def test_zero_timeout(self) -> None:
    args = parse_arguments(["--sec", "0", "echo", "hello"])
    assert args.sec == 0.0

  # ------------------------------------------------

  def test_signal_option(self) -> None:
    args = parse_arguments(["--signal", "INT", "echo", "hello"])
    assert args.signal == "INT"

  # ------------------------------------------------

  def test_signal_lowercase(self) -> None:
    args = parse_arguments(["--signal", "term", "echo", "hello"])
    assert args.signal == "TERM"

  # ------------------------------------------------

  def test_no_output(self) -> None:
    args = parse_arguments(["--no-output", "echo", "hello"])
    assert args.no_output is True

  # ------------------------------------------------

  def test_capture_output(self) -> None:
    args = parse_arguments(["--capture-output", "echo", "hello"])
    assert args.capture_output is True

  # ------------------------------------------------

  def test_capture_output_short_option(self) -> None:
    args = parse_arguments(["-c", "echo", "hello"])
    assert args.capture_output is True

  # ------------------------------------------------

  def test_command_short_c_is_preserved_after_command(self) -> None:
    args = parse_arguments(["python", "-c", "print(1)"])
    assert args.capture_output is False
    assert args.command == ["python", "-c", "print(1)"]

  # ------------------------------------------------

  def test_help_ignores_invalid_options_and_missing_command(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      parse_arguments(["--sec", "invalid", "--help", "--signal", "INVALID"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "usage:" in captured.out
    assert captured.err == ""

  # ------------------------------------------------

  def test_version_ignores_invalid_options_and_missing_command(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      parse_arguments(["--sec", "invalid", "--version", "--signal", "INVALID"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out.strip() == f"timeout-dead {_Const.PROJECT_VERSION}"
    assert captured.err == ""

  # ------------------------------------------------

  def test_invalid_signal(self) -> None:
    with pytest.raises(SystemExit):
      parse_arguments(["--signal", "INVALID", "echo", "x"])

  # ------------------------------------------------

  def test_empty_command(self) -> None:
    args = parse_arguments([])
    assert args.command == []


# MARK: Platform detection tests
# ------------------------------------------------


class TestPlatform:
  def test_is_windows_type(self) -> None:
    assert isinstance(_Const.IS_WINDOWS, bool)

  # ------------------------------------------------

  def test_is_windows_consistent(self) -> None:
    assert _Const.IS_WINDOWS == (os.name == "nt")


# MARK: Bash detection tests
# ------------------------------------------------


class TestBashDetection:
  def test_find_bash_returns_string(self) -> None:
    bash = find_bash()
    assert isinstance(bash, str)
    assert "bash" in bash.lower()

  # ------------------------------------------------

  def test_find_bash_exists(self) -> None:
    bash = find_bash()
    assert Path(bash).is_file()


# MARK: Constants tests
# ------------------------------------------------


class TestConstants:
  def test_default_timeout(self) -> None:
    assert _Const.DEFAULT_TIMEOUT_S == 60.0
    assert isinstance(_Const.DEFAULT_TIMEOUT_S, float)

  # ------------------------------------------------

  def test_grace_period(self) -> None:
    assert _Const.GRACE_PERIOD_S == 1.0
    assert isinstance(_Const.GRACE_PERIOD_S, float)

  # ------------------------------------------------

  def test_signal_names(self) -> None:
    assert "TERM" in _Const.SIGNAL_NAMES
    assert "KILL" in _Const.SIGNAL_NAMES
    assert "HUP" in _Const.SIGNAL_NAMES
    assert "INT" in _Const.SIGNAL_NAMES
    assert len(_Const.SIGNAL_NAMES) == 4

  # ------------------------------------------------

  def test_project_version(self) -> None:
    version = _Const.PROJECT_VERSION
    assert isinstance(version, str)
    assert len(version) > 0
