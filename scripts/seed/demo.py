"""One command that builds the whole demo world.

    python scripts/seed/demo.py            # reset the citizen-side data and rebuild
    python scripts/seed/demo.py --keep     # add to what is already there

CLAUDE.md rule 6: no mock data in the demo path. Every screen a reviewer opens is
populated from the real database by running the real code — the personas below go
through `matching.run_match`, `routing.find_partners` and `applications.create_application`,
the same functions the API calls, so the verdicts on screen are produced by the engine
rather than written into a fixture. If a rule changes, this seed's output changes with it.

**What "reset" means.** Schemes, partners and console logins are left alone; they are
reference data seeded elsewhere. What is cleared is everything a citizen generated:
applications, documents, notifications, citizens, consents, match runs, and the audit
log. `match_runs` is normally never deleted — it is the reproducibility record — so this
script is the one place allowed to, and only because a demo reset is not a production
operation. That exception is deliberate and stated rather than silent.

The three personas are the problem statement in miniature:

  Sunita   Nagpur       vegetable cart   Rs 80,000     -> Micro Finance
  Ramesh   Patna        furniture works  Rs 12,00,000  -> Term Loan, redirected off Micro Finance
  Anjali   Coimbatore   BSc student      Rs 6,00,000   -> Educational Loan

One per scheme family, three states, three languages, and Ramesh is the one who proves
the point: a citizen who would have walked into the wrong queue is told which scheme
actually fits before he goes anywhere.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# `scripts` is imported as a package, so its parent must be on the path. The container
# puts the API at /app; a host checkout puts it at <repo>/apps/api.
_HERE = Path(__file__).resolve()
for candidate in (_HERE.parents[2], Path("/app"), _HERE.parents[2] / "apps" / "api"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import Application, ChannelPartner, Scheme  # noqa: E402
from app.models.enums import ApplicationStatus, DocumentValidationStatus  # noqa: E402
from app.models.application import Document  # noqa: E402
from app.services import applications as application_service  # noqa: E402
from app.services import citizens as citizen_service  # noqa: E402
from app.services import matching, routing  # noqa: E402

# A fixed seed so the demo world is the same every time it is built. A reviewer who saw
# 14 applications under appraisal yesterday should see 14 today.
RANDOM_SEED = 26092  # the problem statement number, for luck

TOTAL_APPLICATIONS = 40

PERSONAS: list[dict[str, Any]] = [
    {
        "name": "Sunita Devi",
        "language": "hi",
        "district": "Nagpur",
        "state": "Maharashtra",
        "phone": "9876500001",
        "gov_id": "2345 6789 0123",
        "amount": 72000,
        "profile": {
            "category": "SC",
            "project_sector": "TRADE",
            "occupation_type": "Vegetable vendor",
            "annual_family_income": 180000,
            "project_cost": 80000,
        },
        # Where she should end up, asserted below rather than assumed.
        "expect_family": "MICRO_FINANCE",
        "documents": ["CASTE_CERTIFICATE", "INCOME_CERTIFICATE", "IDENTITY_PROOF"],
        "advance_to": ApplicationStatus.PARTNER_ACKNOWLEDGED,
    },
    {
        "name": "Ramesh Kumar",
        "language": "hi",
        "district": "Patna",
        "state": "Bihar",
        "phone": "9876500002",
        "gov_id": "3456 7890 1234",
        "amount": 1080000,
        "profile": {
            "category": "SC",
            "project_sector": "MANUFACTURING",
            "occupation_type": "Furniture workshop",
            "annual_family_income": 420000,
            "project_cost": 1200000,
        },
        "expect_family": "TERM_LOAN",
        # The one that carries the pitch: he asked about the scheme everyone has heard
        # of, and the engine sent him to the one that actually fits.
        "expect_redirect_from": "NSFDC_MICRO_FINANCE",
        "documents": [
            "CASTE_CERTIFICATE", "INCOME_CERTIFICATE", "IDENTITY_PROOF",
            "ADDRESS_PROOF", "PROJECT_REPORT",
        ],
        "advance_to": ApplicationStatus.UNDER_APPRAISAL,
    },
    {
        "name": "Anjali R",
        "language": "ta",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "phone": "9876500003",
        "gov_id": "4567 8901 2345",
        "amount": 540000,
        "profile": {
            "category": "SC",
            "project_sector": "EDUCATION",
            "education_level": "Higher secondary",
            "admission_confirmed": True,
            "annual_family_income": 260000,
            "project_cost": 600000,
        },
        "expect_family": "EDUCATION_LOAN",
        "documents": [
            "CASTE_CERTIFICATE", "INCOME_CERTIFICATE", "IDENTITY_PROOF",
            "ADMISSION_LETTER", "FEE_STRUCTURE",
        ],
        "advance_to": ApplicationStatus.SANCTIONED,
    },
]

# The background population. Names and districts are synthetic; the *distribution* is
# what matters, because the ministry dashboard reads it.
BACKGROUND_DISTRICTS = [
    ("Nagpur", "Maharashtra", "mr"), ("Mumbai Suburban", "Maharashtra", "mr"),
    ("Patna", "Bihar", "hi"), ("Lucknow", "Uttar Pradesh", "hi"),
    ("Bhopal", "Madhya Pradesh", "hi"), ("Indore", "Madhya Pradesh", "hi"),
    ("Coimbatore", "Tamil Nadu", "ta"), ("Chennai", "Tamil Nadu", "ta"),
    ("Hyderabad", "Telangana", "te"), ("Kolkata", "West Bengal", "bn"),
]

GIVEN_NAMES = [
    "Kavita", "Suresh", "Lakshmi", "Manoj", "Priya", "Ashok", "Rekha", "Vijay",
    "Sarita", "Dinesh", "Meena", "Rajesh", "Sunanda", "Prakash", "Geeta", "Naresh",
    "Shanti", "Mahesh", "Radha", "Arun",
]
FAMILY_NAMES = ["Kamble", "Yadav", "Paswan", "Murugan", "Das", "Sonkar", "Jatav", "Mandal"]

# Where the background applications sit. Weighted to look like a real pipeline: most
# recent ones are still waiting, a few have been decided, and some were refused — a
# funnel with no rejections in it is not a funnel anyone should believe.
STATUS_MIX: list[tuple[ApplicationStatus, int]] = [
    (ApplicationStatus.SUBMITTED, 9),
    (ApplicationStatus.PARTNER_ACKNOWLEDGED, 8),
    (ApplicationStatus.DOCS_REQUESTED, 6),
    (ApplicationStatus.UNDER_APPRAISAL, 6),
    (ApplicationStatus.SANCTIONED, 4),
    (ApplicationStatus.DISBURSED, 2),
    (ApplicationStatus.REJECTED, 2),
]

REJECTION_REASONS = [
    "Income certificate is dated 2019 and the branch needs one from this year.",
    "The project report does not show how the loan would be repaid.",
]
DOCS_REASONS = [
    "Caste certificate is not readable in the photo sent.",
    "Bank passbook page showing the IFSC is missing.",
    "Please add a passport-size photograph.",
]

# The shortest legal path from SUBMITTED to each end state. The lifecycle refuses a
# jump, so the demo walks the same ladder a real application does.
PATH: dict[ApplicationStatus, list[ApplicationStatus]] = {
    ApplicationStatus.SUBMITTED: [],
    ApplicationStatus.PARTNER_ACKNOWLEDGED: [ApplicationStatus.PARTNER_ACKNOWLEDGED],
    ApplicationStatus.DOCS_REQUESTED: [
        ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.DOCS_REQUESTED,
    ],
    ApplicationStatus.UNDER_APPRAISAL: [
        ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.UNDER_APPRAISAL,
    ],
    ApplicationStatus.SANCTIONED: [
        ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.UNDER_APPRAISAL,
        ApplicationStatus.SANCTIONED,
    ],
    ApplicationStatus.DISBURSED: [
        ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.UNDER_APPRAISAL,
        ApplicationStatus.SANCTIONED, ApplicationStatus.DISBURSED,
    ],
    ApplicationStatus.REJECTED: [
        ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.REJECTED,
    ],
}


class DemoSeedError(RuntimeError):
    pass


async def reset(session: AsyncSession) -> None:
    """Clear everything a citizen generated. Reference data is left alone."""
    # Order matters only where there is no cascade; TRUNCATE ... CASCADE handles it.
    await session.execute(
        text(
            "TRUNCATE notifications, documents, applications, citizen_profiles, "
            "citizens, consents, match_runs, audit_log RESTART IDENTITY CASCADE"
        )
    )
    await session.commit()
    print("  reset: applications, documents, notifications, citizens, consents, "
          "match_runs and audit_log cleared")


async def _require_reference_data(session: AsyncSession) -> None:
    schemes = (await session.execute(select(Scheme))).scalars().all()
    partners = (await session.execute(select(ChannelPartner))).scalars().all()
    if len(schemes) < 3:
        raise DemoSeedError(
            "Fewer than three schemes are loaded. Run `python scripts/seed/run.py` first."
        )
    if len(partners) < 50:
        raise DemoSeedError(
            f"Only {len(partners)} Channel Partners are loaded. "
            "Run `python scripts/seed/run.py` first."
        )


async def _journey(
    session: AsyncSession,
    *,
    name: str,
    language: str,
    district: str,
    state: str,
    profile: dict[str, Any],
    amount: float,
    phone: str | None = None,
    gov_id: str | None = None,
    actor: str = "demo-seed",
) -> tuple[Application, dict[str, Any], str | None]:
    """One citizen, start to finish, through the real services.

    Returns the application, the engine payload, and the partner's name. Nothing here
    writes a verdict by hand — `run_match` decides and `find_partners` routes, so the
    demo world is only ever as correct as the product is.
    """
    engine_payload = await matching.run_match(
        session, profile=profile, language=language, citizen_id=None, actor=actor
    )
    top = engine_payload["results"][0]

    route = await routing.find_partners(
        session,
        scheme_code=top["scheme_code"],
        amount=amount,
        district=district,
        actor=actor,
        match_run_id=engine_payload["match_run_id"],
    )
    if not route["partners"]:
        raise DemoSeedError(
            f"No authorised partner for {top['scheme_code']} in {district}; "
            "the demo world would have a hole in it."
        )
    partner = route["partners"][0]

    consent = await citizen_service.record_consent(
        session, granted=True, purpose="scheme_eligibility_and_partner_routing", ip=None
    )
    citizen = await citizen_service.create_citizen(
        session,
        consent=consent,
        display_name=name,
        phone=phone,
        gov_id_type="AADHAAR" if gov_id else None,
        gov_id=gov_id,
        district=district,
        state=state,
        preferred_language=language,
        actor=actor,
    )

    application = await application_service.create_application(
        session,
        citizen_id=citizen.id,
        scheme_code=top["scheme_code"],
        partner_id=uuid.UUID(partner["partner_id"]),
        amount_requested=amount,
        match_run_id=uuid.UUID(engine_payload["match_run_id"]),
        engine_version=engine_payload["engine_version"],
        actor=actor,
    )
    return application, engine_payload, partner["name"]


async def _attach_documents(
    session: AsyncSession, application: Application, doc_types: list[str], rng: random.Random
) -> None:
    """Uploaded documents, without inventing an OCR result.

    `redaction_applied` is set only for ID-bearing types, which is what the real
    pipeline would produce. `ocr_extract` carries a note saying the text was not
    extracted here rather than a plausible-looking fake — a demo that fabricates an OCR
    reading is a demo that will be believed about something it did not do.
    """
    for doc_type in doc_types:
        warning = rng.random() < 0.25
        session.add(
            Document(
                application_id=application.id,
                doc_type=doc_type,
                storage_key=f"applications/{application.id}/demo-{doc_type.lower()}.png",
                ocr_extract={
                    "seeded": True,
                    "note": "Demo record. No OCR was run; upload a real photo to exercise it.",
                    "warnings": (
                        [{"code": "POSSIBLY_EXPIRED",
                          "message": "This appears to be dated 2019. Most partners require "
                                     "one issued within the last 6 months."}]
                        if warning else []
                    ),
                },
                validation_status=(
                    DocumentValidationStatus.WARNING if warning
                    else DocumentValidationStatus.PASSED
                ),
                redaction_applied=doc_type in {"IDENTITY_PROOF", "ADDRESS_PROOF"},
            )
        )
    await session.flush()


async def _advance(
    session: AsyncSession,
    application: Application,
    target: ApplicationStatus,
    rng: random.Random,
) -> None:
    """Walk the real lifecycle to `target`. Illegal jumps are refused by the service."""
    for step in PATH[target]:
        reason = None
        if step is ApplicationStatus.REJECTED:
            reason = rng.choice(REJECTION_REASONS)
        elif step is ApplicationStatus.DOCS_REQUESTED:
            reason = rng.choice(DOCS_REASONS)
        await application_service.transition(
            session, application, step, actor="partner:demo-officer", reason=reason
        )


async def _backdate(session: AsyncSession, application: Application, days: int) -> None:
    """Spread the world across a few weeks so the SLA clock and turnaround mean something.

    Written with SQL rather than through the model because `created_at` has a server
    default and `updated_at` an onupdate — the ORM would overwrite both on flush.
    """
    # `make_interval(days => :d)` rather than string concatenation: asyncpg infers the
    # parameter type from the expression, and `:d || ' days'` types it as text, so an
    # int argument is rejected outright.
    await session.execute(
        text(
            "UPDATE applications "
            "SET created_at = now() - make_interval(days => :d), "
            "    updated_at = now() - make_interval(days => :d) + interval '2 days' "
            "WHERE id = :id"
        ),
        {"d": days, "id": application.id},
    )


async def seed_demo(session: AsyncSession, *, keep: bool = False) -> None:
    rng = random.Random(RANDOM_SEED)

    await _require_reference_data(session)
    if not keep:
        await reset(session)

    # --- the three personas ---------------------------------------------------------
    print("\n  personas")
    for persona in PERSONAS:
        application, payload, partner_name = await _journey(
            session,
            name=persona["name"],
            language=persona["language"],
            district=persona["district"],
            state=persona["state"],
            profile=persona["profile"],
            amount=persona["amount"],
            phone=persona["phone"],
            gov_id=persona["gov_id"],
        )

        # The engine decided; here we check it decided what the demo script says it will.
        # A persona that silently stops exercising its scheme family after a rule change
        # would make the pitch wrong on stage rather than red in CI.
        top = payload["results"][0]
        if top["family"] != persona["expect_family"]:
            raise DemoSeedError(
                f"{persona['name']} was expected to match {persona['expect_family']} but "
                f"the engine returned {top['family']}. Update the persona or the rules."
            )
        if "expect_redirect_from" in persona:
            redirected = [
                r for r in payload["results"]
                if r["scheme_code"] == persona["expect_redirect_from"]
                and r.get("redirect_suggestion")
            ]
            if not redirected:
                raise DemoSeedError(
                    f"{persona['name']} no longer triggers the redirect from "
                    f"{persona['expect_redirect_from']} — the anti-misrouting demo is broken."
                )

        await _attach_documents(session, application, persona["documents"], rng)
        await _advance(session, application, persona["advance_to"], rng)
        await _backdate(session, application, rng.randint(3, 12))
        await session.commit()

        redirect_note = ""
        if "expect_redirect_from" in persona:
            redirect_note = "  [redirected off Micro Finance]"
        print(
            f"    {persona['name']:<14} {persona['district']:<16} "
            f"{top['scheme_code']:<24} {application.reference_no}  "
            f"{application.status}{redirect_note}"
        )

    # --- the background population -----------------------------------------------------
    wanted = [status for status, count in STATUS_MIX for _ in range(count)]
    remaining = max(0, TOTAL_APPLICATIONS - len(PERSONAS))
    wanted = (wanted * ((remaining // len(wanted)) + 1))[:remaining]
    rng.shuffle(wanted)

    print(f"\n  background population ({len(wanted)} applications)")
    made = 0
    skipped = 0
    for index, target in enumerate(wanted):
        district, state, language = BACKGROUND_DISTRICTS[index % len(BACKGROUND_DISTRICTS)]
        family_profile, amount = _random_profile(rng)
        name = f"{rng.choice(GIVEN_NAMES)} {rng.choice(FAMILY_NAMES)}"

        try:
            application, _, _ = await _journey(
                session,
                name=name,
                language=language,
                district=district,
                state=state,
                profile=family_profile,
                amount=amount,
                phone=f"98765{rng.randint(10000, 99999)}",
                gov_id=None,
            )
        except DemoSeedError:
            # No authorised partner in that district for that family. Real, and not a
            # reason to abort the seed — it is the same gap the ministry dashboard is
            # built to surface.
            await session.rollback()
            skipped += 1
            continue

        if rng.random() < 0.7:
            await _attach_documents(
                session, application, _documents_for(family_profile, rng), rng
            )
        await _advance(session, application, target, rng)
        await _backdate(session, application, rng.randint(1, 45))
        await session.commit()
        made += 1

    print(f"    {made} created, {skipped} skipped for want of an authorised partner")

    await _summary(session)


def _random_profile(rng: random.Random) -> tuple[dict[str, Any], float]:
    """A plausible applicant. Weighted towards micro finance, as the real caseload is."""
    roll = rng.random()
    if roll < 0.55:
        cost = rng.choice([40000, 60000, 80000, 100000, 125000])
        return (
            {
                "category": "SC",
                "project_sector": rng.choice(["TRADE", "SERVICES"]),
                "annual_family_income": rng.randint(90, 260) * 1000,
                "project_cost": cost,
            },
            cost * 0.9,
        )
    if roll < 0.85:
        cost = rng.choice([400000, 800000, 1200000, 2500000])
        return (
            {
                "category": "SC",
                "project_sector": rng.choice(["MANUFACTURING", "SERVICES", "TRANSPORT"]),
                "annual_family_income": rng.randint(200, 480) * 1000,
                "project_cost": cost,
            },
            cost * 0.9,
        )
    cost = rng.choice([300000, 600000, 900000])
    return (
        {
            "category": "SC",
            "project_sector": "EDUCATION",
            "education_level": "Higher secondary",
            "admission_confirmed": True,
            "annual_family_income": rng.randint(120, 320) * 1000,
            "project_cost": cost,
        },
        cost * 0.9,
    )


def _documents_for(profile: dict[str, Any], rng: random.Random) -> list[str]:
    base = ["CASTE_CERTIFICATE", "INCOME_CERTIFICATE", "IDENTITY_PROOF"]
    if profile.get("project_sector") == "EDUCATION":
        base += ["ADMISSION_LETTER", "FEE_STRUCTURE"]
    else:
        base += ["PROJECT_REPORT"]
    # Partial folders are the norm; a world where everyone uploaded everything makes
    # the readiness score on the partner console meaningless.
    return base[: rng.randint(2, len(base))]


async def _summary(session: AsyncSession) -> None:
    rows = (
        await session.execute(
            text(
                "SELECT status::text, count(*) FROM applications "
                "GROUP BY status ORDER BY count(*) DESC"
            )
        )
    ).all()
    totals = {
        label: (await session.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
        for label, table in (
            ("citizens", "citizens"), ("applications", "applications"),
            ("documents", "documents"), ("notifications", "notifications"),
            ("match runs", "match_runs"), ("audit rows", "audit_log"),
        )
    }

    print("\n  demo world")
    for label, value in totals.items():
        print(f"    {label:<14} {value}")
    print("    by status      " + ", ".join(f"{s}={c}" for s, c in rows))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep", action="store_true", help="Add to existing data instead of resetting."
    )
    args = parser.parse_args()

    print("Building the SETU demo world")
    started = datetime.now(UTC)
    async with SessionLocal() as session:
        try:
            await seed_demo(session, keep=args.keep)
        except DemoSeedError as exc:
            print(f"\n  FAILED: {exc}")
            await engine.dispose()
            raise SystemExit(1) from exc

    elapsed = (datetime.now(UTC) - started) / timedelta(seconds=1)
    print(f"\nDone in {elapsed:.1f}s.")
    print("  Citizen app     http://localhost:3000")
    print("  Staff console   http://localhost:3000/console/login")
    print("  Feature phone   http://localhost:3000/demo/whatsapp")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
