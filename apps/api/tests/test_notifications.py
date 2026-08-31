"""Notification rendering, drivers, and the SMS arithmetic that decides what they cost.

The segment counting is the part worth testing hardest. It is invisible, easy to get
subtly wrong, and getting it wrong under-reports the cost of serving Indic-language
citizens by a factor of three — which is exactly the population this project exists to
reach, so the error would land on the people least able to absorb it.
"""

from __future__ import annotations

import pytest

from app.models.enums import NotificationStatus
from app.services import notifications as n

# --- SMS segments ----------------------------------------------------------------------


def test_a_short_latin_message_is_one_gsm7_segment() -> None:
    count, encoding = n.sms_segments("SETU: application SETU-2026-MH-000431 sent.")
    assert (count, encoding) == (1, "GSM-7")


def test_exactly_160_gsm7_characters_still_fits_one_segment() -> None:
    count, encoding = n.sms_segments("a" * 160)
    assert (count, encoding) == (1, "GSM-7")


def test_161_gsm7_characters_costs_two() -> None:
    """Concatenated segments carry a header, so the limit drops to 153 each."""
    count, _ = n.sms_segments("a" * 161)
    assert count == 2


def test_a_gsm7_extension_character_costs_two_septets() -> None:
    """'€' and '{' are in the extension table. 80 of them fill a 160-septet segment."""
    assert n.sms_segments("€" * 80)[0] == 1
    assert n.sms_segments("€" * 81)[0] == 2


@pytest.mark.parametrize(
    ("script", "sample"),
    [
        ("Devanagari", "आवेदन भेजा गया"),
        ("Bengali", "আবেদন পাঠানো হয়েছে"),
        ("Tamil", "விண்ணப்பம் அனுப்பப்பட்டது"),
        ("Telugu", "దరఖాస్తు పంపబడింది"),
    ],
)
def test_every_indic_script_forces_ucs2(script: str, sample: str) -> None:
    """This is the whole reason the templates are written short."""
    assert n.sms_segments(sample)[1] == "UCS-2", script


def test_a_ucs2_segment_is_70_characters_not_160() -> None:
    assert n.sms_segments("आ" * 70) == (1, "UCS-2")
    assert n.sms_segments("आ" * 71)[0] == 2


def test_the_same_message_costs_more_in_tamil_than_in_english() -> None:
    """The cost of answering someone in their own language, made measurable."""
    english = "SETU: your application has been sent to the branch. Keep this number safe."
    tamil = "SETU: உங்கள் விண்ணப்பம் கிளைக்கு அனுப்பப்பட்டது. இந்த எண்ணை பத்திரமாக வைத்திருங்கள்."
    assert n.sms_segments(english)[0] < n.sms_segments(tamil)[0]


def test_an_emoji_counts_as_two_code_units() -> None:
    """Astral-plane characters are surrogate pairs; counting them as one under-bills."""
    assert n.sms_segments("😀" * 35) == (1, "UCS-2")
    assert n.sms_segments("😀" * 36)[0] == 2


def test_an_empty_message_costs_nothing() -> None:
    assert n.sms_segments("") == (0, "GSM-7")


# --- templates ---------------------------------------------------------------------------


def test_every_event_has_all_six_languages() -> None:
    events = n.load_templates()["events"]
    for name, block in events.items():
        for language in ("en", "hi", "mr", "bn", "ta", "te"):
            assert block.get(language), f"{name} has no {language} text"


def test_every_template_fits_two_sms_segments_in_every_language() -> None:
    """A four-segment message is a four-fold bill and a wall of text on a small screen."""
    events = n.load_templates()["events"]
    over: list[str] = []
    for name, block in events.items():
        for language in ("en", "hi", "mr", "bn", "ta", "te"):
            # Placeholders are stripped: the reference number and partner name vary and
            # are not what this test is about.
            body = block[language].replace("{ref}", "").replace("{partner}", "")
            body = body.replace("{link}", "").replace("{reason}", "").replace("{scheme}", "")
            count, _ = n.sms_segments(" ".join(body.split()))
            if count > 2:
                over.append(f"{name}/{language} = {count}")
    assert not over, f"templates too long: {over}"


def test_rendering_fills_the_placeholders() -> None:
    body = n.render(
        "APPLICATION_SUBMITTED",
        "en",
        {"ref": "SETU-2026-MH-000431", "partner": "Test Branch", "link": "http://x/y"},
    )
    assert "SETU-2026-MH-000431" in body
    assert "Test Branch" in body
    assert "{" not in body


def test_a_missing_placeholder_leaves_a_gap_not_a_brace() -> None:
    """A citizen must never receive a message containing the text "{reason}"."""
    body = n.render("DOCS_REQUESTED", "en", {"ref": "X", "link": "y"})
    assert "{reason}" not in body
    assert "{" not in body


def test_an_unknown_language_falls_back_to_english_rather_than_blank() -> None:
    body = n.render("SANCTIONED", "kn", {"ref": "X", "partner": "P"})
    assert "sanctioned" in body.lower()


def test_an_unknown_event_raises_rather_than_sending_nothing() -> None:
    with pytest.raises(n.NotificationError):
        n.render("NO_SUCH_EVENT", "en", {})


def test_the_rejection_template_always_carries_a_reason_and_a_route_onward() -> None:
    """A refusal with no reason and nowhere to go is the failure this project replaces."""
    events = n.load_templates()["events"]
    for language in ("en", "hi", "mr", "bn", "ta", "te"):
        text = events["REJECTED"][language]
        assert "{reason}" in text, language
        assert "{link}" in text, language


def test_the_sanction_template_does_not_promise_money_has_moved() -> None:
    """Sanctioned is not disbursed. Only DISBURSED may say the funds were released."""
    events = n.load_templates()["events"]
    assert "released" not in events["SANCTIONED"]["en"].lower()
    assert "released" in events["DISBURSED"]["en"].lower()


def test_template_review_status_is_declared_per_language() -> None:
    assert n.template_status("en") == "verified"
    assert n.template_status("ta") == "draft"
    assert n.template_status("kn") == "fallback"


# --- drivers -------------------------------------------------------------------------------


def test_the_database_driver_delivers_without_any_contact_address() -> None:
    """The demo's channel, and the only one that needs nothing from the citizen."""
    assert n.DatabaseDriver().send("hello", None).status is NotificationStatus.SENT


def test_the_console_driver_delivers() -> None:
    assert n.ConsoleDriver().send("hello", "3210").status is NotificationStatus.SENT


def test_sms_refuses_rather_than_reporting_a_send_that_never_happened() -> None:
    """A driver returning SENT would put a green tick beside a message nobody received."""
    with pytest.raises(n.ContactUnavailable):
        n.SmsDriver().send("hello", "3210")


def test_whatsapp_refuses_without_a_token() -> None:
    with pytest.raises(n.ContactUnavailable):
        n.WhatsAppDriver().send("hello", "3210")


def test_an_unknown_driver_name_falls_back_rather_than_crashing_a_transition() -> None:
    assert isinstance(n.get_driver("carrier-pigeon"), n.DatabaseDriver)


def test_every_driver_satisfies_the_same_contract() -> None:
    for name, driver in n.DRIVERS.items():
        assert hasattr(driver, "channel"), name
        assert callable(driver.send), name
