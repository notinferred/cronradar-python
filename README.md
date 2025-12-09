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
cronradar.ping('daily-backup', schedule='0 2 * * *', grace_period=300)
```

## Configuration

Set environment variable:
- `CRONRADAR_API_KEY`: Your API key from cronradar.com
- `CRONRADAR_BASE_URL`: Base URL override (optional, default: `https://cronradar.com`)
- `CRONRADAR_METHOD`: HTTP method for ping (optional, default: `GET`)

## Documentation

See [cronradar.com/docs](https://cronradar.com/docs) for full documentation.

## License

MIT
