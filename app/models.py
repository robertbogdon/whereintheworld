"""SQLAlchemy ORM models."""
import geoalchemy2 as ga
from sqlalchemy import BigInteger, Column, DateTime, Double, Integer, Sequence, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Location(Base):
    """OwnTracks location ping."""

    __tablename__ = "locations"

    id = Column(BigInteger, Sequence("locations_id_seq"), primary_key=True)
    topic = Column(Text, nullable=True)
    tst = Column(BigInteger, nullable=False, index=True)
    lat = Column(Double, nullable=False)
    lon = Column(Double, nullable=False)
    acc = Column(Double, nullable=True)
    alt = Column(Double, nullable=True)
    vel = Column(Double, nullable=True)
    vac = Column(Double, nullable=True)
    conn = Column(Text, nullable=True)
    batt = Column(Double, nullable=True)
    bs = Column(Double, nullable=True)
    vel_accuracy = Column(Double, nullable=True)
    p = Column(Double, nullable=True)
    tid = Column(Text, nullable=True)
    t = Column(Text, nullable=True)
    inregions = Column(ARRAY(Text), nullable=True)
    inregions_string = Column(Text, nullable=True)
    excluded = Column(ARRAY(Text), nullable=True)
    geofence = Column(Text, nullable=True, index=True)
    geom = Column(ga.Geography("POINT", srid=4326), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


class Waypoint(Base):
    """Named places / geofences."""

    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, index=True)
    lat = Column(Double, nullable=False)
    lon = Column(Double, nullable=False)
    rad = Column(Double, nullable=False, server_default=text("0"))
    geom = Column(ga.Geography("POINT", srid=4326), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
