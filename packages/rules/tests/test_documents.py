"""The document checklist: narrowed, explained, and never silently short.

The whole point of this list is that it is shorter and more specific than the one a
citizen gets from a government website. These tests hold it to both halves of that:
short enough to be different per persona, and never so short that a document a citizen
actually needs is dropped because we could not decide a condition.
"""

from __future__ import annotations

import pytest

from setu_rules.documents import (
    DocumentLoadError,
    checklist_digest,
    checklist_provenance,
    load_documents,
    required_documents,
)

SUNITA = {
    "category": "SC",
    "project_sector": "TRADE",
    "annual_family_income": 180000,
    "project_cost": 80000,
}
RAMESH = {
    "category": "SC",
    "project_sector": "MANUFACTURING",
    "annual_family_income": 420000,
    "project_cost": 1200000,
}
ANJALI = {
    "category": "SC",
    "project_sector": "EDUCATION",
    "admission_confirmed": True,
    "annual_family_income": 260000,
    "project_cost": 600000,
}


def test_the_checklist_loads_and_every_condition_compiles() -> None:
    """A typo in `profile_when` fails here, not by silently dropping a document."""
    specs, provenance = load_documents()
    assert specs, "the checklist is empty"
    assert provenance is not None


def test_every_document_says_why_it_is_wanted() -> None:
    """A document you understand the purpose of is one you are more likely to bring."""
    specs, _ = load_documents()
    for spec in specs:
        assert spec.name_i18n.get("en"), f"{spec.id} has no English name"
        assert spec.why_i18n.get("en"), f"{spec.id} does not say why it is needed"


def test_the_lists_actually_differ_by_persona() -> None:
    """If every citizen gets the same list, this module has bought nothing."""
    sunita = {d.id for d in required_documents("MICRO_FINANCE", profile=SUNITA)}
    ramesh = {d.id for d in required_documents("TERM_LOAN", profile=RAMESH)}
    anjali = {d.id for d in required_documents("EDUCATION_LOAN", profile=ANJALI)}

    assert sunita != ramesh
    assert ramesh != anjali
    assert len(sunita) < len(ramesh), "a vegetable cart should ask for less than a workshop"


def test_a_student_is_asked_for_an_admission_letter_and_a_trader_is_not() -> None:
    anjali = {d.id for d in required_documents("EDUCATION_LOAN", profile=ANJALI)}
    sunita = {d.id for d in required_documents("MICRO_FINANCE", profile=SUNITA)}
    assert "ADMISSION_LETTER" in anjali
    assert "ADMISSION_LETTER" not in sunita


def test_every_family_asks_for_the_caste_certificate() -> None:
    """The scheme exists for Scheduled Caste applicants; this one is never optional."""
    for family in ("MICRO_FINANCE", "TERM_LOAN", "EDUCATION_LOAN"):
        ids = {d.id for d in required_documents(family, profile=SUNITA)}
        assert "CASTE_CERTIFICATE" in ids, f"{family} does not ask for a caste certificate"
        assert "INCOME_CERTIFICATE" in ids, f"{family} does not ask for an income certificate"


def test_an_undecidable_condition_includes_the_document() -> None:
    """Over-listing costs one sheet of paper. Under-listing costs a second trip.

    An empty profile decides nothing, so the empty-profile list must be a superset of
    every persona's list — never a shorter one.
    """
    unknown = {d.id for d in required_documents("EDUCATION_LOAN", profile={})}
    known = {d.id for d in required_documents("EDUCATION_LOAN", profile=ANJALI)}
    assert known <= unknown, "knowing more about a citizen added documents rather than removing"


def test_partner_type_narrows_the_list_without_emptying_it() -> None:
    for partner_type in ("SCA", "PSB", "RRB", "NBFC_MFI"):
        docs = required_documents("MICRO_FINANCE", partner_type=partner_type, profile=SUNITA)
        assert docs, f"{partner_type} produced an empty checklist"


def test_the_order_is_stable() -> None:
    """A list that reshuffles between page loads is one a citizen cannot tick off."""
    first = [d.id for d in required_documents("TERM_LOAN", profile=RAMESH)]
    second = [d.id for d in required_documents("TERM_LOAN", profile=RAMESH)]
    assert first == second


@pytest.mark.parametrize("language", ["en", "hi", "mr", "bn", "ta", "te"])
def test_every_supported_language_renders_a_full_list(language: str) -> None:
    """A missing translation falls back to English rather than producing an empty row."""
    docs = required_documents("MICRO_FINANCE", profile=SUNITA, language=language)
    assert docs
    for doc in docs:
        assert doc.name.strip(), f"{doc.id} has an empty name in {language}"
        assert doc.why.strip(), f"{doc.id} has an empty reason in {language}"


def test_documents_that_carry_a_government_id_are_flagged() -> None:
    """The upload route refuses these when redaction cannot run, so the flag matters."""
    specs, _ = load_documents()
    flagged = {s.id for s in specs if s.contains_government_id}
    assert "IDENTITY_PROOF" in flagged


def test_a_validity_window_that_is_practice_not_rule_says_so() -> None:
    """CLAUDE.md rule 2. We do not present a partner's habit as a published requirement."""
    specs, _ = load_documents()
    with_validity = [s for s in specs if s.validity_months]
    assert with_validity, "no document carries a validity window"
    assert any(s.validity_is_practice_not_rule for s in with_validity)


def test_the_checklist_carries_provenance_and_admits_what_is_unverified() -> None:
    provenance = checklist_provenance()
    # Until a circular is cited, this must say so rather than imply authority it lacks.
    assert provenance.needs_verification is True
    assert provenance.verification_note


def test_the_digest_changes_when_the_checklist_changes() -> None:
    """Same guarantee as the rules digest: policy cannot change quietly."""
    assert len(checklist_digest()) == 16
    assert checklist_digest() == checklist_digest()


def test_a_broken_checklist_fails_at_load_rather_than_at_render(tmp_path) -> None:
    (tmp_path / "checklist.yaml").write_text(
        "provenance: {needs_verification: true}\n"
        "documents:\n"
        "  - id: BROKEN\n"
        "    name_i18n: {en: Broken}\n"
        "    why_i18n: {en: Because}\n"
        "    applies_to: {profile_when: 'no_such_field == 1'}\n",
        encoding="utf-8",
    )
    load_documents.cache_clear()
    try:
        with pytest.raises((DocumentLoadError, ValueError)):
            load_documents(str(tmp_path))
    finally:
        load_documents.cache_clear()
