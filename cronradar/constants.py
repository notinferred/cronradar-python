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
MAX_MONITOR_KEY_LENGTH = 100

API_KEY_ENV_VAR = "CRONRADAR_API_KEY"
DEBUG_ENV_VAR = "CRONRADAR_DEBUG"


def utf16_length(value: str) -> int:
    """Length in UTF-16 code units, the unit the server uses for its key limit."""
    return len(value.encode("utf-16-le", "surrogatepass")) // 2


def is_valid_monitor_key(monitor_key: Optional[str]) -> bool:
    """
    Validate a monitor key. Returns True if valid; logs a warning and returns False otherwise.
    """
    if monitor_key is None or not isinstance(monitor_key, str) or monitor_key.strip() == "":
        print("[CronRadar] Invalid monitor key: must be a non-empty string.", file=sys.stderr)
        return False
    length = utf16_length(monitor_key)
    if length > MAX_MONITOR_KEY_LENGTH:
        print(
            f"[CronRadar] Invalid monitor key: length {length} exceeds maximum of {MAX_MONITOR_KEY_LENGTH} characters.",
            file=sys.stderr,
        )
        return False
    return True
