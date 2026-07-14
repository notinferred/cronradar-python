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
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote

from .constants import (
    BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_GRACE_PERIOD_SECONDS,
    API_KEY_ENV_VAR,
    is_valid_monitor_key,
)


__version__ = "0.1.0"


def monitor(monitor_key: str, schedule: Optional[str] = None) -> None:
    """
    Monitor a job execution by recording it in CronRadar.
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
        if not is_valid_monitor_key(monitor_key):
            return

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
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
        print(f"[CronRadar] Error during monitor: {e}", file=sys.stderr)


def start_job(monitor_key: str, schedule: Optional[str] = None) -> None:
    """
    Signal that a job has started executing.
    Used for lifecycle tracking to detect hung jobs and measure execution duration.

    Args:
        monitor_key: The monitor key identifying your job
        schedule: Optional cron schedule for auto-registration if monitor doesn't exist

    Returns:
        None

    Raises:
        Never throws - all errors are suppressed to protect job execution
    """
    try:
        if not is_valid_monitor_key(monitor_key):
            return

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
        if not api_key:
            return

        _send_lifecycle_ping(monitor_key, 'start', api_key, schedule)
    except Exception as e:
        print(f"[CronRadar] Error during start_job: {e}", file=sys.stderr)


def complete_job(monitor_key: str) -> None:
    """
    Signal that a job has completed successfully.
    Used for lifecycle tracking to record completion time and calculate duration.

    Args:
        monitor_key: The monitor key identifying your job

    Returns:
        None

    Raises:
        Never throws - all errors are suppressed to protect job execution
    """
    try:
        if not is_valid_monitor_key(monitor_key):
            return

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
        if not api_key:
            return

        _send_lifecycle_ping(monitor_key, 'complete', api_key)
    except Exception as e:
        print(f"[CronRadar] Error during complete_job: {e}", file=sys.stderr)


def fail_job(monitor_key: str, message: Optional[str] = None) -> None:
    """
    Signal that a job has failed.
    Triggers immediate alerts without waiting for grace period.

    Args:
        monitor_key: The monitor key identifying your job
        message: Optional failure message for debugging

    Returns:
        None

    Raises:
        Never throws - all errors are suppressed to protect job execution
    """
    try:
        if not is_valid_monitor_key(monitor_key):
            return

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
        if not api_key:
            return

        _send_lifecycle_ping(monitor_key, 'fail', api_key, message=message)
    except Exception as e:
        print(f"[CronRadar] Error during fail_job: {e}", file=sys.stderr)


@contextmanager
def job(monitor_key: str, schedule: Optional[str] = None):
    """
    Context manager for monitoring code blocks with lifecycle tracking.
    Handles start/complete/fail signals automatically.

    Example:
        with cronradar.job('backup-job', schedule='0 2 * * *'):
            run_backup()

    Args:
        monitor_key: The monitor key identifying your job
        schedule: Optional cron schedule for auto-registration

    Yields:
        None
    """
    start_job(monitor_key, schedule)
    try:
        yield
        complete_job(monitor_key)
    except Exception as e:
        fail_job(monitor_key, str(e))
        raise  # Re-raise to preserve original behavior


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
        if not is_valid_monitor_key(monitor_key):
            return

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
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
                'gracePeriod': DEFAULT_GRACE_PERIOD_SECONDS
            }]
        }

        url = f"{BASE_URL}/api/sync"

        # Prepare request
        data = json.dumps(sync_request).encode('utf-8')
        auth_string = f"{api_key}:".encode('utf-8')
        auth_header = base64.b64encode(auth_string).decode('ascii')

        request = Request(url, data=data, method='POST')
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', f'Basic {auth_header}')

        # Send request with timeout
        response = urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS)

        if 200 <= response.status < 300:
            print(f"[CronRadar] Monitor '{monitor_key}' synced successfully.", file=sys.stderr)
        else:
            print(f"[CronRadar] Failed to sync monitor '{monitor_key}': HTTP {response.status}", file=sys.stderr)

    except Exception as e:
        print(f"[CronRadar] Error syncing monitor '{monitor_key}': {e}", file=sys.stderr)
        # Never throw - protect user's job execution


def sync_monitors(
    monitors,
    source: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
    """
    Reconcile the complete set of monitors for a source in a single request.
    Extensions call this on startup and periodically to declare every discovered
    job (the authoritative set), so dead-man coverage exists before a job ever runs.

    Args:
        monitors: Iterable of dicts, each with 'key' and 'schedule' (required) and
                  optional 'name' and 'grace_period'.
        source: Source framework (e.g., "celery"). Auto-detected if None.
        version: Extension version reported to the server. Defaults to this SDK version.

    Raises:
        Never throws - all errors are suppressed to protect the application.
    """
    try:
        payload_monitors = []
        for m in (monitors or []):
            key = m.get('key')
            schedule = m.get('schedule')
            if not key or not schedule or not is_valid_monitor_key(key):
                continue
            payload_monitors.append({
                'key': key,
                'name': m.get('name') or _generate_readable_name(key),
                'schedule': schedule,
                'gracePeriod': m.get('grace_period', m.get('gracePeriod', DEFAULT_GRACE_PERIOD_SECONDS)),
            })

        api_key = os.environ.get(API_KEY_ENV_VAR, '')
        if not api_key:
            print(f"[CronRadar] Warning: CRONRADAR_API_KEY environment variable not set. {len(payload_monitors)} monitor(s) will not be synced.", file=sys.stderr)
            return

        source = source or _detect_source()

        sync_request = {
            'source': source,
            'version': version or __version__,
            'mode': 'reconcile',
            'monitors': payload_monitors,
        }

        url = f"{BASE_URL}/api/sync"
        data = json.dumps(sync_request).encode('utf-8')
        auth_string = f"{api_key}:".encode('utf-8')
        auth_header = base64.b64encode(auth_string).decode('ascii')

        request = Request(url, data=data, method='POST')
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', f'Basic {auth_header}')

        response = urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS)

        if 200 <= response.status < 300:
            print(f"[CronRadar] Reconciled {len(payload_monitors)} monitor(s) for source '{source}'.", file=sys.stderr)
        else:
            print(f"[CronRadar] Failed to reconcile monitors for source '{source}': HTTP {response.status}", file=sys.stderr)

    except Exception as e:
        print(f"[CronRadar] Error reconciling monitors: {e}", file=sys.stderr)
        # Never throw - protect user's application


def _send_ping_internal(monitor_key: str, api_key: str) -> Optional[int]:
    """Send ping internally and return status code."""
    try:
        # URL-based auth: /ping/{monitor_key}/{api_key}
        url = f"{BASE_URL}/ping/{quote(monitor_key, safe='')}/{quote(api_key, safe='')}"

        request = Request(url, method='GET')

        # Send request with timeout
        response = urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS)
        return response.status

    except HTTPError as e:
        return e.code
    except Exception:
        return None


def _send_lifecycle_ping(
    monitor_key: str,
    endpoint: str,
    api_key: str,
    schedule: Optional[str] = None,
    message: Optional[str] = None
) -> None:
    """Send lifecycle ping (start/complete/fail) internally."""
    try:
        # URL-based auth: /ping/{monitor_key}/{api_key}/{endpoint}
        url = f"{BASE_URL}/ping/{quote(monitor_key, safe='')}/{quote(api_key, safe='')}/{endpoint}"

        # Add query parameters
        params = []
        if schedule:
            params.append(f"schedule={quote(schedule)}")
        if message:
            params.append(f"message={quote(message)}")

        if params:
            url += "?" + "&".join(params)

        request = Request(url, method='POST')

        # Send request with timeout
        urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS)

    except Exception:
        # Silently fail to protect job execution
        pass


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
__all__ = [
    'monitor',  # Simple monitoring function
    'start_job',
    'complete_job',
    'fail_job',
    'job',  # Context manager for automatic lifecycle
    'sync_monitor',
    'sync_monitors',
    '__version__'
]
