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
cronradar.ping('daily-backup')

# With self-healing (auto-register if monitor doesn't exist)
cronradar.ping('daily-backup', schedule='0 2 * * *')
```

## Configuration

Set environment variable:
- `CRONRADAR_API_KEY`: Your API key from cronradar.com

## Documentation

See [cronradar.com/docs](https://cronradar.com/docs) for full documentation.

## License

Proprietary - © 2025 CronRadar. All rights reserved.
