"""The feature-phone channel: rendering, Meta's envelope, and session identity.

The point of this endpoint is that it adds a *channel*, not a second product. These
tests hold it to that: the rendering is checked here, and the decision logic is not,
because the decision logic is `handle_turn` and it is tested once, elsewhere.
"""

from __future__ import annotations

import pytest

from app.api.v1.routes import webhook

# --- rendering a turn as plain text -------------------------------------------------


def test_a_question_with_choices_is_numbered_for_a_keypad() -> None:
    text, finished = webhook.flatten(
        {
            "stage": "ASKING",
            "question": "Which social category are you from?",
            "question_choices": ["SC", "ST", "OBC", "GENERAL"],
        }
    )
    assert "1) SC" in text
    assert "4) GENERAL" in text
    assert "Reply with the number." in text
    assert finished is False


def test_a_question_without_choices_is_left_alone() -> None:
    text, finished = webhook.flatten(
        {"stage": "ASKING", "question": "How much do you need?", "question_choices": None}
    )
    assert text == "How much do you need?"
    assert finished is False


def test_a_decided_turn_names_the_scheme_verbatim() -> None:
    """Official names are never translated or abbreviated, on any channel (CLAUDE.md)."""
    text, finished = webhook.flatten(
        {
            "stage": "DECIDED",
            "results": [
                {
                    "official_name": "Micro Finance Scheme",
                    "verdict": "ELIGIBLE",
                    "matched_because": [{"rule_id": "MF_CATEGORY_SC", "message": "You are SC."}],
                    "indicative_amount": 72000,
                }
            ],
        }
    )
    assert "Micro Finance Scheme" in text
    assert finished is True


def test_a_decided_turn_always_says_setu_does_not_lend() -> None:
    """The single most misunderstood fact about this scheme, on every channel."""
    text, _ = webhook.flatten(
        {
            "stage": "DECIDED",
            "results": [
                {"official_name": "Micro Finance Scheme", "verdict": "ELIGIBLE",
                 "matched_because": [], "indicative_amount": None}
            ],
        }
    )
    assert "does not lend" in text.lower()


def test_an_ineligible_result_says_why_not() -> None:
    text, _ = webhook.flatten(
        {
            "stage": "DECIDED",
            "results": [
                {
                    "official_name": "Micro Finance Scheme",
                    "verdict": "INELIGIBLE",
                    "matched_because": [],
                    "blocked_because": [
                        {"rule_id": "MF_INCOME_CEILING", "message": "Income is above the limit."}
                    ],
                    "indicative_amount": None,
                }
            ],
        }
    )
    assert "Income is above the limit." in text


def test_an_empty_result_asks_again_rather_than_dead_ending() -> None:
    text, finished = webhook.flatten({"stage": "DECIDED", "results": []})
    assert finished is False
    assert text


def test_a_long_reply_is_truncated_to_something_a_feature_phone_can_show() -> None:
    turn = {
        "stage": "DECIDED",
        "results": [
            {
                "official_name": "Micro Finance Scheme",
                "verdict": "ELIGIBLE",
                "matched_because": [{"rule_id": f"R{i}", "message": "x" * 400} for i in range(2)],
                "indicative_amount": 72000,
            }
        ],
    }
    text, _ = webhook.flatten(turn)
    assert len(text) <= webhook.MAX_REPLY_CHARS


# --- session identity ------------------------------------------------------------------


def test_the_same_sender_resumes_the_same_conversation() -> None:
    assert webhook._session_key("919876500011") == webhook._session_key("919876500011")


def test_different_senders_get_different_conversations() -> None:
    assert webhook._session_key("919876500011") != webhook._session_key("919876500012")


def test_the_phone_number_is_not_recoverable_from_the_session_id() -> None:
    """A WhatsApp sender is a phone number, and it is never written down."""
    key = webhook._session_key("919876500011")
    assert "919876500011" not in key
    assert key.startswith("wa-")


# --- language switching ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("said", "expected"),
    [("Tamil", "ta"), ("தமிழ்", "ta"), ("hindi", "hi"), ("हिन्दी", "hi"), ("Bengali", "bn")],
)
def test_naming_a_language_switches_to_it(said: str, expected: str) -> None:
    assert webhook._detect_language(said, "en") == expected


def test_an_ordinary_message_does_not_change_language() -> None:
    assert webhook._detect_language("mujhe 80 hazaar chahiye", "hi") == "hi"


# --- Meta's envelope -----------------------------------------------------------------------


def test_a_real_meta_text_message_is_parsed() -> None:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "919876500011",
                                    "type": "text",
                                    "text": {"body": "mujhe loan chahiye"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }
    sender, text = webhook._parse_meta_envelope(payload)
    assert sender == "919876500011"
    assert text == "mujhe loan chahiye"


def test_a_delivery_status_callback_is_not_treated_as_a_message() -> None:
    """Meta sends read receipts through the same webhook; they are not conversation."""
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]}
    assert webhook._parse_meta_envelope(payload) == (None, "")


def test_a_non_text_message_is_ignored() -> None:
    """An image or a location is not something the orchestrator can read."""
    payload = {
        "entry": [{"changes": [{"value": {"messages": [{"from": "91", "type": "image"}]}}]}]
    }
    assert webhook._parse_meta_envelope(payload) == (None, "")


def test_a_malformed_envelope_does_not_raise() -> None:
    """This endpoint is public. A bad payload must be a 202, not a 500."""
    for payload in ({}, {"entry": "not-a-list"}, {"entry": [{"changes": None}]}):
        assert webhook._parse_meta_envelope(payload) == (None, "")


# --- numbered replies ------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["1", " 2 ", "9"])
def test_a_bare_digit_is_recognised_as_a_menu_choice(text: str) -> None:
    assert webhook.DIGIT_REPLY.match(text)


@pytest.mark.parametrize("text", ["10", "1.8 lakh", "80000", "0", "1 lakh"])
def test_an_amount_is_not_mistaken_for_a_menu_choice(text: str) -> None:
    """"80000" must reach the extractor as an amount, not select option 8."""
    assert webhook.DIGIT_REPLY.match(text) is None
