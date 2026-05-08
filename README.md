# WhereInTheWorld 🗺️

**OwnTracks location history service** — stores location pings with PostGIS and
provides a query API for OpenClaw agents and other consumers.

## Quick Start

```bash
# 1. Generate secrets
./generate-secrets.sh

# 2. Start the stack
docker compose up -d

# 3. Check it's alive
curl -s http://localhost:36024/health

# 4. Verify with API key
curl -s -H "X-API-Key: $(grep WITW_API_KEY .env | cut -d= -f2)" \
  http://localhost:36024/api/status
```

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  OwnTracks   │────▶│  whereintheworld │────▶│ whereintheworld │
│  (Phone)     │     │  (FastAPI)       │     │  -db (PostGIS)  │
└──────────────┘     │  :8000           │     └──────────────────┘
                     │  :36024 (host)   │
┌──────────────┐     │                  │
│  OpenClaw     │────▶│  /api/locations  │
│  Agent       │     │  /api/places     │
└──────────────┘     └──────────────────┘
```

## Configuration

All configuration is through environment variables. Copy `env.example` to `.env`
and fill in values, or run `./generate-secrets.sh` to auto-generate.

| Variable | Default | Description |
|---|---|---|
| `WITW_DB_PASSWORD` | *(required)* | Postgres password |
| `WITW_DB_HOST` | `whereintheworld-db` | Database hostname |
| `WITW_DB_PORT` | `5432` | Database port |
| `WITW_DB_USER` | `witw` | Database user |
| `WITW_DB_NAME` | `whereintheworld` | Database name |
| `WITW_API_KEY` | *(required)* | API key for all endpoints |
| `HOST_BIND_ADDRESS` | `127.0.0.1` | Host bind address (use `0.0.0.0` for all interfaces) |
| `HOST_PORT` | `36024` | Host port mapped to container :8000 |

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Health check |
| GET | `/api/status` | Yes | Service status |
| POST | `/api/owntracks` | Yes | Ingest OwnTracks ping |
| GET | `/api/locations/current` | Yes | Latest location |
| GET | `/api/locations` | Yes | Search with filters |
| GET | `/api/locations/near` | Yes | Proximity search |
| GET | `/api/locations/place/{name}` | Yes | By place name |
| GET | `/api/locations/track` | Yes | Day timeline |
| GET | `/api/locations/stats` | Yes | Aggregate stats |
| GET | `/api/places` | Yes | List all places |
| GET | `/docs` | No | Swagger UI |

All authenticated endpoints use `X-API-Key` header.

## OwnTracks Configuration

In the OwnTracks app, configure HTTP mode:

- **Mode:** HTTP
- **URL:** `https://your-hostname:36024/api/owntracks`
- **Headers:** `X-API-Key: <your-api-key>`
- **Auth:** None (header-based auth)

## Tailscale Serve

```bash
tailscale serve --bg --https=36024 localhost:36024
```

## Deployment Notes

- The `whereintheworld` user inside the container is non-root
- Database volume persists across restarts (`docker compose down -v` to reset)
- Health checks are configured for both services
- See `docs/deployment.md` for production considerations

## OpenClaw Agent Skill

If you run this with OpenClaw agents, install the skill at `skill/` to give
agents the knowledge they need to query the API.
