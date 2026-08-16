"""Tests for command runner behavior."""

import signal
import textwrap
import time
from pathlib import Path

import pytest

from tests.helpers import run_cli
from timeout_dead.constants import _Const
from timeout_dead.runner import run_command


# MARK: Run command tests
# ------------------------------------------------


class TestRunCommand:
  def test_successful_command(self) -> None:
    rc, timed_out = run_command("echo hello")
    assert rc == 0
    assert timed_out is False

  # ------------------------------------------------

  def test_failing_command(self) -> None:
    rc, timed_out = run_command("exit 42")
    assert rc == 42
    assert timed_out is False

  # ------------------------------------------------

  def test_no_output_suppresses_stdout(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc, timed_out = run_command('echo "hidden output"', no_output=True)
    captured = capsys.readouterr()
    assert rc == 0
    assert timed_out is False
    assert "hidden output" not in captured.out

  # ------------------------------------------------

  def test_no_output_suppresses_stderr(
    self,
    capsys: pytest.CaptureFixture[str],
  ) -> None:
    rc, timed_out = run_command("echo hidden >&2", no_output=True)
    captured = capsys.readouterr()
    assert rc == 0
    assert timed_out is False
    assert "hidden" not in captured.err

  # MARK: Timeout tests
  # ------------------------------------------------

  def test_timeout_kills_process(self) -> None:
    rc, timed_out = run_command("sleep 10", timeout=1)
    assert rc != 0
    assert timed_out is True

  # ------------------------------------------------

  def test_timeout_outcome_with_no_output(self) -> None:
    _, timed_out = run_command("sleep 10", timeout=1, no_output=True)
    assert timed_out is True

  # ------------------------------------------------

  def test_grace_period(self) -> None:
    start = time.monotonic()
    rc, timed_out = run_command("sleep 10", timeout=1)
    elapsed = time.monotonic() - start
    assert elapsed < 4.0
    assert rc != 0
    assert timed_out is True


# MARK: Float timeout tests
# ------------------------------------------------


class TestFloatTimeout:
  def test_float_parsed_correctly(self) -> None:
    rc, timed_out = run_command("echo ok", timeout=2.5)
    assert rc == 0
    assert timed_out is False

  # ------------------------------------------------

  def test_subsecond_timeout_triggers(self) -> None:
    rc, timed_out = run_command("sleep 10", timeout=0.3)
    assert rc != 0
    assert timed_out is True

  # ------------------------------------------------

  def test_millisecond_timeout(self) -> None:
    start = time.monotonic()
    rc, timed_out = run_command("sleep 10", timeout=0.5)
    elapsed = time.monotonic() - start
    assert rc != 0
    assert timed_out is True
    assert elapsed < 4.0

  # ------------------------------------------------

  def test_float_timeout_outcome(self) -> None:
    _, timed_out = run_command("sleep 10", timeout=1.5)
    assert timed_out is True

  # ------------------------------------------------

  def test_cli_float_arg(self) -> None:
    result = run_cli("--sec", "0.3", "sleep", "10")
    assert result.returncode != 0
    assert "Timed out after 0.3 seconds" in result.stderr

  # ------------------------------------------------

  def test_cli_float_with_signal(self) -> None:
    result = run_cli("--sec", "0.5", "--signal", "KILL", "sleep", "10")
    assert result.returncode != 0

  # ------------------------------------------------

  def test_cli_float_no_output(self) -> None:
    result = run_cli("--no-output", "--sec", "0.3", "sleep", "10")
    assert "Timed out after 0.3 seconds" in result.stderr
    assert "Running:" not in result.stdout
    assert "Exit code:" in result.stdout


# MARK: Windows Job Object tests
# ------------------------------------------------


class TestJobObject:
  def test_force_kill_terminates_process_tree(self) -> None:
    """On Windows, force-kill via Job Object kills bash and all children."""
    rc, timed_out = run_command("sleep 10 & sleep 10 & wait", timeout=1)
    assert rc != 0
    assert timed_out is True

  # ------------------------------------------------

  def test_graceful_then_force_kill(self) -> None:
    """Graceful CTRL_BREAK_EVENT first, then Job Object force-kill."""

    start = time.monotonic()
    rc, timed_out = run_command("sleep 10 & sleep 10 & wait", timeout=1)
    elapsed = time.monotonic() - start
    assert rc != 0
    assert timed_out is True
    assert elapsed < 5.0

  # ------------------------------------------------

  def test_cli_force_kill_tree(self) -> None:
    """CLI: force-kill kills process tree."""

    result = run_cli(
      "--sec",
      "1",
      "bash",
      "-c",
      "sleep 10 & sleep 10 & wait",
    )
    assert result.returncode != 0
    assert "Timed out after 1.0 seconds" in result.stderr

  # ------------------------------------------------

  def test_no_output_job_object(self) -> None:
    """--no-output + Job Object force-kill shows timeout message."""

    result = run_cli("--no-output", "--sec", "0.5", "sleep", "10")
    assert "Timed out after 0.5 seconds" in result.stderr
    assert "Running:" not in result.stdout
    assert "Exit code:" in result.stdout


# MARK: Signal selection tests
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
    _Const.IS_WINDOWS,
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
    rc, timed_out = run_command("sleep 10", timeout=1, signal_name="HUP")
    assert rc != 0
    assert timed_out is True

  # ------------------------------------------------

  def test_run_command_unknown_signal_defaults_to_term(self) -> None:
    rc, timed_out = run_command("sleep 10", timeout=1, signal_name="UNKNOWN")
    assert rc != 0
    assert timed_out is True
