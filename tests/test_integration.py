"""Subprocess integration tests for timeout-dead."""

import re
import shlex
import shutil
import sys
from pathlib import Path

import pytest

from tests.helpers import run_cli
from timeout_dead.constants import _Const


# MARK: Integration tests (subprocess)
# ------------------------------------------------


class TestIntegration:
  def test_cli_help(self) -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "timeout" in result.stdout.lower()
    assert "--sec" in result.stdout
    assert "--signal" in result.stdout
    assert "--no-output" in result.stdout
    assert "--capture-output" in result.stdout
    assert "--version" in result.stdout
    assert "Flag priority:" in result.stdout

  # ------------------------------------------------

  def test_cli_help_ignores_other_flags_and_missing_command(self) -> None:
    result = run_cli("--sec", "invalid", "--help", "--signal", "INVALID")
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "no command" not in result.stderr.lower()

  # ------------------------------------------------

  def test_cli_version_ignores_other_flags_and_missing_command(self) -> None:
    result = run_cli("--sec", "invalid", "--version", "--signal", "INVALID")
    assert result.returncode == 0
    assert result.stdout.strip() == f"timeout-dead {_Const.PROJECT_VERSION}"
    assert "no command" not in result.stderr.lower()

  # ------------------------------------------------

  def test_cli_version_long(self) -> None:
    result = run_cli("--version")
    assert result.returncode == 0
    assert re.match(r"timeout-dead \d+\.\d+", result.stdout)

  # ------------------------------------------------

  def test_cli_version_short(self) -> None:
    result = run_cli("-v")
    assert result.returncode == 0
    assert re.match(r"timeout-dead \d+\.\d+", result.stdout)

  # ------------------------------------------------

  def test_cli_version_matches_const(self) -> None:
    result = run_cli("--version")
    version = _Const.PROJECT_VERSION
    assert result.stdout.strip() == f"timeout-dead {version}"

  # ------------------------------------------------

  def test_cli_basic(self) -> None:
    result = run_cli("echo", "hello-integration")
    assert result.returncode == 0
    assert "hello-integration" in result.stdout

  # ------------------------------------------------

  def test_cli_failure(self) -> None:
    result = run_cli("exit", "13")
    assert result.returncode == 13

  # ------------------------------------------------

  def test_cli_timeout(self) -> None:
    result = run_cli("--sec", "1", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_no_output(self) -> None:
    result = run_cli("--no-output", "echo", "secret")
    assert result.returncode == 0
    assert "secret" not in result.stdout
    assert "Running:" not in result.stdout
    assert "Exit code" not in result.stdout

  # ------------------------------------------------

  def test_cli_no_command(self) -> None:
    result = run_cli("--sec", "10")
    assert result.returncode == 1
    assert "no command" in result.stderr.lower()

  # ------------------------------------------------

  def test_cli_with_signal_option(self) -> None:
    result = run_cli("--signal", "KILL", "--sec", "2", "echo", "signal-test")
    assert result.returncode == 0

  # ------------------------------------------------

  def test_cli_signal_int_timeout(self) -> None:
    result = run_cli("--signal", "INT", "--sec", "1", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_signal_hup_timeout(self) -> None:
    result = run_cli("--signal", "HUP", "--sec", "1", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_signal_kill_timeout(self) -> None:
    result = run_cli("--signal", "KILL", "--sec", "1", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_vim_smoke(self) -> None:
    if not shutil.which("vim"):
      pytest.skip("vim not found in PATH")
    result = run_cli("--sec", "5", "vim", "--version", timeout=30)
    assert result.returncode == 0
    assert "VIM" in result.stdout.upper()

  # ------------------------------------------------

  def test_cli_default_output_has_no_separator(self) -> None:
    result = run_cli("echo", "hello-flush")
    expected_stdout = (
      "Running: echo hello-flush\n\n"
      "Timeout: 60.0 seconds\n\n\n"
      "Out:\n\nhello-flush\n\nExit code: 0\n\n"
    )
    assert result.returncode == 0
    assert result.stdout == expected_stdout
    assert _Const.SEPARATOR not in result.stdout
    assert "Err:" not in result.stdout
    assert "Out:" in result.stdout

  # ------------------------------------------------

  def test_cli_capture_output_formats_stdout_stream(self) -> None:
    command = "printf 'alpha-capture\n'"
    result = run_cli("--capture-output", command)
    expected_stdout = (
      f"Running: {command}\n"
      "\n"
      "Timeout: 60.0 seconds\n"
      "\n\n"
      "Err:\n\n"
      "Out:\n\n"
      "alpha-capture\n\n\n"
      "Exit code: 0\n\n"
    )
    assert result.returncode == 0
    assert result.stdout == expected_stdout

  # ------------------------------------------------

  def test_cli_capture_output_formats_stderr_stream(self) -> None:
    command = "printf 'beta-capture\n' >&2"
    result = run_cli("--capture-output", command)
    assert result.returncode == 0
    assert "Err:\n\nbeta-capture" in result.stdout
    assert "Out:" in result.stdout
    assert "beta-capture" not in result.stderr

  # ------------------------------------------------

  def test_cli_capture_output_formats_streams_without_trailing_newline(self) -> None:
    command = "printf 'alpha-capture'"
    result = run_cli("--capture-output", command)
    expected_stdout = (
      f"Running: {command}\n"
      "\n"
      "Timeout: 60.0 seconds\n"
      "\n\n"
      "Err:\n\n"
      "Out:\n\n"
      "alpha-capture\n\n"
      "Exit code: 0\n\n"
    )
    assert result.returncode == 0
    assert result.stdout == expected_stdout

  # ------------------------------------------------

  def test_cli_capture_output_prints_full_output_after_tail_preview(self) -> None:
    command = (
      'python -c "'
      "import sys; "
      "[print(f'out-line-{i}') for i in range(1, 8)]; "
      "[print(f'err-line-{i}', file=sys.stderr) for i in range(1, 8)]"
      '"'
    )
    result = run_cli("--capture-output", command)
    assert result.returncode == 0
    assert "\x1b[" not in result.stdout
    assert "err-line-1" in result.stdout
    assert "err-line-7" in result.stdout
    assert "out-line-1" in result.stdout
    assert "out-line-7" in result.stdout

  # ------------------------------------------------

  def test_cli_capture_output_no_output_suppresses_normal_output(self) -> None:
    command = "printf 'alpha-capture\n'; printf 'beta-capture\n' >&2"
    result = run_cli("--no-output", "--capture-output", command)
    assert result.returncode == 0
    assert result.stdout == ""
    assert _Const.MSG_CAPTURE_IGNORED in result.stderr
    assert "alpha-capture" not in result.stderr
    assert "beta-capture" not in result.stderr

  # ------------------------------------------------

  def test_cli_capture_output_handles_undecodable_bytes(self) -> None:
    command = (
      'python -c "import sys; '
      "sys.stdout.buffer.write(bytes([0x98])); "
      'sys.stderr.buffer.write(bytes([0x98]))"'
    )
    result = run_cli("--capture-output", command)
    assert result.returncode == 0
    assert "UnicodeDecodeError" not in result.stderr
    assert "\\x98" in result.stdout

  # ------------------------------------------------

  def test_cli_capture_output_runs_example_script(self) -> None:
    script_path = Path(__file__).with_name("example_script.py")
    command = (
      f"{shlex.quote(Path(sys.executable).as_posix())} {shlex.quote(script_path.as_posix())}"
    )
    result = run_cli("--capture-output", command, timeout=45)
    assert result.returncode == 0
    assert "Err:" in result.stdout
    assert "Out:" in result.stdout
    assert "STDOUT: first line" in result.stdout
    assert "STDOUT: final line" in result.stdout
    assert "STDERR: first line" in result.stdout
    assert "STDERR: final line" in result.stdout
    assert "EXAMPLE: stdout/stderr capture demo finished" in result.stdout
    assert "UnicodeDecodeError" not in result.stderr
