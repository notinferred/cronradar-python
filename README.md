# CronRadar Python SDK

Monitor cron jobs with one function call.

## Installation

```bash
pip install cronradar
```

## Usage

```python
import cronradar

# After your cron job completes successfully
cronradar.monitor('daily-backup')

# With self-healing (auto-register if monitor doesn't exist)
cronradar.monitor('daily-backup', schedule='0 2 * * *')
```

## Lifecycle Tracking

**Option 1: Context Manager (Automatic)**
```python
with cronradar.job('daily-backup', schedule='0 2 * * *'):
    run_backup()
```

**Option 2: Manual**
```python
cronradar.start_job('daily-backup')
try:
    run_backup()
    cronradar.complete_job('daily-backup')
except Exception as e:
    cronradar.fail_job('daily-backup', str(e))
    raise
```

## Configuration

Set environment variable:
- `CRONRADAR_API_KEY`: Your API key from cronradar.com

## Documentation

See [cronradar.com/docs](https://cronradar.com/docs) for full documentation.

## License

Proprietary - © 2025 CronRadar. All rights reserved.
