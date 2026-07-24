# time-d

[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://python.org)
[![uv](https://img.shields.io/badge/uv-0.5+-blueviolet?logo=python)](https://docs.astral.sh/uv/)
[![pytest](https://img.shields.io/badge/pytest-8+-cyan?logo=pytest)](https://pytest.org)
[![ruff](https://img.shields.io/badge/ruff-0.8+-black?logo=ruff)](https://docs.astral.sh/ruff/)
[![pyright](https://img.shields.io/badge/pyright-basic-orange)](https://github.com/microsoft/pyright)

<img align="right" height="256" src="icon.png"/>

**Lightweight command timeout utility with zero dependencies.** Runs any shell command with a configurable time limit and termination signal. If the command exceeds the timeout, `time-d` sends the chosen signal, waits a 1-second grace period, then force-kills the process. Works on Linux, macOS, and Windows (Git Bash / WSL).

## Features

- **Zero runtime dependencies** — pure Python standard library
- Configurable timeout in seconds
- Selectable termination signal (TERM, KILL, HUP, INT)
- Optional silent mode (`--no-output`) to suppress all normal output
- Two-stage termination: graceful signal → 1s grace → force kill
- Cross-platform: Unix process groups + Windows process handling
- Clean exit code forwarding

## Installation

Requires Python 3.10 or later.

```bash
pip install git+https://github.com/UmbrellaLeaf5/time-d
```

Or install from source:

```bash
git clone https://github.com/UmbrellaLeaf5/time-d
cd time-d
uv sync
uv pip install -e .
```

## Usage

```bash
# Run a command with default 60s timeout
time-d "python -c 'print(42)'"

# Specify a custom timeout
time-d --sec 120 "npm run build"

# Use SIGINT instead of default SIGTERM
time-d --signal INT --sec 30 "long-running-server"

# Run silently — suppress all normal output
time-d --no-output "curl -s https://example.com"
```

### Full options

```
usage: time-d [-h] [--sec SECONDS] [--signal {TERM,KILL,HUP,INT}]
              [--no-output] COMMAND ...

Lightweight command timeout utility.

positional arguments:
  COMMAND               command to execute

options:
  -h, --help            show this help message and exit
  --sec SECONDS         timeout in seconds (default: 60)
  --signal {TERM,KILL,HUP,INT}
                        signal to send on timeout (default: TERM)
  --no-output           suppress normal output (stdout, stderr, header, footer)
```

### How it works

1. `time-d` starts the command in a new process group (Unix) or as a subprocess (Windows).
2. A background timer waits for the specified timeout.
3. If the command finishes in time, its output and exit code are forwarded.
4. If the timeout expires:
   - The chosen signal is sent to the process group.
   - After 1 second, if the process is still running, `SIGKILL` (Unix) or `process.kill()` (Windows) is sent.
   - A `Timeout exceeded` message is printed to stderr.

## Development

```bash
uv sync                    # install dev dependencies (pytest)
pytest tests/ -v           # run test suite
ruff check .               # lint
ruff format --check .      # format check
pyright .                  # type check
```

## License

[Unlicense](LICENSE) — public domain.

<a href="https://www.flaticon.com/free-icons/timeout" title="timeout icons">Timeout icons created by Those Icons - Flaticon</a>
