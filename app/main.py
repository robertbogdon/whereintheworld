"""
WhereInTheWorld — OwnTracks location history API.

Service that accepts location pings from OwnTracks and provides
a query API for location history, searchable by time range,
named place, proximity, and more.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import async_session_factory, engine, get_session
from .models import Location
from .schemas import (
    CurrentLocation,
    IngestionResponse,
    LocationList,
    LocationOut,
    OwnTracksPayload,
    PlacesList,
    PlaceOut,
    StatsOut,
    StatusOut,
)

logger = logging.getLogger("whereintheworld")


# ── Lifecycle ───────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — manages startup/shutdown hooks."""
    logger.info("Starting WhereInTheWorld…")
    yield
    logger.info("Shutting down WhereInTheWorld…")
    await engine.dispose()


app = FastAPI(
    title="WhereInTheWorld",
    description=(
        "Personal location history service. "
        "Accepts pings from OwnTracks and provides a query API "
        "for OwnClaw agents and other consumers."
    ),
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "WhereInTheWorld",
        "url": "https://github.com/robertbogdon/whereintheworld",
    },
)


# ── Auth ────────────────────────────────────────────────────────────


async def verify_api_key(request: Request):
    """Dependency: rejects requests without a valid X-API-Key header."""
    key = request.headers.get("X-API-Key", "")
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide via X-API-Key header.",
        )


# ── Helper — parse date string to unix timestamp ────────────────────


def _date_to_timestamp(date_str: str, end_of_day: bool = False) -> int:
    """Convert YYYY-MM-DD string to unix timestamp."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        return int(dt.timestamp())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.",
        )


# ── Endpoints ───────────────────────────────────────────────────────


@app.get("/health", tags=["System"])
async def health():
    """Unauthenticated health check. Returns 200 when the service is alive."""
    return {"status": "ok"}


@app.get(
    "/api/status",
    response_model=StatusOut,
    tags=["System"],
    dependencies=[Depends(verify_api_key)],
)
async def get_status(db: AsyncSession = Depends(get_session)):
    """Service status with location count."""
    result = await db.execute(select(func.count(Location.id)))
    count = result.scalar() or 0
    return StatusOut(status="ok", version="0.1.0", locations_stored=count)


# ── Ingestion ───────────────────────────────────────────────────────


@app.post(
    "/api/owntracks",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingestion"],
    dependencies=[Depends(verify_api_key)],
    summary="Ingest an OwnTracks location ping",
)
async def ingest_owntracks(
    payload: OwnTracksPayload,
    db: AsyncSession = Depends(get_session),
):
    """Receive a location ping from OwnTracks (HTTP mode) and store it.

    Accepts the standard OwnTracks JSON payload format.
    The 'geofence' field is populated from the first entry in 'inregions'
    if not explicitly provided.
    """
    inregions = payload.inregions or []
    excluded = payload.excluded or []

    # Infer geofence from inregions if not explicitly provided
    geofence = payload.geofence
    if not geofence and inregions:
        geofence = inregions[0]

    loc = Location(
        topic=payload.topic,
        tst=payload.tst,
        lat=payload.lat,
        lon=payload.lon,
        acc=payload.acc,
        alt=payload.alt,
        vel=payload.vel,
        vac=payload.vac,
        conn=payload.conn,
        batt=payload.batt,
        bs=payload.bs,
        p=payload.p,
        tid=payload.tid,
        t=payload.t,
        inregions=inregions or None,
        excluded=excluded or None,
        geofence=geofence,
    )
    db.add(loc)
    await db.flush()
    loc_id = loc.id

    ts_utc = datetime.fromtimestamp(payload.tst, tz=timezone.utc)

    return IngestionResponse(
        status="ok",
        location_id=loc_id,
        message=f"Location recorded at {ts_utc.isoformat()}",
    )


# ── Current location ────────────────────────────────────────────────


@app.get(
    "/api/locations/current",
    response_model=CurrentLocation,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Get the most recent location ping",
)
async def get_current_location(db: AsyncSession = Depends(get_session)):
    """Returns the single most recent location entry."""
    result = await db.execute(
        select(Location).order_by(Location.tst.desc()).limit(1)
    )
    loc = result.scalar_one_or_none()
    return CurrentLocation(
        location=LocationOut.model_validate(loc) if loc else None
    )


# ── Query locations ─────────────────────────────────────────────────


@app.get(
    "/api/locations",
    response_model=LocationList,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Query location history with filters",
)
async def query_locations(
    from_: Optional[int] = Query(
        None, alias="from", description="Start timestamp (unix epoch, inclusive)"
    ),
    to: Optional[int] = Query(
        None, description="End timestamp (unix epoch, inclusive)"
    ),
    from_date: Optional[str] = Query(
        None,
        alias="from_date",
        description="Start date YYYY-MM-DD (inclusive, alternative to 'from')",
    ),
    to_date: Optional[str] = Query(
        None,
        alias="to_date",
        description="End date YYYY-MM-DD (inclusive, alternative to 'to')",
    ),
    geofence: Optional[str] = Query(
        None, description="Filter by geofence/place name"
    ),
    tid: Optional[str] = Query(
        None, description="Filter by tracker ID"
    ),
    limit: int = Query(100, ge=1, le=10000, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    db: AsyncSession = Depends(get_session),
):
    """Search location history by time range, place, or tracker ID.

    All parameters are optional — returns most recent locations by default.
    Supports both unix timestamps (from/to) and date strings (from_date/to_date).
    """
    q = select(Location)

    # Time range by unix timestamps
    if from_ is not None:
        q = q.where(Location.tst >= from_)
    if to is not None:
        q = q.where(Location.tst <= to)

    # Time range by date strings (alternative to unix timestamps)
    if from_date is not None:
        q = q.where(Location.tst >= _date_to_timestamp(from_date))
    if to_date is not None:
        q = q.where(Location.tst <= _date_to_timestamp(to_date, end_of_day=True))

    if geofence:
        q = q.where(Location.geofence == geofence)
    if tid:
        q = q.where(Location.tid == tid)

    # Total matching count
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch paginated results (most recent first)
    q = q.order_by(Location.tst.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return LocationList(
        locations=[LocationOut.model_validate(r) for r in rows],
        total=total,
    )


# ── Near a point ────────────────────────────────────────────────────


@app.get(
    "/api/locations/near",
    response_model=LocationList,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Search locations near a geographic point",
)
async def query_locations_near(
    lat: float = Query(..., description="Latitude (WGS84, decimal degrees)"),
    lon: float = Query(..., description="Longitude (WGS84, decimal degrees)"),
    radius_m: float = Query(
        1000, ge=1, le=100_000, description="Search radius in meters"
    ),
    from_: Optional[int] = Query(
        None, alias="from", description="Start timestamp (unix epoch)"
    ),
    to: Optional[int] = Query(
        None, description="End timestamp (unix epoch)"
    ),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    """Find locations within a radius of a given coordinate.

    Uses PostGIS ST_DWithin for efficient geospatial index queries.
    Results are ordered by distance from the search point (nearest first).
    """
    point_wkt = f"POINT({lon} {lat})"
    point_geog = func.ST_GeogFromText(point_wkt)
    distance_filter = func.ST_DWithin(Location.geom, point_geog, radius_m)

    q = select(Location).where(distance_filter)

    if from_ is not None:
        q = q.where(Location.tst >= from_)
    if to is not None:
        q = q.where(Location.tst <= to)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        q.order_by(func.ST_Distance(Location.geom, point_geog))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(q)
    rows = result.scalars().all()

    return LocationList(
        locations=[LocationOut.model_validate(r) for r in rows],
        total=total,
    )


# ── By place name ───────────────────────────────────────────────────


@app.get(
    "/api/locations/place/{place_name}",
    response_model=LocationList,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Search locations by named place (geofence)",
)
async def query_locations_by_place(
    place_name: str,
    from_: Optional[int] = Query(
        None, alias="from", description="Start timestamp (unix epoch)"
    ),
    to: Optional[int] = Query(
        None, description="End timestamp (unix epoch)"
    ),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    """Return all location pings tagged with a specific geofence name.

    Geofences are set by OwnTracks 'inregions' or the explicit geofence field.
    """
    q = select(Location).where(Location.geofence == place_name)

    if from_ is not None:
        q = q.where(Location.tst >= from_)
    if to is not None:
        q = q.where(Location.tst <= to)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Location.tst.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return LocationList(
        locations=[LocationOut.model_validate(r) for r in rows],
        total=total,
    )


# ── Day timeline ────────────────────────────────────────────────────


@app.get(
    "/api/locations/track",
    response_model=LocationList,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Get a chronological day timeline",
)
async def query_track(
    date: Optional[str] = Query(
        None,
        description="Date YYYY-MM-DD (defaults to today UTC). "
        "Use 'from'/'to' for arbitrary ranges.",
    ),
    from_: Optional[int] = Query(
        None,
        alias="from",
        description="Start timestamp (unix epoch) — overrides 'date'",
    ),
    to: Optional[int] = Query(
        None,
        description="End timestamp (unix epoch) — overrides 'date'",
    ),
    limit: int = Query(10000, ge=1, le=100000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    """Returns locations in chronological order (oldest first).

    Designed for building day-timeline views. Specify a date or a custom
    timestamp range. When 'from' and 'to' are both provided, 'date' is ignored.
    """
    q = select(Location)

    if from_ is not None and to is not None:
        q = q.where(Location.tst >= from_, Location.tst <= to)
    elif date:
        start = _date_to_timestamp(date)
        end = _date_to_timestamp(date, end_of_day=True)
        q = q.where(Location.tst >= start, Location.tst <= end)
    else:
        # Default: today UTC
        now = datetime.now(timezone.utc)
        start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end = int(
            now.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
        )
        q = q.where(Location.tst >= start, Location.tst <= end)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Location.tst.asc()).offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()

    return LocationList(
        locations=[LocationOut.model_validate(r) for r in rows],
        total=total,
    )


# ── Places ──────────────────────────────────────────────────────────


@app.get(
    "/api/places",
    response_model=PlacesList,
    tags=["Places"],
    dependencies=[Depends(verify_api_key)],
    summary="List all named places (geofences) with visit counts",
)
async def list_places(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    """Returns distinct geofence names, average coordinates, and visit counts.

    Places are ordered by visit count (most visited first).
    """
    q = select(
        Location.geofence,
        func.count(Location.id).label("visit_count"),
        func.avg(Location.lat).label("avg_lat"),
        func.avg(Location.lon).label("avg_lon"),
    ).where(
        Location.geofence.isnot(None)
    ).group_by(
        Location.geofence
    ).order_by(
        func.count(Location.id).desc()
    ).offset(offset).limit(limit)

    result = await db.execute(q)
    rows = result.all()

    places = [
        PlaceOut(
            name=row.geofence,
            lat=round(float(row.avg_lat), 6) if row.avg_lat else 0.0,
            lon=round(float(row.avg_lon), 6) if row.avg_lon else 0.0,
            visit_count=row.visit_count,
        )
        for row in rows
    ]

    return PlacesList(places=places, total=len(places))


# ── Stats ───────────────────────────────────────────────────────────


@app.get(
    "/api/locations/stats",
    response_model=StatsOut,
    tags=["Locations"],
    dependencies=[Depends(verify_api_key)],
    summary="Aggregate location statistics",
)
async def get_stats(db: AsyncSession = Depends(get_session)):
    """Returns aggregate stats: total locations, places, date range, daily average."""
    total = (
        await db.execute(select(func.count(Location.id)))
    ).scalar() or 0
    earliest = (
        await db.execute(select(func.min(Location.tst)))
    ).scalar()
    latest = (
        await db.execute(select(func.max(Location.tst)))
    ).scalar()
    num_places = (
        await db.execute(
            select(func.count(func.distinct(Location.geofence))).where(
                Location.geofence.isnot(None)
            )
        )
    ).scalar() or 0

    daily_avg = None
    if earliest and latest:
        days = max(1, (latest - earliest) / 86400)
        daily_avg = round(total / days, 1)

    return StatsOut(
        total_locations=total,
        total_places=num_places,
        earliest=earliest,
        latest=latest,
        daily_average=daily_avg,
    )
