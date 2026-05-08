# CronRadar Python SDK

The base SDK for monitoring scheduled jobs in Python. Wrap a function, send a heartbeat, or track full lifecycle — CronRadar tracks duration, alerts on missed schedules, and recovers from accidental monitor deletion.

For Celery auto-discovery, install the `cronradar-celery` extension on top of this base.

## Install

```bash
pip install cronradar
# or
poetry add cronradar
# or
uv add cronradar
```

Python 3.8+ supported.

## Setup

The SDK reads its API key from the `CRONRADAR_API_KEY` environment variable.

```bash
export CRONRADAR_API_KEY=ck_app_xxxxxxxxxxxxxxxxxxxx
```

Get the API key from the CronRadar dashboard at [app.cronradar.com](https://app.cronradar.com) under your application's settings. API keys have the form `ck_app_<random>`.

The SDK does not require explicit initialization. The first call reads the env var; if it's missing, the SDK logs a single warning to `stderr` and silently no-ops every subsequent call (per the "never break a user's job" guarantee).

## Quickstart

```python
import cronradar

# First-time call: pass schedule so the monitor auto-registers.
cronradar.monitor('daily-backup', schedule='0 2 * * *')

# Subsequent calls: just the key.
cronradar.monitor('daily-backup')
```

That's the minimal integration. CronRadar:

- Creates the `daily-backup` monitor on the first ping (because `schedule` was provided)
- Records each subsequent ping
- Alerts you (email + any other configured channels) if the monitor doesn't ping within `0 2 * * *` plus its grace period
- Re-creates the monitor if you delete it from the dashboard and the schedule param is still being passed

## Manual lifecycle

For finer-grained tracking — duration measurement, explicit failure messages, hung-job detection — use the lifecycle endpoints.

### Context manager (recommended)

```python
import cronradar

with cronradar.job('daily-backup', schedule='0 2 * * *'):
    run_backup()
```

The context manager:

- Calls `start_job` on `__enter__`
- Calls `complete_job` on a clean exit
- Calls `fail_job` with the exception message on a raised exception
- Re-raises the original exception so your error handlers run normally
- Auto-registers the monitor on first run if `schedule` is provided

### Manual call style

```python
import cronradar

cronradar.start_job('daily-backup')
try:
    run_backup()
    cronradar.complete_job('daily-backup')
except Exception as e:
    cronradar.fail_job('daily-backup', str(e))
    raise   # always re-raise — monitoring observes, never alters behavior
```

## Reference

### `monitor(key, schedule=None, grace_period=None)`

Records a successful execution.

```python
cronradar.monitor(key)
cronradar.monitor(key, schedule='0 2 * * *')
cronradar.monitor(key, schedule='0 2 * * *', grace_period=120)
```

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `key` | `str` | yes | Monitor key. Lowercase, kebab/snake/dot-case. Max 64 chars. |
| `schedule` | `str` | optional | Standard 5-field cron expression. Required on the *first* ping for self-healing registration. |
| `grace_period` | `int` | optional | Seconds. How late the next ping can be before an alert fires. Default: 60. |

Raises: never. Network errors and 4xx/5xx responses are caught and logged to `stderr`.

### `start_job(key)`

Records that a job has begun executing.

```python
cronradar.start_job(key)
```

Used in conjunction with `complete_job` or `fail_job` to measure duration and detect hung jobs.

### `complete_job(key)`

Records successful completion.

```python
cronradar.complete_job(key)
```

Pair with a prior `start_job(key)` to record duration in the dashboard.

### `fail_job(key, message=None)`

Records explicit failure.

```python
cronradar.fail_job(key, 'Database connection refused')
```

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `key` | `str` | yes | Monitor key. |
| `message` | `str` | optional | Human-readable failure detail, shown in the dashboard. |

Triggers an immediate alert (no grace period). The message appears in the alert payload.

### `job(key, schedule=None, grace_period=None)`

Returns a context manager that wraps a block with lifecycle tracking.

```python
with cronradar.job(key, schedule='0 2 * * *') as ctx:
    run_work()
```

Same parameter semantics as `monitor`. The context manager re-raises any exception from the wrapped block; monitoring never swallows your exceptions.

### `sync_monitor(key, schedule, source=None, name=None)`

Pre-registers a monitor without sending a ping. Used by extensions like `cronradar-celery` during application startup.

```python
cronradar.sync_monitor(
    key='daily-backup',
    schedule='0 2 * * *',
    source='celery',
    name='Daily Backup',
)
```

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `key` | `str` | yes | Monitor key. |
| `schedule` | `str` | yes | Cron expression. |
| `source` | `str` | optional | Identifier for the framework or origin. |
| `name` | `str` | optional | Human-readable display name. |

Used internally by extensions; rarely needed in application code.

## Configuration

| Environment variable | Required | Default | Purpose |
|---|---|---|---|
| `CRONRADAR_API_KEY` | yes | — | API key from the CronRadar dashboard. Format `ck_app_xxxxx`. |
| `CRONRADAR_BASE_URL` | no | `https://cron.life` | Override the ingestion endpoint. Used for self-hosted or staging environments. |
| `CRONRADAR_TIMEOUT` | no | `5.0` | HTTP request timeout in seconds (float). |
| `CRONRADAR_LOG_ERRORS` | no | `1` | Set to `0` to suppress the stderr warnings the SDK emits on network failure. |

## Error handling

The SDK upholds two hard guarantees:

1. **Never raises to user code.** Network errors, timeouts, 4xx/5xx responses, malformed payloads — all caught and logged to `stderr`. A failing CronRadar API must not break a user's cron job.
2. **Re-raises user-job exceptions.** When using `cronradar.job(...)` as a context manager, the original exception from your block always propagates. Monitoring observes; it does not change behavior.

What this looks like at runtime:

| Situation | SDK behavior | Your code |
|---|---|---|
| Network unreachable | Logs to stderr; returns | Continues normally |
| 5-second timeout | Logs to stderr; returns | Continues normally |
| 401 Unauthorized | Logs to stderr; returns | Continues normally |
| Block in `with cronradar.job(...)` raises | Records `fail_job`; re-raises | Receives the original exception |
| `CRONRADAR_API_KEY` missing | Logs once per process; subsequent calls no-op | Continues normally |

If you need to know whether a ping succeeded — for example, in tests — every function returns `None` either way; success is silent. Inspect `stderr` or set `CRONRADAR_LOG_ERRORS=1` (default) to see failures.

## Troubleshooting

### `401 Unauthorized` in stderr logs

Your `CRONRADAR_API_KEY` is wrong or missing. Verify:

```bash
echo $CRONRADAR_API_KEY    # should print ck_app_xxxxx
```

The key must match the one shown on **app.cronradar.com → your application → Settings → API Keys**. Keys are not retrievable after creation — if you lost it, create a new one and rotate.

### `404 Monitor Not Found` on first ping

You called `monitor(key)` without a `schedule` for a brand-new key. The first ping must include `schedule` so CronRadar can register the monitor:

```python
cronradar.monitor('daily-backup', schedule='0 2 * * *')
```

Subsequent pings can omit `schedule`. If you delete the monitor from the dashboard and the next ping doesn't include `schedule`, you'll see the same 404.

### My cron expression is rejected

CronRadar uses the standard 5-field POSIX cron format: `minute hour day-of-month month day-of-week`. Six-field expressions (with seconds) and Quartz-style 7-field expressions are not accepted. Common pitfalls:

| Wrong | Right |
|---|---|
| `0 0 2 * * *` (6 fields) | `0 2 * * *` |
| `0 2 ? * MON-FRI` (Quartz `?`) | `0 2 * * 1-5` |

### The job runs but I never see a ping in the dashboard

Three things to check, in order:

1. **API key** — see "401 Unauthorized" above.
2. **Network** — outbound HTTPS to `https://cron.life` may be blocked by firewall.
3. **Process termination** — short-lived scripts may exit before the HTTP request completes. The SDK uses synchronous requests by default so this is uncommon, but if you've configured an async transport, ensure your event loop has time to flush.

### Errors are noisy in development

Set `CRONRADAR_LOG_ERRORS=0` in dev environments where you don't have a real API key set:

```bash
CRONRADAR_LOG_ERRORS=0 python my_job.py
```

The SDK still no-ops cleanly; it just stops complaining.

## Links

- **Documentation:** [docs.cronradar.com](https://docs.cronradar.com)
- **Agent-friendly index:** [docs.cronradar.com/llms.txt](https://docs.cronradar.com/llms.txt)
- **OpenAPI spec:** [api.cronradar.com/swagger/v1/swagger.json](https://api.cronradar.com/swagger/v1/swagger.json)
- **PyPI:** [pypi.org/project/cronradar](https://pypi.org/project/cronradar)
- **GitHub:** [github.com/cronradar/cronradar-python](https://github.com/cronradar/cronradar-python)
- **Celery extension:** [github.com/cronradar/cronradar-celery](https://github.com/cronradar/cronradar-celery)
- **Support:** support@cronradar.com

## License

© 2026 [CronRadar](https://cronradar.com) · Proprietary — see [LICENSE](./LICENSE).
