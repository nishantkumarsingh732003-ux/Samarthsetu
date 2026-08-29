"""Cache key construction.

The key decides who shares a cached routing answer, so getting it wrong either serves
one citizen another's results or defeats the cache entirely.
"""

from app.core import cache
from app.core.routing_config import AMOUNT_BAND_SIZE, GEOHASH_PRECISION

NAGPUR = (21.1458, 79.0882)
PUNE = (18.5204, 73.8567)


def test_geohash_length_matches_configured_precision() -> None:
    assert len(cache.geohash(*NAGPUR)) == GEOHASH_PRECISION


def test_geohash_is_stable() -> None:
    assert cache.geohash(*NAGPUR) == cache.geohash(*NAGPUR)


def test_distant_cities_land_in_different_cells() -> None:
    assert cache.geohash(*NAGPUR) != cache.geohash(*PUNE)


def test_nearby_points_share_a_cell() -> None:
    """~5km cells: two citizens in the same neighbourhood get the same answer."""
    nudged = (NAGPUR[0] + 0.002, NAGPUR[1] + 0.002)
    assert cache.geohash(*NAGPUR) == cache.geohash(*nudged)


def test_known_geohash_value() -> None:
    """Pinned against the standard algorithm so a refactor cannot silently change it."""
    assert cache.geohash(57.64911, 10.40744, 5) == "u4pru"


def test_amount_is_bucketed() -> None:
    assert cache.amount_band(90000) == cache.amount_band(90000 + AMOUNT_BAND_SIZE - 1)
    assert cache.amount_band(90000) != cache.amount_band(90000 + AMOUNT_BAND_SIZE)


def test_similar_requests_share_a_key() -> None:
    a = cache.routing_key("NSFDC_MICRO_FINANCE", 90000, *NAGPUR, "Nagpur")
    b = cache.routing_key("NSFDC_MICRO_FINANCE", 92500, *NAGPUR, "Nagpur")
    assert a == b


def test_different_schemes_never_share_a_key() -> None:
    a = cache.routing_key("NSFDC_MICRO_FINANCE", 90000, *NAGPUR, "Nagpur")
    b = cache.routing_key("NSFDC_TERM_LOAN", 90000, *NAGPUR, "Nagpur")
    assert a != b


def test_key_is_namespaced_and_versioned() -> None:
    """A routing algorithm change must not serve stale results from the old one."""
    key = cache.routing_key("NSFDC_MICRO_FINANCE", 90000, *NAGPUR, "Nagpur")
    assert key.startswith("setu:route:v")


def test_district_only_requests_key_on_the_district() -> None:
    key = cache.routing_key("NSFDC_MICRO_FINANCE", 90000, None, None, "Nagpur")
    assert key.endswith("d:Nagpur")
