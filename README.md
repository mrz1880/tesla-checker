# Tesla Checker

Automated Tesla used car inventory checker with push notifications. Monitors Tesla's certified pre-owned inventory in France and sends a notification to your phone when a new vehicle matching your criteria appears.

## Features

- **Scheduled checks** (2x/day via cron, configurable)
- **Push notifications** via [ntfy.sh](https://ntfy.sh) with direct link to the vehicle
- **Error alerts** when the Tesla API changes or becomes unavailable
- **API + DOM scraping fallback** for resilience
- **Fully configurable** search criteria via environment variables
- **Dockerized** for self-hosting on a NAS or any server

## Architecture

Clean Architecture with DDD principles:

```
src/
├── domain/                        # Business logic, no external dependencies
│   ├── vehicle.py                 # Vehicle entity (identity: VIN)
│   ├── search_criteria.py         # Search criteria value object
│   ├── inventory_snapshot.py      # Inventory snapshot aggregate + diff logic
│   └── ports.py                   # Ports (Protocol): Gateway, Repository, Notifier, Clock
├── application/
│   └── check_inventory.py         # Use case: fetch → filter → diff → notify
├── infrastructure/
│   ├── tesla_playwright_gateway.py  # Camoufox browser automation
│   ├── json_snapshot_repository.py  # JSON file persistence
│   ├── ntfy_notifier.py             # Push notifications
│   ├── system_clock.py              # Clock implementation
│   └── tesla_api_schemas.py         # Pydantic validation schemas
└── config.py                      # Environment-based configuration
```

## Quick Start

### Local

```bash
make install          # Create venv, install deps, setup pre-commit
make check            # Run lint + type-check + tests
make check-now        # Run a single inventory check
```

### Docker

```bash
docker build -t tesla-checker .
docker run --rm \
  -e NTFY_TOPIC=your-topic \
  -e TESLA_ZIP=75001 \
  -v ./results:/data \
  tesla-checker
```

### Docker Compose (NAS / Server)

```bash
cp deploy/.env.example deploy/.env
# Edit deploy/.env with your ntfy topic
docker compose -f deploy/compose.yml up -d
```

## Configuration

All search criteria are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NTFY_TOPIC` | *(required)* | ntfy.sh topic for push notifications |
| `NTFY_URL` | `https://ntfy.sh` | ntfy server URL |
| `CRON_SCHEDULE` | `30 8,18 * * *` | Cron schedule (default: 8:30 and 18:30) |
| `TESLA_ZIP` | `59130` | Postal code for search center |
| `TESLA_LAT` | `50.6117` | Latitude |
| `TESLA_LNG` | `3.1665` | Longitude |
| `TESLA_MARKET` | `FR` | Tesla market (country) |
| `TESLA_MODEL` | `m3` | Tesla model (`m3`, `my`, `ms`, `mx`) |
| `TESLA_MIN_YEAR` | `2024` | Minimum model year |
| `TESLA_MAX_ODOMETER` | `50000` | Maximum kilometers |
| `TESLA_PAINTS` | `WHITE,BLACK` | Comma-separated paint colors |
| `TESLA_TRIMS` | `LRAWD,PRAWD,PAWD` | Comma-separated trim codes |
| `TESLA_REQUIRE_EAP` | `true` | Require Enhanced Autopilot |

## How It Works

1. **Camoufox** (anti-detection Firefox fork) loads the Tesla inventory page
2. The Tesla inventory API is called from within the browser context (bypasses Akamai bot protection)
3. If the API is rate-limited, falls back to scraping vehicle data from the rendered DOM
4. Results are compared with the previous check to detect new/removed vehicles
5. New vehicles trigger a push notification via ntfy.sh with a direct link

## Development

```bash
make install          # Setup
make fmt              # Auto-format
make lint             # Ruff linter
make type-check       # mypy strict
make test             # pytest
make check            # All of the above
```

## License

MIT
