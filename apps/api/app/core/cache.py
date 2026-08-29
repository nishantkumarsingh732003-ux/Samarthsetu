"""Redis cache for partner routing, with a dependency-free geohash.

Routing is read-heavy and the answer barely changes between two citizens standing in
the same neighbourhood asking for a similar amount, so results are cached on
(scheme, amount band, geohash cell).

The cache is strictly an optimisation. Every failure path — Redis down, malformed
payload, connection refused — falls through to a live query rather than erroring, so a
Redis outage slows the service down instead of taking it off the air.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings
from app.core.routing_config import (
    AMOUNT_BAND_SIZE,
    CACHE_TTL_SECONDS,
    GEOHASH_PRECISION,
    ROUTING_VERSION,
)

logger = logging.getLogger(__name__)

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def geohash(lat: float, lng: float, precision: int = GEOHASH_PRECISION) -> str:
    """Standard geohash. ~25 lines beats adding a dependency for one function."""
    lat_range = [-90.0, 90.0]
    lng_range = [-180.0, 180.0]
    out: list[str] = []
    bits = 0
    bit_count = 0
    use_lng = True

    while len(out) < precision:
        if use_lng:
            mid = sum(lng_range) / 2
            if lng > mid:
                bits = (bits << 1) | 1
                lng_range[0] = mid
            else:
                bits <<= 1
                lng_range[1] = mid
        else:
            mid = sum(lat_range) / 2
            if lat > mid:
                bits = (bits << 1) | 1
                lat_range[0] = mid
            else:
                bits <<= 1
                lat_range[1] = mid

        use_lng = not use_lng
        bit_count += 1
        if bit_count == 5:
            out.append(_BASE32[bits])
            bits = 0
            bit_count = 0

    return "".join(out)


def amount_band(amount: float) -> int:
    """Bucket the amount so near-identical requests share a cache entry."""
    return int(amount // AMOUNT_BAND_SIZE) * AMOUNT_BAND_SIZE


def routing_key(
    scheme_code: str, amount: float, lat: float | None, lng: float | None, district: str | None
) -> str:
    cell = geohash(lat, lng) if lat is not None and lng is not None else f"d:{district or '-'}"
    return f"setu:route:v{ROUTING_VERSION}:{scheme_code}:{amount_band(amount)}:{cell}"


async def cache_get(key: str) -> Any | None:
    try:
        raw = await get_client().get(key)
    except Exception as exc:  # noqa: BLE001 - cache must never break the request
        logger.warning("routing cache read failed, serving live: %s", exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("discarding malformed cache entry %s", key)
        return None


async def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    try:
        await get_client().set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:  # noqa: BLE001 - cache must never break the request
        logger.warning("routing cache write failed: %s", exc)


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
