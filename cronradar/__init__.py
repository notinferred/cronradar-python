"""
CronRadar Python SDK

Dead-simple cron job monitoring with auto-registration support.
Two main functions: ping() for execution confirmation, sync_monitor() for registration.
"""

import os
import sys
import base64
import json
import traceback
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


__version__ = "0.0.3"


def ping(monitor_key: str, schedule: Optional[str] = None) -> None:
    """
    Ping CronRadar to indicate your job has run successfully.
    Optionally provide schedule for self-healing (auto-registration on 404).

    Args:
        monitor_key: The monitor key identifying your job
        schedule: Optional cron schedule for auto-registration if monitor doesn't exist

    Returns:
        None

    Raises:
        Never throws - all errors are suppressed to protect job execution
    """
    try:
        api_key = os.environ.get('CRONRADAR_API_KEY', '')
        if not api_key:
            print(f"[CronRadar] Warning: CRONRADAR_API_KEY environment variable not set. Monitor '{monitor_key}' will not be tracked.", file=sys.stderr)
            return

        # Try to ping
        status_code = _send_ping_internal(monitor_key, api_key)

        # Self-healing: if monitor doesn't exist and schedule provided, create it
        if status_code == 404 and schedule:
            print(f"[CronRadar] Monitor '{monitor_key}' not found. Auto-registering with schedule '{schedule}'...", file=sys.stderr)

            source = _detect_source()
            sync_monitor(monitor_key, schedule, source=source)

            # Retry ping
            _send_ping_internal(monitor_key, api_key)
    except Exception as e:
        # Never throw - protect user's job execution
        # Optionally log for debugging
        print(f"[CronRadar] Error during ping: {e}", file=sys.stderr)


def sync_monitor(
    monitor_key: str,
    schedule: str,
    source: Optional[str] = None,
    name: Optional[str] = None
) -> None:
    """
    Register a monitor with CronRadar, setting up expectations for when it should run.
    Used by extensions to sync discovered jobs.

    Args:
        monitor_key: The unique identifier for this monitor
        schedule: Cron expression defining when the job runs
        source: Source framework (e.g., "celery", "airflow"). Auto-detected if None.
        name: Human-readable name. Generated from key if None.

    Returns:
        None

    Raises:
        Never throws - all errors are suppressed to protect job execution
    """
    try:
        api_key = os.environ.get('CRONRADAR_API_KEY', '')
        if not api_key:
            print(f"[CronRadar] Warning: CRONRADAR_API_KEY environment variable not set. Monitor '{monitor_key}' will not be synced.", file=sys.stderr)
            return

        source = source or _detect_source()
        name = name or _generate_readable_name(monitor_key)

        sync_request = {
            'source': source,
            'monitors': [{
                'key': monitor_key,
                'name': name,
                'schedule': schedule,
                'gracePeriod': 60
            }]
        }

        url = 'https://api.cronradar.com/api/sync'

        # Prepare request
        data = json.dumps(sync_request).encode('utf-8')
        auth_string = f"{api_key}:".encode('utf-8')
        auth_header = base64.b64encode(auth_string).decode('ascii')

        request = Request(url, data=data, method='POST')
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', f'Basic {auth_header}')

        # Send request with timeout
        response = urlopen(request, timeout=5)

        if 200 <= response.status < 300:
            print(f"[CronRadar] Monitor '{monitor_key}' synced successfully.", file=sys.stderr)
        else:
            print(f"[CronRadar] Failed to sync monitor '{monitor_key}': HTTP {response.status}", file=sys.stderr)

    except Exception as e:
        print(f"[CronRadar] Error syncing monitor '{monitor_key}': {e}", file=sys.stderr)
        # Never throw - protect user's job execution


def _send_ping_internal(monitor_key: str, api_key: str) -> Optional[int]:
    """Send ping internally and return status code."""
    try:
        from urllib.parse import quote
        url = f"https://api.cronradar.com/ping/{quote(monitor_key, safe='')}"

        # Prepare request
        auth_string = f"{api_key}:".encode('utf-8')
        auth_header = base64.b64encode(auth_string).decode('ascii')

        request = Request(url, method='GET')
        request.add_header('Authorization', f'Basic {auth_header}')

        # Send request with timeout
        response = urlopen(request, timeout=5)
        return response.status

    except HTTPError as e:
        return e.code
    except Exception:
        return None


def _detect_source() -> str:
    """
    Detect the calling source/framework based on stack trace and imported modules.

    Returns:
        Source identifier string
    """
    try:
        # Check for Celery
        if 'celery' in sys.modules:
            return 'celery'

        # Check for Airflow
        if 'airflow' in sys.modules:
            return 'airflow'

        # Check for APScheduler
        if 'apscheduler' in sys.modules:
            return 'apscheduler'

        # Check stack trace
        stack = traceback.extract_stack()
        for frame in stack:
            filename = frame.filename.lower()
            if 'celery' in filename:
                return 'celery-direct'
            if 'airflow' in filename:
                return 'airflow-direct'
            if 'django' in filename:
                return 'django-direct'
            if 'flask' in filename:
                return 'flask-direct'

    except Exception:
        pass

    return 'manual'


def _generate_readable_name(monitor_key: str) -> str:
    """
    Generate a human-readable name from a monitor key.
    Converts kebab-case or snake_case to Title Case.

    Args:
        monitor_key: The monitor key

    Returns:
        Human-readable name
    """
    if not monitor_key:
        return monitor_key

    # Handle kebab-case: "check-overdue-pings" -> "Check Overdue Pings"
    if '-' in monitor_key:
        return ' '.join(word.capitalize() for word in monitor_key.split('-'))

    # Handle snake_case: "check_overdue_pings" -> "Check Overdue Pings"
    if '_' in monitor_key:
        return ' '.join(word.capitalize() for word in monitor_key.split('_'))

    # Handle PascalCase: "CheckOverduePings" -> "Check Overdue Pings"
    if monitor_key and monitor_key[0].isupper():
        import re
        # Insert space before capital letters
        result = re.sub(r'(?<!^)([A-Z])', r' \1', monitor_key)
        return result

    # Default: just capitalize first letter
    return monitor_key.capitalize()


# Export public API
__all__ = ['ping', 'sync_monitor', '__version__']
