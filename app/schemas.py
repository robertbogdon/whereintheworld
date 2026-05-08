"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── OwnTracks payload ───────────────────────────────────────────────


class OwnTracksPayload(BaseModel):
    """Schema for validating incoming OwnTracks HTTP JSON payloads.

    See: https://owntracks.org/book/tech/json/
    """

    payload_type: str = Field(
        "location", alias="_type", serialization_alias="_type"
    )
    tst: int  # Unix epoch seconds (required)
    lat: float  # Latitude (required)
    lon: float  # Longitude (required)
    acc: Optional[float] = None  # Accuracy in meters
    alt: Optional[float] = None  # Altitude in meters
    vel: Optional[float] = None  # Velocity in km/h
    vac: Optional[float] = None  # Vertical accuracy
    conn: Optional[str] = None  # Network connection type
    batt: Optional[float] = None  # Battery level %
    bs: Optional[float] = None  # Battery status
    p: Optional[float] = None  # Pressure in hPa
    tid: Optional[str] = None  # Tracker ID
    t: Optional[str] = None  # Trigger (p=ping, c=circular, b=beacon, etc.)
    topic: Optional[str] = None
    inregions: Optional[list[str]] = None  # Geofence regions entered
    inregions_string: Optional[str] = None
    excluded: Optional[list[str]] = None  # Exited regions
    geofence: Optional[str] = None  # Named geofence (inferred if absent)

    model_config = {"populate_by_name": True}


# ── API responses ───────────────────────────────────────────────────


class LocationOut(BaseModel):
    """Public representation of a stored location."""

    id: int
    tst: int
    lat: float
    lon: float
    acc: Optional[float] = None
    alt: Optional[float] = None
    vel: Optional[float] = None
    batt: Optional[float] = None
    geofence: Optional[str] = None
    tid: Optional[str] = None
    t: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LocationList(BaseModel):
    """Paginated list of locations."""

    locations: list[LocationOut]
    total: int


class CurrentLocation(BaseModel):
    """Wrapper for a single current-location response."""

    location: Optional[LocationOut] = None


class PlaceOut(BaseModel):
    """Summary of a named place / geofence."""

    name: str
    lat: float
    lon: float
    rad: float = 0
    visit_count: int = 0


class PlacesList(BaseModel):
    """List of distinct places with visit counts."""

    places: list[PlaceOut]
    total: int


class StatsOut(BaseModel):
    """Aggregate statistics."""

    total_locations: int
    total_places: int
    earliest: Optional[int] = None
    latest: Optional[int] = None
    daily_average: Optional[float] = None


class StatusOut(BaseModel):
    """Service health / status response."""

    status: str = "ok"
    version: str = ""
    locations_stored: Optional[int] = None


class IngestionResponse(BaseModel):
    """Response after ingesting a location ping."""

    status: str
    location_id: Optional[int] = None
    message: str = ""
