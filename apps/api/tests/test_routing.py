"""Routing scorer and rejection logic.

These run without a database: they exercise the pure functions that decide *why* a
partner is ranked or excluded, which is the part a citizen actually reads.
"""

from types import SimpleNamespace

import pytest

from app.core.routing_config import (
    MAX_SERVICE_RADIUS_KM,
    MAX_USEFUL_DISTANCE_KM,
    TYPE_AFFINITY,
    WEIGHTS,
)
from app.models.enums import PartnerType, SchemeFamily
from app.services import routing


def partner(**kw):
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        name="Test Branch",
        type=PartnerType.PSB,
        parent_org="Test Bank",
        ifsc="TEST0SETU01",
        address="1, Main Road, Nagpur",
        district="Nagpur",
        state="Maharashtra",
        pincode="440001",
        contact={"data_source": "SYNTHETIC"},
    )
    return SimpleNamespace(**{**base, **kw})


def auth(**kw):
    base = dict(
        min_ticket=10000,
        max_ticket=125000,
        is_currently_accepting=True,
        avg_turnaround_days=20,
        active_load=40,
        service_districts=["Nagpur"],
    )
    return SimpleNamespace(**{**base, **kw})


SCHEME = SimpleNamespace(
    code="NSFDC_MICRO_FINANCE",
    official_name="Micro Finance Scheme",
    family=SchemeFamily.MICRO_FINANCE,
)


# ------------------------------------------------------------------ score components


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_distance_score_falls_with_distance() -> None:
    assert routing._distance_score(0) == 1.0
    assert routing._distance_score(MAX_USEFUL_DISTANCE_KM) == 0.0
    assert routing._distance_score(MAX_USEFUL_DISTANCE_KM * 2) == 0.0
    assert routing._distance_score(10) > routing._distance_score(30)


def test_unknown_values_score_neutral_never_as_a_bonus() -> None:
    """A partner must not win by having no data."""
    assert routing._distance_score(None) == 0.5
    assert routing._turnaround_score(None) == 0.5
    assert routing._load_score(None) == 0.5


def test_faster_turnaround_scores_higher() -> None:
    assert routing._turnaround_score(7) == 1.0
    assert routing._turnaround_score(45) == 0.0
    assert routing._turnaround_score(10) > routing._turnaround_score(40)


def test_busier_partner_scores_lower() -> None:
    assert routing._load_score(0) == 1.0
    assert routing._load_score(100) == 0.0
    assert routing._load_score(20) > routing._load_score(80)


def test_nbfc_mfi_is_preferred_for_micro_finance() -> None:
    micro = TYPE_AFFINITY[SchemeFamily.MICRO_FINANCE]
    assert micro[PartnerType.NBFC_MFI] == max(micro.values())


def test_psb_is_preferred_for_education() -> None:
    education = TYPE_AFFINITY[SchemeFamily.EDUCATION_LOAN]
    assert education[PartnerType.PSB] == max(education.values())
    assert education[PartnerType.NBFC_MFI] == min(education.values())


def test_score_breakdown_contributions_sum_to_the_total() -> None:
    """The UI shows the components; they must actually add up to the headline score."""
    result = routing._score(partner(), auth(), SCHEME, distance_km=5.0)
    total = sum(c["contribution"] for c in result.score_breakdown.values())
    assert abs(total - result.score) < 0.001


def test_every_component_is_returned_with_its_raw_value() -> None:
    result = routing._score(partner(), auth(avg_turnaround_days=12), SCHEME, 5.0)
    assert set(result.score_breakdown) == {"distance", "turnaround", "type_affinity", "load"}
    assert result.score_breakdown["turnaround"]["value"] == 12
    assert result.score_breakdown["distance"]["value"] == 5.0


# --------------------------------------------------------------------- why_not logic


def test_missing_authorisation_is_the_rejection_not_an_error() -> None:
    """A NULL authorisation row means "not authorised", and that is reportable."""
    rejection = routing._reject_reason(partner(), None, SCHEME, 90000, "Nagpur", 1.2)
    assert rejection is not None
    assert rejection.reason_code == "NOT_AUTHORISED"
    assert "not authorised" in rejection.reason
    assert "1.2 km" in rejection.reason


def test_paused_capacity_is_reported_separately_from_not_authorised() -> None:
    rejection = routing._reject_reason(
        partner(), auth(is_currently_accepting=False), SCHEME, 90000, "Nagpur", 2.0
    )
    assert rejection.reason_code == "NOT_ACCEPTING"


def test_amount_below_and_above_the_ticket_band_are_distinguished() -> None:
    below = routing._reject_reason(
        partner(), auth(min_ticket=50000), SCHEME, 10000, "Nagpur", 1.0
    )
    above = routing._reject_reason(
        partner(), auth(max_ticket=60000), SCHEME, 90000, "Nagpur", 1.0
    )
    assert below.reason_code == "BELOW_MIN_TICKET"
    assert above.reason_code == "ABOVE_MAX_TICKET"
    assert "60,000" in above.reason


def test_partner_beyond_the_service_radius_is_rejected_not_merely_downranked() -> None:
    rejection = routing._reject_reason(
        partner(), auth(), SCHEME, 90000, "Nagpur", MAX_SERVICE_RADIUS_KM + 1
    )
    assert rejection.reason_code == "TOO_FAR"


def test_district_outside_the_service_area_is_rejected() -> None:
    rejection = routing._reject_reason(
        partner(), auth(service_districts=["Pune"]), SCHEME, 90000, "Nagpur", 5.0
    )
    assert rejection.reason_code == "DISTRICT_NOT_SERVED"
    assert "Pune" in rejection.reason


def test_an_eligible_partner_is_not_rejected() -> None:
    assert routing._reject_reason(partner(), auth(), SCHEME, 90000, "Nagpur", 5.0) is None


def test_authorisation_is_checked_before_capacity() -> None:
    """"They don't do this scheme" is the fact that misroutes people, so it leads."""
    rejection = routing._reject_reason(None or partner(), None, SCHEME, 90000, "Nagpur", 1.0)
    assert rejection.reason_code == "NOT_AUTHORISED"


@pytest.mark.parametrize("amount", [10000, 125000])
def test_ticket_band_boundaries_are_inclusive(amount: int) -> None:
    assert routing._reject_reason(partner(), auth(), SCHEME, amount, "Nagpur", 5.0) is None
