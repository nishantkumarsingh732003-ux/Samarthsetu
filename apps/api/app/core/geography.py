"""District reference geography.

District names, state names and coordinates are **real** — district-headquarters
locations, accurate to roughly the town centre. Everything the partner seeder builds on
top of them (branch locations, capacity, contact details) is synthetic; see
scripts/seed/partners.py.

Lives in the API rather than the seeder because two callers need it: the seeder places
partners, and the conversational extractor recognises a district or state named in a
citizen's own words.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import NamedTuple


class District(NamedTuple):
    name: str
    state: str
    lat: float
    lng: float
    pincode: str


# 53 districts across 10 states. Coordinates are district-headquarters town centres.
DISTRICTS: tuple[District, ...] = (
    # --- Maharashtra ---
    District("Nagpur", "Maharashtra", 21.1458, 79.0882, "440001"),
    District("Pune", "Maharashtra", 18.5204, 73.8567, "411001"),
    District("Mumbai Suburban", "Maharashtra", 19.0760, 72.8777, "400051"),
    District("Nashik", "Maharashtra", 19.9975, 73.7898, "422001"),
    District("Chhatrapati Sambhajinagar", "Maharashtra", 19.8762, 75.3433, "431001"),
    District("Amravati", "Maharashtra", 20.9374, 77.7796, "444601"),
    District("Solapur", "Maharashtra", 17.6599, 75.9064, "413001"),
    District("Kolhapur", "Maharashtra", 16.7050, 74.2433, "416001"),
    # --- Bihar ---
    District("Patna", "Bihar", 25.5941, 85.1376, "800001"),
    District("Gaya", "Bihar", 24.7955, 85.0002, "823001"),
    District("Muzaffarpur", "Bihar", 26.1197, 85.3910, "842001"),
    District("Bhagalpur", "Bihar", 25.2425, 86.9842, "812001"),
    District("Darbhanga", "Bihar", 26.1542, 85.8918, "846004"),
    District("Purnia", "Bihar", 25.7771, 87.4753, "854301"),
    # --- Tamil Nadu ---
    District("Coimbatore", "Tamil Nadu", 11.0168, 76.9558, "641001"),
    District("Chennai", "Tamil Nadu", 13.0827, 80.2707, "600001"),
    District("Madurai", "Tamil Nadu", 9.9252, 78.1198, "625001"),
    District("Salem", "Tamil Nadu", 11.6643, 78.1460, "636001"),
    District("Tiruchirappalli", "Tamil Nadu", 10.7905, 78.7047, "620001"),
    District("Erode", "Tamil Nadu", 11.3410, 77.7172, "638001"),
    # --- Uttar Pradesh ---
    District("Lucknow", "Uttar Pradesh", 26.8467, 80.9462, "226001"),
    District("Kanpur Nagar", "Uttar Pradesh", 26.4499, 80.3319, "208001"),
    District("Varanasi", "Uttar Pradesh", 25.3176, 82.9739, "221001"),
    District("Agra", "Uttar Pradesh", 27.1767, 78.0081, "282001"),
    District("Prayagraj", "Uttar Pradesh", 25.4358, 81.8463, "211001"),
    District("Gorakhpur", "Uttar Pradesh", 26.7606, 83.3732, "273001"),
    # --- Karnataka ---
    District("Bengaluru Urban", "Karnataka", 12.9716, 77.5946, "560001"),
    District("Mysuru", "Karnataka", 12.2958, 76.6394, "570001"),
    District("Belagavi", "Karnataka", 15.8497, 74.4977, "590001"),
    District("Dharwad", "Karnataka", 15.4589, 75.0078, "580001"),
    District("Kalaburagi", "Karnataka", 17.3297, 76.8343, "585101"),
    # --- West Bengal ---
    District("Kolkata", "West Bengal", 22.5726, 88.3639, "700001"),
    District("Howrah", "West Bengal", 22.5958, 88.2636, "711101"),
    District("Darjeeling", "West Bengal", 27.0360, 88.2627, "734101"),
    District("Murshidabad", "West Bengal", 24.1750, 88.2800, "742101"),
    District("Purba Bardhaman", "West Bengal", 23.2324, 87.8615, "713101"),
    # --- Telangana ---
    District("Hyderabad", "Telangana", 17.3850, 78.4867, "500001"),
    District("Warangal", "Telangana", 17.9689, 79.5941, "506002"),
    District("Karimnagar", "Telangana", 18.4386, 79.1288, "505001"),
    District("Nizamabad", "Telangana", 18.6725, 78.0941, "503001"),
    # --- Rajasthan ---
    District("Jaipur", "Rajasthan", 26.9124, 75.7873, "302001"),
    District("Jodhpur", "Rajasthan", 26.2389, 73.0243, "342001"),
    District("Udaipur", "Rajasthan", 24.5854, 73.7125, "313001"),
    District("Kota", "Rajasthan", 25.2138, 75.8648, "324001"),
    District("Ajmer", "Rajasthan", 26.4499, 74.6399, "305001"),
    # --- Gujarat ---
    District("Ahmedabad", "Gujarat", 23.0225, 72.5714, "380001"),
    District("Surat", "Gujarat", 21.1702, 72.8311, "395003"),
    District("Vadodara", "Gujarat", 22.3072, 73.1812, "390001"),
    District("Rajkot", "Gujarat", 22.3039, 70.8022, "360001"),
    # --- Madhya Pradesh ---
    District("Bhopal", "Madhya Pradesh", 23.2599, 77.4126, "462001"),
    District("Indore", "Madhya Pradesh", 22.7196, 75.8577, "452001"),
    District("Jabalpur", "Madhya Pradesh", 23.1815, 79.9864, "482001"),
    District("Gwalior", "Madhya Pradesh", 26.2183, 78.1828, "474001"),
)

DISTRICTS_BY_STATE: dict[str, list[District]] = {}
for _d in DISTRICTS:
    DISTRICTS_BY_STATE.setdefault(_d.state, []).append(_d)

STATES: tuple[str, ...] = tuple(DISTRICTS_BY_STATE)


def district_by_name(name: str) -> District | None:
    for d in DISTRICTS:
        if d.name.casefold() == name.casefold():
            return d
    return None


EARTH_RADIUS_KM = 6371.0


def haversine_km(a: District, b: District) -> float:
    """Great-circle distance between two district centres."""
    lat1, lng1, lat2, lng2 = map(radians, (a.lat, a.lng, b.lat, b.lng))
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))


def nearest_districts(home: District, limit: int) -> list[District]:
    """The closest districts to `home` within the same state."""
    siblings = [d for d in DISTRICTS_BY_STATE[home.state] if d.name != home.name]
    siblings.sort(key=lambda d: haversine_km(home, d))
    return siblings[:limit]


# Lowercased lookup for recognising a place named in free text.
DISTRICT_LOOKUP: dict[str, District] = {d.name.casefold(): d for d in DISTRICTS}
STATE_LOOKUP: dict[str, str] = {s.casefold(): s for s in DISTRICTS_BY_STATE}
