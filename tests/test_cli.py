"""Tests for timeout-dead CLI utility."""

import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from timeout_dead.cli import (
  _Const,
  _find_bash,
  _is_windows,
  main,
  parse_arguments,
  print_footer,
  print_header,
  run_command,
)


# MARK: Helpers
# ------------------------------------------------


def _run_cli(
  *args: str,
  timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
  """Run timeout-dead as a subprocess."""

  return subprocess.run(
    [sys.executable, "-m", "timeout_dead.cli", *args],
    capture_output=True,
    text=True,
    timeout=timeout,
    check=False,
  )


# MARK: Argument parsing tests
# ------------------------------------------------


class TestParseArguments:
  def test_defaults(self) -> None:
    args = parse_arguments(["echo", "hello"])
    assert args.sec == 60.0
    assert args.signal == "TERM"
    assert args.no_output is False
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
    assert isinstance(_is_windows(), bool)

  # ------------------------------------------------

  def test_is_windows_consistent(self) -> None:
    assert _is_windows() == (os.name == "nt")


# MARK: Bash detection tests
# ------------------------------------------------


class TestBashDetection:
  def test_find_bash_returns_string(self) -> None:
    bash = _find_bash()
    assert isinstance(bash, str)
    assert "bash" in bash.lower()

  # ------------------------------------------------

  def test_find_bash_exists(self) -> None:
    bash = _find_bash()
    assert os.path.isfile(bash)


# MARK: run_command tests
# ------------------------------------------------


class TestRunCommand:
  def test_successful_command(self) -> None:
    rc = run_command("echo hello")
    assert rc == 0

  # ------------------------------------------------

  def test_failing_command(self) -> None:
    rc = run_command("exit 42")
    assert rc == 42

  # ------------------------------------------------

  def test_command_with_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc = run_command('echo "test output"')
    captured = capsys.readouterr()
    assert rc == 0
    assert "test output" in captured.out

  # ------------------------------------------------

  def test_command_with_stderr(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc = run_command("echo error >&2")
    captured = capsys.readouterr()
    assert rc == 0
    assert "error" in captured.err

  # ------------------------------------------------

  def test_no_output_suppresses_stdout(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc = run_command('echo "hidden output"', no_output=True)
    captured = capsys.readouterr()
    assert rc == 0
    assert "hidden output" not in captured.out

  # ------------------------------------------------

  def test_no_output_suppresses_stderr(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc = run_command("echo hidden >&2", no_output=True)
    captured = capsys.readouterr()
    assert rc == 0
    assert "hidden" not in captured.err

  # MARK: Timeout tests
  # ------------------------------------------------

  def test_timeout_kills_process(self) -> None:
    rc = run_command("sleep 10", timeout=1)
    assert rc != 0

  # ------------------------------------------------

  def test_timeout_message(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    run_command("sleep 10", timeout=1)
    captured = capsys.readouterr()
    assert "Timeout exceeded" in captured.err

  # ------------------------------------------------

  def test_timeout_message_even_with_no_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    run_command("sleep 10", timeout=1, no_output=True)
    captured = capsys.readouterr()
    assert "Timeout exceeded" in captured.err

  # ------------------------------------------------

  def test_grace_period(self) -> None:
    start = time.monotonic()
    rc = run_command("sleep 10", timeout=1)
    elapsed = time.monotonic() - start
    assert elapsed < 4.0
    assert rc != 0


# MARK: Float timeout tests
# ------------------------------------------------


class TestFloatTimeout:
  def test_float_parsed_correctly(self) -> None:
    rc = run_command("echo ok", timeout=2.5)
    assert rc == 0

  # ------------------------------------------------

  def test_subsecond_timeout_triggers(self) -> None:
    rc = run_command("sleep 10", timeout=0.3)
    assert rc != 0

  # ------------------------------------------------

  def test_millisecond_timeout(self) -> None:
    start = time.monotonic()
    rc = run_command("sleep 10", timeout=0.5)
    elapsed = time.monotonic() - start
    assert rc != 0
    assert elapsed < 4.0

  # ------------------------------------------------

  def test_float_in_message(self, capsys: pytest.CaptureFixture[str]) -> None:
    run_command("sleep 10", timeout=1.5)
    captured = capsys.readouterr()
    assert "Timeout exceeded" in captured.err

  # ------------------------------------------------

  def test_cli_float_arg(self) -> None:
    result = _run_cli("--sec", "0.3", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_float_with_signal(self) -> None:
    result = _run_cli("--sec", "0.5", "--signal", "KILL", "sleep", "10")
    assert result.returncode != 0

  # ------------------------------------------------

  def test_cli_float_no_output(self) -> None:
    result = _run_cli("--no-output", "--sec", "0.3", "sleep", "10")
    assert "Timeout exceeded" in result.stderr
    assert "Running:" not in result.stdout


# MARK: Windows Job Object tests
# ------------------------------------------------


class TestJobObject:
  def test_force_kill_terminates_process_tree(self) -> None:
    """On Windows, force-kill via Job Object kills bash and all children."""
    rc = run_command("sleep 10 & sleep 10 & wait", timeout=1)
    assert rc != 0

  # ------------------------------------------------

  def test_graceful_then_force_kill(self) -> None:
    """Graceful CTRL_BREAK_EVENT first, then Job Object force-kill."""

    start = time.monotonic()
    rc = run_command("sleep 10 & sleep 10 & wait", timeout=1)
    elapsed = time.monotonic() - start
    assert rc != 0
    assert elapsed < 5.0

  # ------------------------------------------------

  def test_cli_force_kill_tree(self) -> None:
    """CLI: force-kill kills process tree."""

    result = _run_cli(
      "--sec",
      "1",
      "bash",
      "-c",
      "sleep 10 & sleep 10 & wait",
    )
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_no_output_job_object(self) -> None:
    """--no-output + Job Object force-kill shows timeout message."""

    result = _run_cli("--no-output", "--sec", "0.5", "sleep", "10")
    assert "Timeout exceeded" in result.stderr
    assert "Running:" not in result.stdout


# ------------------------------------------------


class TestSignalSelection:
  def test_signal_map_covers_names(self) -> None:
    for name in _Const.SIGNAL_NAMES:
      assert name in _Const.SIGNAL_MAP
    assert len(_Const.SIGNAL_MAP) == len(_Const.SIGNAL_NAMES)

  # ------------------------------------------------

  def test_signal_term_is_default(self) -> None:
    assert _Const.SIGNAL_MAP["TERM"] == signal.SIGTERM

  # ------------------------------------------------

  def test_signal_kill_is_valid(self) -> None:
    kill_val = _Const.SIGNAL_MAP["KILL"]
    assert kill_val > 0

  # ------------------------------------------------

  @pytest.mark.skipif(
    _is_windows(),
    reason="SIGINT file-based test requires Unix signal handling",
  )
  def test_signal_int_handling(self, tmp_path: Path) -> None:
    """Python script catches SIGINT and writes signal number to file."""

    marker = tmp_path / "signal.txt"
    script_path = tmp_path / "handler.py"
    script_path.write_text(
      textwrap.dedent(f"""
      import signal
      import sys

      def handler(sig, frame):
          with open({str(marker)!r}, "w") as f:
              f.write(str(sig))
          sys.exit(0)

      signal.signal(signal.SIGINT, handler)
      import time
      time.sleep(30)
      """).strip()
    )

    run_command(
      f'python "{script_path}"',
      timeout=1,
      signal_name="INT",
    )

    assert marker.exists()
    assert marker.read_text().strip() == str(signal.SIGINT.value)

  # ------------------------------------------------

  def test_signal_hup_terminates(self) -> None:
    rc = run_command("sleep 10", timeout=1, signal_name="HUP")
    assert rc != 0

  # ------------------------------------------------

  def test_run_command_unknown_signal_defaults_to_term(self) -> None:
    rc = run_command("sleep 10", timeout=1, signal_name="UNKNOWN")
    assert rc != 0


# MARK: --no-output tests
# ------------------------------------------------


class TestNoOutput:
  def test_header_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    print_header("test cmd", 60)
    captured = capsys.readouterr()
    assert "Running:" in captured.out

  # ------------------------------------------------

  def test_footer_output(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    print_footer(0)
    captured = capsys.readouterr()
    assert "Exit code" in captured.out


# MARK: main() tests
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
  ) -> None:
    with pytest.raises(SystemExit) as exc_info:
      main(["echo", "hello"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "hello" in captured.out

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
    assert "Exit code" not in captured.out

  # ------------------------------------------------

  def test_main_no_output_still_shows_timeout(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    with pytest.raises(SystemExit):
      main(["--no-output", "--sec", "1", "sleep", "10"])
    captured = capsys.readouterr()
    assert "Timeout exceeded" in captured.err

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


# MARK: Integration tests (subprocess)
# ------------------------------------------------


class TestIntegration:
  def test_cli_help(self) -> None:
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "timeout" in result.stdout.lower()
    assert "--sec" in result.stdout
    assert "--signal" in result.stdout
    assert "--no-output" in result.stdout
    assert "--version" in result.stdout

  # ------------------------------------------------

  def test_cli_version_long(self) -> None:
    result = _run_cli("--version")
    assert result.returncode == 0
    assert "timeout-dead" in result.stdout

  # ------------------------------------------------

  def test_cli_version_short(self) -> None:
    result = _run_cli("-v")
    assert result.returncode == 0
    assert "timeout-dead" in result.stdout

  # ------------------------------------------------

  def test_cli_basic(self) -> None:
    result = _run_cli("echo", "hello-integration")
    assert result.returncode == 0
    assert "hello-integration" in result.stdout

  # ------------------------------------------------

  def test_cli_failure(self) -> None:
    result = _run_cli("exit", "13")
    assert result.returncode == 13

  # ------------------------------------------------

  def test_cli_timeout(self) -> None:
    result = _run_cli("--sec", "1", "sleep", "10")
    assert result.returncode != 0
    assert "Timeout exceeded" in result.stderr

  # ------------------------------------------------

  def test_cli_no_output(self) -> None:
    result = _run_cli("--no-output", "echo", "secret")
    assert result.returncode == 0
    assert "secret" not in result.stdout
    assert "Running:" not in result.stdout
    assert "Exit code" not in result.stdout

  # ------------------------------------------------

  def test_cli_no_command(self) -> None:
    result = _run_cli("--sec", "10")
    assert result.returncode == 1
    assert "no command" in result.stderr.lower()

  # ------------------------------------------------

  def test_cli_with_signal_option(self) -> None:
    result = _run_cli("--signal", "KILL", "--sec", "2", "echo", "signal-test")
    assert result.returncode == 0


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

  def test_header_separator_length(self) -> None:
    assert len(_Const.HEADER_SEPARATOR) == 50
