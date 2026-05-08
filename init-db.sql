-- init-db.sql
-- Bootstraps the WhereInTheWorld database schema.
-- Mounted into the postgis container's docker-entrypoint-initdb.d/
-- so it runs automatically on first container start.

-- Enable PostGIS on the database
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- LOCATIONS — individual OwnTracks pings
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
    id               BIGSERIAL PRIMARY KEY,
    topic            TEXT,
    tst              BIGINT NOT NULL,
    lat              DOUBLE PRECISION NOT NULL,
    lon              DOUBLE PRECISION NOT NULL,
    acc              DOUBLE PRECISION,
    alt              DOUBLE PRECISION,
    vel              DOUBLE PRECISION,
    vac              DOUBLE PRECISION,
    conn             TEXT,
    batt             DOUBLE PRECISION,
    bs               DOUBLE PRECISION,
    vel_accuracy     DOUBLE PRECISION,
    p                DOUBLE PRECISION,
    tid              TEXT,
    t                TEXT,
    inregions        TEXT[],
    inregions_string TEXT,
    excluded         TEXT[],
    geofence         TEXT,
    geom             GEOGRAPHY(Point, 4326) NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locations_tst          ON locations (tst DESC);
CREATE INDEX IF NOT EXISTS idx_locations_geofence     ON locations (geofence);
CREATE INDEX IF NOT EXISTS idx_locations_geom_gist    ON locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_locations_tst_geofence ON locations (tst DESC, geofence);
CREATE INDEX IF NOT EXISTS idx_locations_created_at   ON locations (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_locations_tid          ON locations (tid);

-- ============================================================
-- WAYPOINTS — named places / geofences (for future use)
-- ============================================================
CREATE TABLE IF NOT EXISTS waypoints (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    lat        DOUBLE PRECISION NOT NULL,
    lon        DOUBLE PRECISION NOT NULL,
    rad        DOUBLE PRECISION DEFAULT 0,
    geom       GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waypoints_name      ON waypoints (name);
CREATE INDEX IF NOT EXISTS idx_waypoints_geom_gist ON waypoints USING GIST (geom);

-- ============================================================
-- TRIGGERS — auto-compute geometry columns
-- ============================================================
CREATE OR REPLACE FUNCTION set_location_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.lon, NEW.lat), 4326)::geography;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_location_geom ON locations;
CREATE TRIGGER trg_set_location_geom
    BEFORE INSERT OR UPDATE OF lat, lon ON locations
    FOR EACH ROW
    EXECUTE FUNCTION set_location_geom();

CREATE OR REPLACE FUNCTION set_waypoint_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.lon, NEW.lat), 4326)::geography;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_waypoint_geom ON waypoints;
CREATE TRIGGER trg_set_waypoint_geom
    BEFORE INSERT OR UPDATE OF lat, lon ON waypoints
    FOR EACH ROW
    EXECUTE FUNCTION set_waypoint_geom();
