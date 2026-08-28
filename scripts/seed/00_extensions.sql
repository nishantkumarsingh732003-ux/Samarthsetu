-- Enabled on first container start (docker-entrypoint-initdb.d).
-- PostGIS backs channel_partners.geom; pgvector backs semantic scheme search.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
