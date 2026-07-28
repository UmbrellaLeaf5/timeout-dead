"""CLI stdout helpers."""

import sys


# MARK: Public API
# ------------------------------------------------


def write_stdout(text: str) -> None:
  """Write text directly to stdout and flush immediately."""

  sys.stdout.write(text)
  sys.stdout.flush()
