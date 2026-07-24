#!/usr/bin/env python3

"""
Script to run console commands with timeout via bash
Usage: uv run timeouted.py --sec 60 <command>
"""

import subprocess
import sys
import os
import signal
import time
import argparse
import threading
import shutil
from typing import Optional, Tuple


def _find_bash() -> str:
    """Find bash executable in PATH."""
    bash = shutil.which("bash")
    if bash is None:
        print("\nbash not found in PATH — Git Bash is required", file=sys.stderr)
        sys.exit(1)
    return bash


def _is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt"


def _terminate_process(process: subprocess.Popen, force: bool = False) -> None:
    """Terminate process gracefully or forcefully."""
    if process.poll() is not None:
        return
        
    try:
        if _is_windows():
            if force:
                process.kill()
            else:
                process.terminate()
        else:
            pgid = os.getpgid(process.pid)
            if force:
                os.killpg(pgid, signal.SIGKILL)
            else:
                os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass


def _kill_with_timeout(process: subprocess.Popen, timeout: int) -> None:
    """Kill process after timeout with grace period."""
    if process.poll() is not None:
        return
        
    _terminate_process(process, force=False)
    time.sleep(1)
    
    if process.poll() is None:
        _terminate_process(process, force=True)
    
    print(f"\nTimeout exceeded {timeout} seconds", file=sys.stderr)


def run_command(command_string: str, timeout: int = 60) -> int:
    """
    Run command with timeout via bash.
    
    Args:
        command_string: Command to execute
        timeout: Timeout in seconds
    
    Returns:
        Process return code
    """
    process: Optional[subprocess.Popen] = None
    timer: Optional[threading.Timer] = None
    
    try:
        # Start process
        process = subprocess.Popen(
            [_find_bash(), "-c", command_string],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=None if _is_windows() else os.setsid,
        )
        
        # Set up timeout timer
        timer = threading.Timer(
            timeout, 
            _kill_with_timeout, 
            args=(process, timeout)
        )
        timer.start()
        
        # Wait for completion
        stdout, stderr = process.communicate()
        timer.cancel()
        
        # Output results
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)
            
        return process.returncode
        
    except Exception as e:
        # Cleanup on error
        if timer:
            timer.cancel()
        if process and process.poll() is None:
            try:
                _terminate_process(process, force=True)
            except Exception:
                pass
                
        print(f"Execution error: {e}", file=sys.stderr)
        return -1


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run command with timeout via bash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--sec",
        type=int,
        default=60,
        help="Timeout in seconds (default: 60)",
        metavar="SECONDS",
    )
    
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute",
        metavar="COMMAND",
    )
    
    return parser.parse_args()


def print_header(command: str, timeout: int) -> None:
    """Print execution header."""
    print(f"Running: {command}")
    print(f"Timeout: {timeout} seconds")
    print("-" * 60)


def print_footer(return_code: int) -> None:
    """Print execution footer."""
    print("-" * 60)
    print(f"Exit code: {return_code}")


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    if not args.command:
        print("Error: no command specified", file=sys.stderr)
        sys.exit(1)
    
    command_string = " ".join(args.command)
    print_header(command_string, args.sec)
    
    return_code = run_command(command_string, args.sec)
    
    print_footer(return_code)
    sys.exit(return_code)


if __name__ == "__main__":
    main()
