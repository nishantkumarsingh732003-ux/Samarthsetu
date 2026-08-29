"""Channel Partner registry seeder.

=============================================================================
SYNTHETIC DEMO DATA — NOT THE OFFICIAL MoSJE CHANNEL PARTNER MASTER
=============================================================================

What is real:
  - District names, state names, and district-headquarters coordinates (geo.py).
  - The institution names. State Channelising Agencies, public sector banks, regional
    rural banks and NBFC-MFIs named here are the actual bodies that make up the
    Channel Finance System.
  - The authorisation pattern: which partner *type* typically handles which scheme
    family.

What is invented, and must not be quoted as fact about any named institution:
  - Every branch location, IFSC, phone number and email.
  - Every capacity figure: is_currently_accepting, avg_turnaround_days, active_load.
  - Every ticket-size band on an authorisation row.

Markers that make a record unmistakably synthetic:
  - IFSC codes embed "SETU" (e.g. SBIN0SETU07) and are not valid routing codes.
  - Contact emails use the reserved .invalid TLD, which can never resolve.
  - Every row carries contact.data_source = "SYNTHETIC".

Generation is deterministic: the same SEED produces the same 120 partners on every
run, so a demo is reproducible and a bug is re-triggerable.

Replace this wholesale once the official partner master is available.
"""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChannelPartner, PartnerSchemeAuthorisation, Scheme
from app.models.enums import PartnerType
from app.core.geography import DISTRICTS, DISTRICTS_BY_STATE, District, nearest_districts

SEED = 26092  # the problem statement number, so the seed itself is traceable
TARGET_PARTNERS = 120

MICRO = "NSFDC_MICRO_FINANCE"
TERM = "NSFDC_TERM_LOAN"
EDUCATION = "NSFDC_EDUCATION_LOAN"

# --- real institution names, by category -------------------------------------------

STATE_CHANNELISING_AGENCIES: dict[str, str] = {
    "Maharashtra": "Mahatma Phule Backward Class Development Corporation",
    "Bihar": "Bihar State Backward Classes Finance and Development Corporation",
    "Tamil Nadu": "Tamil Nadu Adi Dravidar Housing and Development Corporation",
    "Uttar Pradesh": "Uttar Pradesh Scheduled Castes Finance and Development Corporation",
    "Karnataka": "Dr. B. R. Ambedkar Development Corporation",
    "West Bengal": "West Bengal SC, ST and OBC Development and Finance Corporation",
    "Telangana": "Telangana Scheduled Castes Cooperative Development Corporation",
    "Rajasthan": "Rajasthan SC/ST Finance and Development Cooperative Corporation",
    "Gujarat": "Gujarat Scheduled Castes Development Corporation",
    "Madhya Pradesh": "Madhya Pradesh Antyavasayi Cooperative Development Committee",
}

PUBLIC_SECTOR_BANKS: tuple[tuple[str, str], ...] = (
    ("State Bank of India", "SBIN"),
    ("Punjab National Bank", "PUNB"),
    ("Bank of Baroda", "BARB"),
    ("Canara Bank", "CNRB"),
    ("Union Bank of India", "UBIN"),
    ("Bank of India", "BKID"),
    ("Indian Bank", "IDIB"),
    ("Central Bank of India", "CBIN"),
    ("UCO Bank", "UCBA"),
    ("Indian Overseas Bank", "IOBA"),
)

REGIONAL_RURAL_BANKS: dict[str, tuple[tuple[str, str], ...]] = {
    "Maharashtra": (("Maharashtra Gramin Bank", "MAHG"),
                    ("Vidharbha Konkan Gramin Bank", "VKGB")),
    "Bihar": (("Dakshin Bihar Gramin Bank", "DBGB"),
              ("Uttar Bihar Gramin Bank", "UBGB")),
    "Tamil Nadu": (("Tamil Nadu Grama Bank", "TNGB"),),
    "Uttar Pradesh": (("Baroda UP Bank", "BUPB"), ("Aryavart Bank", "ARYB")),
    "Karnataka": (("Karnataka Gramin Bank", "KRGB"),
                  ("Karnataka Vikas Grameena Bank", "KVGB")),
    "West Bengal": (("Bangiya Gramin Vikash Bank", "BGVB"),
                    ("Paschim Banga Gramin Bank", "PBGB")),
    "Telangana": (("Telangana Grameena Bank", "TGBK"),),
    "Rajasthan": (("Rajasthan Marudhara Gramin Bank", "RMGB"),
                  ("Baroda Rajasthan Kshetriya Gramin Bank", "BRKG")),
    "Gujarat": (("Baroda Gujarat Gramin Bank", "BGGB"),
                ("Saurashtra Gramin Bank", "SGBK")),
    "Madhya Pradesh": (("Madhya Pradesh Gramin Bank", "MPGB"),
                       ("Madhyanchal Gramin Bank", "MDGB")),
}

NBFC_MFIS: tuple[str, ...] = (
    "CreditAccess Grameen",
    "Satin Creditcare Network",
    "Spandana Sphoorty Financial",
    "Muthoot Microfin",
    "Asirvad Micro Finance",
    "Annapurna Finance",
    "Fusion Micro Finance",
    "Arohan Financial Services",
    "Svatantra Microfin",
)

# Large cities genuinely host many more Channel Partner branches than small district
# towns. Spreading 120 partners uniformly over 53 districts left major cities with a
# single branch, which is both unrealistic and makes routing look empty.
METRO_DISTRICTS: frozenset[str] = frozenset({
    "Mumbai Suburban", "Pune", "Nagpur", "Chennai", "Coimbatore", "Kolkata",
    "Bengaluru Urban", "Hyderabad", "Ahmedabad", "Surat", "Jaipur", "Lucknow",
    "Kanpur Nagar", "Patna", "Bhopal", "Indore",
})
METRO_WEIGHT = 8.0
DISTRICT_WEIGHT = 1.0

# Roughly the real shape of the network: many bank branches, one SCA per state.
TYPE_MIX: tuple[tuple[PartnerType, float], ...] = (
    (PartnerType.PSB, 0.42),
    (PartnerType.RRB, 0.24),
    (PartnerType.NBFC_MFI, 0.22),
    (PartnerType.SCA, 0.12),
)


def _synthetic_ifsc(prefix: str, index: int) -> str:
    """Deliberately invalid routing code carrying a SETU marker.

    Shape matches the CHECK constraint (^[A-Z]{4}0[A-Z0-9]{6}$) so the row is storable,
    but "SETU" in the branch segment makes it obviously not a real branch code.
    """
    return f"{prefix[:4].upper()}0SETU{index % 100:02d}"


def _jitter(rng: random.Random, lat: float, lng: float) -> tuple[float, float]:
    """Scatter a branch a few km around the district centre."""
    return lat + rng.uniform(-0.09, 0.09), lng + rng.uniform(-0.09, 0.09)


def _authorisations(
    rng: random.Random, partner_type: PartnerType, district: District
) -> list[dict[str, Any]]:
    """Which schemes this partner may process, and on what terms.

    The pattern mirrors how the Channel Finance System actually divides work:
      - SCAs carry the enterprise schemes (micro finance and term loan) but not
        education, which routes through the banking channel.
      - PSBs carry education and term loans; a minority also do micro finance.
      - RRBs sit close to the ground: micro finance always, term loans often, no
        education.
      - NBFC-MFIs do micro finance only, and at small ticket sizes.

    Those gaps are the whole point. A partner with no row for a scheme is not
    authorised for it, and that is exactly what the routing engine reports as
    `why_not` when it excludes a branch that is otherwise nearby.
    """
    service = _service_districts(rng, district)

    def row(code: str, lo: int, hi: int) -> dict[str, Any]:
        return {
            "scheme_code": code,
            "min_ticket": lo,
            "max_ticket": hi,
            # ~15% of authorisations are paused for exhausted capacity.
            "is_currently_accepting": rng.random() > 0.15,
            "avg_turnaround_days": rng.randint(7, 45),
            "active_load": rng.randint(0, 100),
            "service_districts": service,
        }

    if partner_type is PartnerType.SCA:
        rows = [row(MICRO, 10000, 125000), row(TERM, 140001, 4500000)]
        # A small number of SCAs are also cleared for education.
        if rng.random() < 0.20:
            rows.append(row(EDUCATION, 50000, 4000000))
        return rows

    if partner_type is PartnerType.PSB:
        rows = [row(EDUCATION, 50000, 4000000), row(TERM, 140001, 4500000)]
        if rng.random() < 0.35:
            rows.append(row(MICRO, 25000, 125000))
        return rows

    if partner_type is PartnerType.RRB:
        rows = [row(MICRO, 10000, 125000)]
        if rng.random() < 0.60:
            rows.append(row(TERM, 140001, 2500000))
        return rows

    # NBFC-MFI: micro finance only, and a low ceiling.
    return [row(MICRO, 5000, rng.choice([60000, 75000, 90000, 100000]))]


def _service_districts(rng: random.Random, home: District) -> list[str]:
    """The home district plus its one or two NEAREST neighbours in the same state.

    Picking neighbours at random would let a Mumbai branch claim to serve Nagpur, 700km
    away, and the router would then rank it for a Nagpur citizen. A service area has to
    be geographically real or the routing built on it is fiction.
    """
    neighbours = nearest_districts(home, rng.randint(1, 2))
    return [home.name, *(d.name for d in neighbours)]


def _build_partners(rng: random.Random) -> list[dict[str, Any]]:
    """Deterministically construct the whole registry before touching the database.

    Built in three passes so coverage is guaranteed rather than left to chance:
      1. One State Channelising Agency per state — every state has enterprise coverage.
      2. One partner in every district — no district is left with zero partners, so
         "no partner nearby" in the routing output is a real finding, not a seed gap.
      3. The remainder weighted towards large cities, which is where branches actually
         cluster.
    """
    partners: list[dict[str, Any]] = []
    covered: set[str] = set()

    for state, org in STATE_CHANNELISING_AGENCIES.items():
        district = DISTRICTS_BY_STATE[state][0]
        partners.append(_make(rng, PartnerType.SCA, org, district, len(partners)))
        covered.add(district.name)

    types, weights = zip(*TYPE_MIX, strict=True)

    for district in DISTRICTS:
        if district.name in covered:
            continue
        partner_type = rng.choices(types, weights=weights, k=1)[0]
        partners.append(
            _make(rng, partner_type, _org_for(rng, partner_type, district), district, len(partners))
        )
        covered.add(district.name)

    density = [
        METRO_WEIGHT if d.name in METRO_DISTRICTS else DISTRICT_WEIGHT for d in DISTRICTS
    ]
    while len(partners) < TARGET_PARTNERS:
        district = rng.choices(DISTRICTS, weights=density, k=1)[0]
        partner_type = rng.choices(types, weights=weights, k=1)[0]

        partners.append(
            _make(rng, partner_type, _org_for(rng, partner_type, district), district, len(partners))
        )

    return partners


def _org_for(rng: random.Random, partner_type: PartnerType, district: District) -> str:
    if partner_type is PartnerType.SCA:
        return STATE_CHANNELISING_AGENCIES[district.state]
    if partner_type is PartnerType.PSB:
        return rng.choice(PUBLIC_SECTOR_BANKS)[0]
    if partner_type is PartnerType.RRB:
        return rng.choice(REGIONAL_RURAL_BANKS[district.state])[0]
    return rng.choice(NBFC_MFIS)


def _make(
    rng: random.Random, partner_type: PartnerType, org: str, district: District, index: int
) -> dict[str, Any]:
    lat, lng = _jitter(rng, district.lat, district.lng)

    if partner_type is PartnerType.SCA:
        name = f"{org} — {district.name} District Office"
        ifsc = None
        prefix = None
    elif partner_type is PartnerType.PSB:
        prefix = next(p for n, p in PUBLIC_SECTOR_BANKS if n == org)
        name = f"{org}, {district.name} Main Branch"
        ifsc = _synthetic_ifsc(prefix, index)
    elif partner_type is PartnerType.RRB:
        prefix = next(
            p for n, p in REGIONAL_RURAL_BANKS[district.state] if n == org
        )
        name = f"{org}, {district.name} Branch"
        ifsc = _synthetic_ifsc(prefix, index)
    else:
        name = f"{org} — {district.name} Service Centre"
        ifsc = None

    slug = district.name.split()[0].lower()
    return {
        "name": name,
        "type": partner_type,
        "parent_org": org,
        "ifsc": ifsc,
        "address": f"{rng.randint(1, 240)}, Main Road, {district.name}, {district.state}",
        "district": district.name,
        "state": district.state,
        "pincode": district.pincode,
        "lat": lat,
        "lng": lng,
        "contact": {
            # .invalid is reserved by RFC 2606 and can never resolve.
            "phone": f"+91-{rng.randint(70, 99)}{rng.randint(10000000, 99999999)}",
            "email": f"{slug}.{index:03d}@setu-demo.invalid",
            "data_source": "SYNTHETIC",
        },
        "authorisations": _authorisations(rng, partner_type, district),
    }


async def seed_partners(session: AsyncSession) -> str:
    """Replace the partner registry with a deterministic synthetic network."""
    scheme_ids = {
        code: sid
        for code, sid in (await session.execute(select(Scheme.code, Scheme.id))).all()
    }
    if not scheme_ids:
        raise SystemExit("Seed schemes before partners: python scripts/seed/run.py schemes")

    # Wholesale replacement keeps the seeder idempotent without merge ambiguity.
    await session.execute(delete(PartnerSchemeAuthorisation))
    await session.execute(delete(ChannelPartner))

    rng = random.Random(SEED)
    specs = _build_partners(rng)

    auth_count = 0
    paused = 0
    for spec in specs:
        auths = spec.pop("authorisations")
        lat = spec.pop("lat")
        lng = spec.pop("lng")
        partner = ChannelPartner(
            **spec,
            geom=f"SRID=4326;POINT({lng} {lat})",
            is_active=True,
        )
        session.add(partner)
        await session.flush()

        for auth in auths:
            code = auth.pop("scheme_code")
            session.add(
                PartnerSchemeAuthorisation(
                    partner_id=partner.id, scheme_id=scheme_ids[code], **auth
                )
            )
            auth_count += 1
            if not auth["is_currently_accepting"]:
                paused += 1

    by_type: dict[str, int] = {}
    for spec in specs:
        by_type[str(spec["type"])] = by_type.get(str(spec["type"]), 0) + 1
    mix = " ".join(f"{k}={v}" for k, v in sorted(by_type.items()))

    states = len({s["state"] for s in specs})
    return (
        f"{len(specs)} partners across {states} states ({mix}), "
        f"{auth_count} authorisations, {paused} paused for capacity"
    )
