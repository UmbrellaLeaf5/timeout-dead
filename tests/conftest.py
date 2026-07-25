"""Shared fixtures for timeout-dead tests."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Iterator[Path]:
  """Temporary directory for tests."""

  with tempfile.TemporaryDirectory() as tmp:
    yield Path(tmp)
