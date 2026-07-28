# timeout-dead

[![PyPI version](https://img.shields.io/pypi/v/timeout-dead)](https://pypi.org/project/timeout-dead/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue)](https://github.com/UmbrellaLeaf5/timeout-dead)
[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)
[![Tests](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/tests.yml/badge.svg)](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/tests.yml)
[![Ruff](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/ruff.yml/badge.svg)](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/ruff.yml)
[![Pyright](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/pyright.yml/badge.svg)](https://github.com/UmbrellaLeaf5/timeout-dead/actions/workflows/pyright.yml)

<img align="right" height="256" src="icon.png"/>

**Lightweight command timeout utility with zero runtime dependencies.**
Runs any shell command with a configurable time limit and termination signal.
If the command exceeds the timeout, `timeout-dead` sends the chosen signal,
waits a 1-second grace period, then force-kills the process.
Fully cross-platform — Linux, macOS, and Windows (Git Bash / WSL).

## Installation

```bash
pip install timeout-dead
```

Or via uv:

```bash
uv tool install timeout-dead
```

Requires Python 3.10 or later. Zero runtime dependencies — pure Python standard library.

## Quick start

```bash
# Run a command with default 60s timeout
timeout-dead "python -c 'print(42)'"

# Short alias also works
time-d "echo hello"

# Specify a custom timeout
timeout-dead --sec 120 "npm run build"

# Sub-second timeouts work too
timeout-dead --sec 0.5 "potentially-hanging-tool"

# Use SIGINT instead of default SIGTERM
timeout-dead --signal INT --sec 30 "long-running-server"

# Run silently — suppress all normal output
timeout-dead --no-output "curl -s https://example.com"

# Capture stderr/stdout with a five-line live tail preview
timeout-dead --capture-output "git diff --stat"

# Run the bundled stdout/stderr demo script with live capture
time-d --capture-output "python tests/example_script.py"
```

## Usage

```
usage: timeout-dead [-h] [-v] [--sec SECONDS] [--signal SIGNAL] [--no-output]
                    [-c] COMMAND ...

Lightweight command timeout utility.

positional arguments:
  COMMAND               command to execute

options:
  -h, --help            show this help message and exit
  -v, --version         show version and exit
  --sec SECONDS         timeout in seconds (default: 60.0, accepts floats)
  --signal SIGNAL       signal to send on timeout (TERM, KILL, HUP, INT)
  --no-output           suppress normal output and override --capture-output
  -c, --capture-output  capture and format stdout/stderr blocks
```

Default output format:

```text
Running: git status --short --branch
Timeout: 60.0 seconds

Out:

<command output>

Exit code: 0
```

Captured final output format (`--capture-output`):

```text
Running: git status --short --branch
Timeout: 60.0 seconds

Err:

<stderr text>

Out:

<stdout text>

Exit code: 0
```

In capture mode, `timeout-dead` reads stdout and stderr concurrently while the command is
still running. When stdout is an interactive terminal, the `Err:` and `Out:` blocks are
redrawn as a live tail preview: only the last 5 stderr lines and last 5 stdout lines are
shown, so large output does not scroll the whole screen. After the command exits, the
preview is cleared and the complete stderr/stdout text is printed in the final format
shown above.

The live preview uses a fixed-height local frame and throttled redraws to reduce flicker
on fast character-by-character output. The terminal cursor is hidden while the preview is
active and restored when the command completes, fails, or is interrupted.

When stdout is redirected or captured by CI/test tools, output stays plain text with no
ANSI control sequences. In that mode, `timeout-dead` prints the same complete final blocks
after the command exits.

The default mode intentionally does not capture streams. It inherits the terminal handles
so interactive and TUI programs such as `vim`, `less`, REPLs, Gradle progress output, and
similar tools continue to behave normally. Use `--capture-output` only when you need
separated stdout/stderr blocks in logs or tests.

To see a longer mixed stdout/stderr example locally:

```bash
time-d --capture-output "python tests/example_script.py"
```

Flag priority:

1. `-h` / `--help` and `-v` / `--version` exit immediately and ignore all other arguments.
2. `--sec` and `--signal` apply whenever a command is executed.
3. `--no-output` suppresses all normal output and has priority over `--capture-output`.
4. `--capture-output` is enabled only when `--no-output` is not set.
5. `COMMAND` is required unless `-h` / `--help` or `-v` / `--version` is used.

## How it works

1. `timeout-dead` starts the command in a new process group (Unix) / console group (Windows).
2. A background timer waits for the specified timeout.
3. If the command finishes in time, its output and exit code are forwarded.
4. If the timeout expires:
   - The chosen signal is sent to the process group.
   - After 1 second, if the process is still running, `SIGKILL` (Unix) or `process.kill()` (Windows) is sent.
   - A `Timeout exceeded` message is printed to stderr.

> **Windows signal note:** On Windows, `CTRL_BREAK_EVENT` (used for `TERM` and `HUP`) is sent to the main process only — child processes may not receive it. They will be force-killed after the 1-second grace period. For critical cleanup, use `KILL` or ensure the parent handles cleanup.

> **Process group note:** Processes that explicitly detach from their process group (e.g., via `setsid` or `nohup`) may not be terminated. Even `KILL` may not reach processes that have created a new session.

## Cross-platform

Zero code changes between platforms. `timeout-dead` detects the OS at startup and
uses the native termination strategy:

| OS      | Process isolation           | Graceful signal    | Force kill                 |
| ------- | --------------------------- | ------------------ | -------------------------- |
| Linux   | `setsid()` process group    | `SIGTERM`          | `SIGKILL` via `killpg()`   |
| macOS   | `setsid()` process group    | `SIGTERM`          | `SIGKILL` via `killpg()`   |
| Windows | Job Object (`kernel32.dll`) | `CTRL_BREAK_EVENT` | `taskkill /T /F` + Job close |

Tested on all three platforms in CI.

## Signal reference

| Signal | Unix                                  | Windows                            |
| ------ | ------------------------------------- | ---------------------------------- |
| `TERM` | `SIGTERM` (15) — terminate gracefully | `CTRL_BREAK_EVENT` — console break |
| `KILL` | `SIGKILL` (9) — force kill            | Falls back to `TerminateProcess`   |
| `HUP`  | `SIGHUP` (1) — hangup                 | Falls back to `TerminateProcess`   |
| `INT`  | `SIGINT` (2) — interrupt (Ctrl+C)     | `CTRL_C_EVENT` — console interrupt |

## Why `subprocess` timeout is not enough

Python's built-in `subprocess` timeout only kills the direct child, not its entire process tree. If your command spawns subprocesses (`npm install`, `make`, `docker build`), children survive the parent kill.

`timeout-dead` uses **process groups** to terminate everything — every subprocess, pipeline, and child.

## Real-world scenarios

| Scenario         | Command                   | Why it hangs                                            | `timeout-dead`                                           |
| ---------------- | ------------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| Gradle build     | `./gradlew build`         | 20+ min fresh build, agent generates duplicate commands | `timeout-dead --sec 600 "./gradlew build"`               |
| CMake build      | `cmake --build .`         | Locks waiting for dependency resolution                 | `timeout-dead --sec 180 "cmake --build ."`               |
| Spring Boot      | `./gradlew bootRun`       | Server never exits, agent won't proceed                 | `timeout-dead --sec 30 --signal INT "./gradlew bootRun"` |
| Docker build     | `docker build -t myapp .` | Network timeout, internal retries, no progress          | `timeout-dead --sec 600 "docker build -t myapp ."`       |
| npm install      | `npm install`             | Corrupted cache or registry auth hang                   | `timeout-dead --sec 300 "npm install"`                   |
| Interactive REPL | `python` / `node` / `irb` | Waits for input, agent doesn't know                     | `timeout-dead --sec 5 "python"`                          |
| Interactive REPL | `vim` / `nano` / `less`   | May leave terminal echo disabled after kill             | `timeout-dead --sec 10 --signal INT "vim"`               |

## For AI agents

If you build agents that execute shell commands, `timeout-dead` is essential infrastructure. Agents frequently generate commands that hang — waiting for input, entering infinite loops, or starting interactive programs.

Instead of agents freezing indefinitely, wrap every command:

```bash
timeout-dead --sec <timeout> --signal <signal> "<command>"
```

No dependencies, no code changes. Agent always gets a response — exit code + output — and can implement retry, fallback, or user notification.

## Development

```bash
git clone https://github.com/UmbrellaLeaf5/timeout-dead
cd timeout-dead
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/timeout_dead/ tests/
uv run ruff format --check .
uv run pyright src/timeout_dead/
```

## License

[Unlicense](LICENSE) — public domain.

<a href="https://www.flaticon.com/free-icons/timeout" title="timeout icons">Timeout icons created by pocike - Flaticon</a>
