"""Partner routing weights and thresholds.

Every number here is a policy choice, not an implementation detail, so it lives in one
readable place. The routing response returns each component's raw value *and* its
normalised score, so a citizen can be shown exactly why one branch outranked another
and a ministry reviewer can argue with the weights rather than the code.
"""

from __future__ import annotations

from app.models.enums import PartnerType, SchemeFamily

# Composite score weights. Must sum to 1.0 (asserted below).
WEIGHTS: dict[str, float] = {
    "distance": 0.40,
    "turnaround": 0.25,
    "type_affinity": 0.20,
    "load": 0.15,
}

# A partner beyond this is not a usable answer for a citizen travelling to a branch,
# however good its turnaround. Exceeding it is a rejection with a stated reason, not a
# low score — and "no partner within range" is itself the finding that Phase 6 surfaces
# as an underserved district.
MAX_SERVICE_RADIUS_KM = 150.0

# Beyond this, extra distance stops mattering — a citizen who must travel 60km is in
# the same practical position as one who must travel 90km.
MAX_USEFUL_DISTANCE_KM = 50.0

# The turnaround range the seed data spans; used to normalise days into a 0-1 score.
FASTEST_TURNAROUND_DAYS = 7
SLOWEST_TURNAROUND_DAYS = 45

# How many nearest partners to pull before filtering. Large enough that the `why_not`
# list has genuinely nearby rejects to talk about.
CANDIDATE_LIMIT = 60

TOP_N_RESULTS = 5
TOP_N_WHY_NOT = 3

# Which partner type suits which scheme family, 0.0-1.0.
#
# NBFC-MFIs are built for small-ticket doorstep lending, so they lead on micro finance.
# Education lending is a banking-channel product, so PSBs lead there and NBFC-MFIs do
# not appear at all. SCAs are the state's own agencies and are strong across the two
# enterprise schemes.
TYPE_AFFINITY: dict[SchemeFamily, dict[PartnerType, float]] = {
    SchemeFamily.MICRO_FINANCE: {
        PartnerType.NBFC_MFI: 1.00,
        PartnerType.RRB: 0.85,
        PartnerType.SCA: 0.70,
        PartnerType.PSB: 0.50,
    },
    SchemeFamily.TERM_LOAN: {
        PartnerType.SCA: 1.00,
        PartnerType.PSB: 0.85,
        PartnerType.RRB: 0.70,
        PartnerType.NBFC_MFI: 0.30,
    },
    SchemeFamily.EDUCATION_LOAN: {
        PartnerType.PSB: 1.00,
        PartnerType.SCA: 0.65,
        PartnerType.RRB: 0.50,
        PartnerType.NBFC_MFI: 0.10,
    },
}

# Redis cache on routing results.
CACHE_TTL_SECONDS = 600
# Amount is bucketed before it enters the cache key, so two citizens asking for
# Rs 88,000 and Rs 90,000 share a cached result.
AMOUNT_BAND_SIZE = 10000
GEOHASH_PRECISION = 5  # ~4.9km x 4.9km cells

ROUTING_VERSION = "1.0.0"

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "routing weights must sum to 1.0"
