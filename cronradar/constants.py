"""
Centralized constants for the CronRadar Python SDK.
Mirrors the .NET CronRadarConstants for cross-SDK consistency.
"""

import os
import sys
from typing import Optional


BASE_URL = "https://cron.life"
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_GRACE_PERIOD_SECONDS = 60
MAX_MONITOR_KEY_LENGTH = 200

API_KEY_ENV_VAR = "CRONRADAR_API_KEY"
DEBUG_ENV_VAR = "CRONRADAR_DEBUG"


def is_valid_monitor_key(monitor_key: Optional[str]) -> bool:
    """
    Validate a monitor key. Returns True if valid; logs a warning and returns False otherwise.
    """
    if monitor_key is None or not isinstance(monitor_key, str) or monitor_key.strip() == "":
        print("[CronRadar] Invalid monitor key: must be a non-empty string.", file=sys.stderr)
        return False
    if len(monitor_key) > MAX_MONITOR_KEY_LENGTH:
        print(
            f"[CronRadar] Invalid monitor key: length {len(monitor_key)} exceeds maximum of {MAX_MONITOR_KEY_LENGTH} characters.",
            file=sys.stderr,
        )
        return False
    return True
