"""The published scheme catalogue, readable without a login.

Which schemes exist, what they are worth, and where each figure came from is public
information. Putting it behind an account would contradict the whole premise: a citizen
should be able to read the terms before deciding whether to hand over any data at all.

Read from `setu_rules` rather than from the `schemes` table. The YAML is the source of
truth for rules and provenance — including the open questions against figures we could
not source — and the table is a projection of it. Serving the catalogue from the
projection would quietly drop exactly the caveats that make it honest.

Nothing here decides eligibility. `POST /match` does that, from the same rule pack.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.v1.deps import SessionDep
from app.models import ChannelPartner, PartnerSchemeAuthorisation, Scheme
from app.schemas.catalogue import (
    LimitsOut,
    OpenQuestionOut,
    ProvenanceOut,
    SchemeCatalogueOut,
    SchemeDetailOut,
    SchemeRuleOut,
    SchemeSummaryOut,
)

router = APIRouter()

LANGUAGES = ("en", "hi", "mr", "bn", "ta", "te")


def _provenance_out(provenance) -> ProvenanceOut:
    return ProvenanceOut(
        source=provenance.source,
        source_url=provenance.source_url,
        circular_ref=provenance.circular_ref,
        effective_from=provenance.effective_from,
        last_verified_on=provenance.last_verified_on,
        needs_verification=provenance.needs_verification,
        verification_note=provenance.verification_note,
        open_questions=[
            OpenQuestionOut(field=q.field, question=q.question)
            for q in provenance.open_questions
        ],
    )


def _limits_out(limits) -> LimitsOut:
    return LimitsOut(
        min_project_cost=limits.min_project_cost,
        max_project_cost=limits.max_project_cost,
        max_loan_amount=limits.max_loan_amount,
        max_funding_pct=limits.max_funding_pct,
        interest_rate_min=limits.interest_rate_min,
        interest_rate_max=limits.interest_rate_max,
        tenure_months=limits.tenure_months,
        moratorium_months=limits.moratorium_months,
    )


def _summary(scheme, language: str, partner_count: int) -> SchemeSummaryOut:
    from setu_rules import translation_status

    return SchemeSummaryOut(
        code=scheme.code,
        official_name=scheme.official_name,
        # A gloss, not a translation: the official name above stays verbatim, and this
        # is only there so a Tamil reader knows how to say it.
        name_gloss=scheme.name_i18n.get(language) if language != "en" else None,
        family=str(scheme.family),
        limits=_limits_out(scheme.limits),
        provenance=_provenance_out(scheme.provenance),
        rule_count=len(scheme.rules),
        hard_block_count=sum(1 for r in scheme.rules if str(r.severity) == "HARD_BLOCK"),
        authorised_partner_count=partner_count,
        translation_status=translation_status(language),
    )


async def _partner_counts(session) -> dict[str, int]:
    """How many currently-accepting Channel Partners are authorised for each scheme.

    Zero is a meaningful answer and is reported as zero. A scheme nobody is authorised
    to process is precisely the dead end this project is meant to surface.
    """
    rows = await session.execute(
        select(Scheme.code, func.count(PartnerSchemeAuthorisation.id))
        .select_from(Scheme)
        .outerjoin(
            PartnerSchemeAuthorisation,
            (PartnerSchemeAuthorisation.scheme_id == Scheme.id)
            & (PartnerSchemeAuthorisation.is_currently_accepting.is_(True)),
        )
        .outerjoin(
            ChannelPartner,
            (ChannelPartner.id == PartnerSchemeAuthorisation.partner_id)
            & (ChannelPartner.is_active.is_(True)),
        )
        .group_by(Scheme.code)
    )
    return {code: count for code, count in rows}


@router.get(
    "",
    response_model=SchemeCatalogueOut,
    summary="Every scheme in the rule pack, with its provenance",
    description=(
        "Public and unauthenticated. Serves the versioned rule pack directly, so the "
        "engine version and rules digest returned here are the same pair that stamps "
        "every eligibility verdict."
    ),
)
async def catalogue(
    session: SessionDep,
    language: str = Query(default="en", description="Language for rule messages and glosses."),
) -> SchemeCatalogueOut:
    from setu_rules import ENGINE_VERSION, load_schemes, rules_digest

    if language not in LANGUAGES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"language must be one of {', '.join(LANGUAGES)}",
        )

    counts = await _partner_counts(session)
    schemes = load_schemes()

    return SchemeCatalogueOut(
        engine_version=ENGINE_VERSION,
        rules_digest=rules_digest(),
        language=language,
        schemes=[_summary(s, language, counts.get(s.code, 0)) for s in schemes],
    )


@router.get(
    "/{code}",
    response_model=SchemeDetailOut,
    summary="One scheme, with every rule and the documents it needs",
    description=(
        "The rule expressions are published verbatim. A verdict citing a rule id can "
        "therefore be checked against the expression carrying that id by anyone, "
        "without database access."
    ),
)
async def detail(
    code: str,
    session: SessionDep,
    language: str = Query(default="en"),
) -> SchemeDetailOut:
    from setu_rules import load_schemes
    from setu_rules.documents import checklist_digest, required_documents

    if language not in LANGUAGES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"language must be one of {', '.join(LANGUAGES)}",
        )

    scheme = next((s for s in load_schemes() if s.code == code), None)
    if scheme is None:
        # Deliberately does not list the valid codes: the catalogue endpoint is right
        # there, and an error message that enumerates a namespace is a habit worth not
        # forming even where the namespace is public.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such scheme.")

    counts = await _partner_counts(session)
    summary = _summary(scheme, language, counts.get(scheme.code, 0))

    rules = [
        SchemeRuleOut(
            rule_id=rule.id,
            severity=str(rule.severity),
            when_source=rule.when_source,
            message=rule.message_i18n.get(language) or rule.message_i18n.get("en", ""),
            satisfied_message=(
                rule.satisfied_i18n.get(language) or rule.satisfied_i18n.get("en")
            ),
            suggest_instead=rule.suggest_instead,
            fields=sorted(rule.fields),
        )
        for rule in scheme.rules
    ]

    documents = required_documents(
        family=str(scheme.family), partner_type=None, profile={}, language=language
    )

    return SchemeDetailOut(
        **summary.model_dump(),
        rules=rules,
        required_documents=[doc.to_dict() for doc in documents],
        checklist_digest=checklist_digest(),
    )
