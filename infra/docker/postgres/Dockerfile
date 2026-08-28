# CLAUDE.md requires PostGIS (partner geo) and pgvector (semantic search) in one
# Postgres 16. No published image ships both, so we add pgvector to the PostGIS image.
FROM postgis/postgis:16-3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
