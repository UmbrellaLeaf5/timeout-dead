"""Shared test helpers."""

import subprocess
import sys


# MARK: CLI helpers
# ------------------------------------------------


def run_cli(
  *args: str,
  timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
  """Run timeout-dead as a subprocess."""

  return subprocess.run(
    [sys.executable, "-m", "timeout_dead.main", *args],
    capture_output=True,
    text=True,
    timeout=timeout,
    check=False,
  )
