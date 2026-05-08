# WhereInTheWorld — OpenClaw Skill
# v0.1.0

Agents should use this skill to interact with the WhereInTheWorld location
history service. The service stores location pings from OwnTracks and provides
a query API.

## Configuration

The following variables must be set in the agent's environment or config:

- `WITW_BASE_URL` — Base URL of the WhereInTheWorld service
  (e.g. `https://whereintheworld.tailnet-name.ts.net:36024`)
- `WITW_API_KEY` — Shared API key for authentication

## API Endpoints

All endpoints except `/health` require the `X-API-Key` header set to `WITW_API_KEY`.
All timestamps are Unix epoch seconds (UTC).

### Get Current Location

Get the most recent location ping.

```
GET {WITW_BASE_URL}/api/locations/current
X-API-Key: {WITW_API_KEY}
```

### Query Location History

Search locations by time range, place, or tracker ID.

```
GET {WITW_BASE_URL}/api/locations
X-API-Key: {WITW_API_KEY}
```

**Optional query parameters:**
- `from` — Start timestamp (unix epoch, inclusive)
- `to` — End timestamp (unix epoch, inclusive)
- `from_date` — Start date YYYY-MM-DD (alternative to `from`)
- `to_date` — End date YYYY-MM-DD (alternative to `to`)
- `geofence` — Filter by named place/geofence
- `tid` — Filter by tracker ID
- `limit` — Max results (default 100, max 10000)
- `offset` — Pagination offset

### Search Near a Point

Find locations within a radius of a coordinate. Results ordered by distance.

```
GET {WITW_BASE_URL}/api/locations/near
X-API-Key: {WITW_API_KEY}
```

**Required parameters:**
- `lat` — Latitude (WGS84)
- `lon` — Longitude (WGS84)
- `radius_m` — Radius in meters

**Optional:** `from`, `to`, `limit`, `offset`

### Search by Place Name

Get all locations tagged with a specific geofence name.

```
GET {WITW_BASE_URL}/api/locations/place/{place_name}
X-API-Key: {WITW_API_KEY}
```

**Optional:** `from`, `to`, `limit`, `offset`

### Day Timeline

Get locations for a specific day in chronological order (oldest first).

```
GET {WITW_BASE_URL}/api/locations/track
X-API-Key: {WITW_API_KEY}
```

**Optional:** `date` (YYYY-MM-DD, defaults to today UTC), or `from`+`to` for arbitrary ranges.

### List Places

Get all distinct geofence names with visit counts and average coordinates.

```
GET {WITW_BASE_URL}/api/places
X-API-Key: {WITW_API_KEY}
```

### Stats

Get aggregate statistics (totals, date range, daily average).

```
GET {WITW_BASE_URL}/api/locations/stats
X-API-Key: {WITW_API_KEY}
```

### Health Check (no auth required)

```
GET {WITW_BASE_URL}/health
```

## Example Agent Queries

### "Where am I right now?"

```
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/locations/current"
```

### "Where was I yesterday?"

```
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/locations/track?date=$(date -d yesterday +%Y-%m-%d)"
```

### "Have I been to the office this week?"

```
# Monday of this week in unix epoch
MONDAY=$(date -d "last monday" +%s)
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/locations?from=$MONDAY&geofence=office"
```

### "Where do I spend the most time?"

```
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/locations/stats"
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/places"
```

### "Where was I within 500m of the office building?"

```
curl -s -H "X-API-Key: $WITW_API_KEY" \
  "$WITW_BASE_URL/api/locations/near?lat=51.509865&lon=-0.118092&radius_m=500"
```
