"""
Core logic for the stay_awake utility.

Provides:
- prevent_sleep(): block system sleep while running
- start_daemon(): launch background process
- stop_daemon(): stop background process
- daemon_main(): internal entry point for the daemon
"""

import ctypes
import os
import signal
import subprocess
import sys
import time

# Windows API flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

# PID file location
PID_FILE = os.path.join(os.getenv("LOCALAPPDATA"), "stayawake.pid")


# ---------------------------------------------------------------------------
# Core sleep-prevention loop
# ---------------------------------------------------------------------------
def prevent_sleep(verbose: bool = False, minutes: int | None = None) -> None:
    """
    Prevent Windows from sleeping using SetThreadExecutionState.

    Args:
        verbose: Print status messages.
        minutes: Optional timer in minutes.
    """
    if verbose:
        print("StayAwake: enabling system-required state")

    # Tell Windows to keep the system awake
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    )

    end_time = time.time() + (minutes * 60) if minutes else None

    try:
        while True:
            time.sleep(60)

            if end_time and time.time() >= end_time:
                if verbose:
                    print("StayAwake: timer expired")
                break

    except KeyboardInterrupt:
        if verbose:
            print("StayAwake: interrupted by user")

    finally:
        if verbose:
            print("StayAwake: restoring normal sleep behaviour")

        # Restore normal behaviour
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


# ---------------------------------------------------------------------------
# Daemon management
# ---------------------------------------------------------------------------
def start_daemon(verbose: bool = False, minutes: int | None = None) -> None:
    """
    Start the background daemon process.

    Args:
        verbose: Print status messages.
        minutes: Optional timer in minutes.
    """
    if os.path.exists(PID_FILE):
        print("StayAwake: already running")
        return

    cmd = [sys.executable, "-m", "stay_awake", "--_daemon"]

    if verbose:
        cmd.append("-v")
    if minutes:
        cmd.extend(["-t", str(minutes)])

    try:
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)

        if minutes:
            print(f"StayAwake: enabled for {minutes} minutes")
        else:
            print("StayAwake: enabled")

    except Exception as e:
        print(f"StayAwake: failed to start daemon: {e}")



def stop_daemon() -> None:
    """
    Stop the background daemon process.
    """
    if not os.path.exists(PID_FILE):
        print("StayAwake: not running")
        return

    try:
        with open(PID_FILE) as f:
            pid = int(f.read())

        os.kill(pid, signal.SIGTERM)
        print("StayAwake: disabled")

    except Exception as e:
        print(f"StayAwake: failed to stop: {e}")

    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)


def daemon_main(verbose: bool = False, minutes: int | None = None) -> None:
    """
    Internal entry point for the background daemon.

    Args:
        verbose: Print status messages.
        minutes: Optional timer in minutes.
    """
    # Write PID so stop_daemon() can find it
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"StayAwake: failed to write PID file: {e}")
        return

    try:
        prevent_sleep(verbose=verbose, minutes=minutes)
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
