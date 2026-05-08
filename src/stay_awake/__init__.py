"""
stay_awake package — Windows sleep prevention utility.
"""

from .stay_awake import prevent_sleep, start_daemon, stop_daemon

__all__ = ["prevent_sleep", "start_daemon", "stop_daemon"]

VERSION = "1.0.0"
