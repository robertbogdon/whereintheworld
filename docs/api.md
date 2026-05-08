# API Reference

Complete documentation for the WhereInTheWorld API.

## Authentication

All endpoints except `/health` require the `X-API-Key` header:

```
X-API-Key: <your-api-key>
```

## Endpoints

### Health

```
GET /health
```

Returns `{"status": "ok"}` when the service is running. No authentication required.

### Status

```
GET /api/status
```

Returns service version and location count.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "locations_stored": 12345
}
```

### Ingest OwnTracks Ping

```
POST /api/owntracks
Content-Type: application/json
X-API-Key: <key>
```

**Request body** (standard OwnTracks JSON format):
```json
{
  "_type": "location",
  "tst": 1715000000,
  "lat": 51.509865,
  "lon": -0.118092,
  "acc": 25.0,
  "alt": 35.0,
  "vel": 0,
  "batt": 85,
  "tid": "ROB",
  "t": "p",
  "inregions": ["home"],
  "geofence": "home"
}
```

**Response:**
```json
{
  "status": "ok",
  "location_id": 42,
  "message": "Location recorded at 2024-05-06T10:53:20+00:00"
}
```

### Get Current Location

```
GET /api/locations/current
```

Returns the single most recent location ping.

**Response:**
```json
{
  "location": {
    "id": 42,
    "tst": 1715000000,
    "lat": 51.509865,
    "lon": -0.118092,
    "acc": 25.0,
    "alt": 35.0,
    "vel": 0,
    "batt": 85,
    "geofence": "home",
    "tid": "ROB",
    "t": "p",
    "created_at": "2024-05-06T10:53:20.123456+00:00"
  }
}
```

Returns `{"location": null}` if no data has been collected yet.

### Query Locations

```
GET /api/locations?from=<epoch>&to=<epoch>&geofence=<name>&limit=100&offset=0
```

Search with time range, place, and tracker filters. Returns newest first.

**Parameters:**
| Name | Type | Description |
|---|---|---|
| `from` | int (epoch) | Start timestamp, inclusive |
| `to` | int (epoch) | End timestamp, inclusive |
| `from_date` | string | Start date YYYY-MM-DD (alternative to `from`) |
| `to_date` | string | End date YYYY-MM-DD (alternative to `to`) |
| `geofence` | string | Filter by named place |
| `tid` | string | Filter by tracker ID |
| `limit` | int | Max results (1-10000, default 100) |
| `offset` | int | Pagination offset |

**Response:**
```json
{
  "locations": [
    {
      "id": 42,
      "tst": 1715000000,
      "lat": 51.509865,
      "lon": -0.118092,
      "geofence": "home",
      "tid": "ROB",
      "t": "p"
    }
  ],
  "total": 1
}
```

### Search Near Point

```
GET /api/locations/near?lat=51.509865&lon=-0.118092&radius_m=500&from=<epoch>&to=<epoch>
```

Finds locations within a radius. Results ordered by distance (nearest first).

**Required parameters:**
| Name | Type | Description |
|---|---|---|
| `lat` | float | Latitude (WGS84) |
| `lon` | float | Longitude (WGS84) |
| `radius_m` | float | Radius in meters (1-100000) |

Optional: `from`, `to`, `limit`, `offset`.

### Search by Place

```
GET /api/locations/place/home
```

Filter by exact geofence name. Optional: `from`, `to`, `limit`, `offset`.

### Day Timeline

```
GET /api/locations/track?date=2024-05-06
```

Returns locations for a day in chronological order (oldest first). Good for
building timeline views.

**Parameters:**
| Name | Type | Description |
|---|---|---|
| `date` | string | YYYY-MM-DD (defaults to today UTC) |
| `from` | int | Overrides `date` if both provided |
| `to` | int | Overrides `date` if both provided |
| `limit` | int | Max results (1-100000, default 10000) |

### List Places

```
GET /api/places
```

Returns all distinct geofence names with visit counts and average coordinates.
Ordered by visit count (most visited first).

**Response:**
```json
{
  "places": [
    { "name": "home", "lat": 51.509865, "lon": -0.118092, "rad": 0, "visit_count": 5432 },
    { "name": "office", "lat": 51.500729, "lon": -0.124626, "rad": 0, "visit_count": 2789 }
  ],
  "total": 2
}
```

### Stats

```
GET /api/locations/stats
```

**Response:**
```json
{
  "total_locations": 12345,
  "total_places": 5,
  "earliest": 1680000000,
  "latest": 1715000000,
  "daily_average": 42.3
}
```

## Response Formats

All responses are JSON. Paginated endpoints return:
- `locations` (or `places`) — the data array
- `total` — total matching count (not just the current page)

## Error Responses

```json
{
  "detail": "Invalid or missing API key. Provide via X-API-Key header."
}
```

Standard HTTP status codes: 200, 201, 400, 401.
