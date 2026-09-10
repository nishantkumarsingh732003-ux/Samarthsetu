"""Outbound notifications, behind a driver interface.

Four drivers, one contract. The demo runs entirely on `DatabaseDriver` — messages are
rendered, stored, and read back on the citizen's tracking page — so a full journey can
be shown on a laptop with no network, no Meta account, and no telecom contract. The SMS
and WhatsApp drivers implement the same `Driver` protocol and are wired in; swapping one
in is a config change, not a code change.

**Why the external drivers cannot actually send yet, and why that is deliberate.**
Phase 5 stores `phone_last4` and nothing more, because at that point nothing needed to
call the citizen. An SMS gateway needs a dialable number, so `SmsDriver` and
`WhatsAppDriver` raise `ContactUnavailable` rather than quietly no-op. That is the
honest state: reinstating a full phone number is a schema and consent decision, not
something to slip in behind a notification feature. The exact change it would take is
written down in OPEN_ITEMS OI-43.

The in-app channel is not a consolation prize. It needs no contact address at all, which
means it leaks nothing, works offline, and cannot be intercepted on a shared handset —
and the citizen reads it on the same tracking page they already have the number for.

**SMS segment counting is real, not decorative.** GSM-7 fits 160 characters in a
segment; anything outside that alphabet forces UCS-2, where a segment is 70 characters.
Every Indic script is UCS-2. A message that costs one segment in English costs three in
Tamil, and the sender pays per segment. `sms_segments()` measures it so the cost of
serving people in their own language is visible rather than discovered on an invoice.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Application, ChannelPartner, Citizen, Notification, Scheme
from app.models.enums import NotificationChannel, NotificationStatus
from app.services import audit, redaction

logger = logging.getLogger(__name__)

TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "templates" / "notifications.yaml"
FALLBACK_LANGUAGE = "en"

# GSM 03.38 basic set plus the extension characters that cost two septets. Anything
# outside this forces the whole message to UCS-2.
GSM7_BASIC = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM7_EXTENDED = set("^{}\\[~]|€")

GSM7_SINGLE, GSM7_MULTI = 160, 153
UCS2_SINGLE, UCS2_MULTI = 70, 67


class ContactUnavailable(RuntimeError):
    """The channel needs an address this system deliberately does not retain."""


class NotificationError(RuntimeError):
    """Delivery failed for a reason the operator should see."""


def sms_segments(text: str) -> tuple[int, str]:
    """How many SMS segments this message costs, and in which encoding.

    Returns e.g. `(3, "UCS-2")`. Getting this wrong under-bills by a factor of three on
    every Indic-language message, which is exactly the population this service exists
    to reach.
    """
    if all(char in GSM7_BASIC or char in GSM7_EXTENDED for char in text):
        # Extension characters occupy two septets each.
        septets = sum(2 if char in GSM7_EXTENDED else 1 for char in text)
        if septets <= GSM7_SINGLE:
            return (1 if septets else 0), "GSM-7"
        return -(-septets // GSM7_MULTI), "GSM-7"

    # UCS-2. Characters outside the BMP take two code units; an emoji is two, not one.
    units = sum(2 if ord(char) > 0xFFFF else 1 for char in text)
    if units <= UCS2_SINGLE:
        return (1 if units else 0), "UCS-2"
    return -(-units // UCS2_MULTI), "UCS-2"


# --- templates -------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_templates(path: str | None = None) -> dict[str, Any]:
    target = Path(path) if path else TEMPLATES_PATH
    data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    events = data.get("events") or {}
    if not events:
        raise NotificationError(f"No notification templates in {target}")
    return {"events": events, "meta": data.get("_meta") or {}}


def template_status(language: str) -> str:
    """"verified" | "draft" | "fallback" — carried through so unreviewed copy is labelled."""
    meta = load_templates()["meta"].get("status") or {}
    if language not in meta:
        return "fallback"
    return meta[language]


def render(event: str, language: str, context: dict[str, Any]) -> str:
    """Fill one template. A missing translation falls back to English, never to blank."""
    events = load_templates()["events"]
    block = events.get(event)
    if block is None:
        raise NotificationError(f"No template for event {event!r}")

    text = block.get(language) or block.get(FALLBACK_LANGUAGE)
    if not text:
        raise NotificationError(f"Template {event!r} has no {language} and no English text")

    # A missing placeholder must not produce "{reason}" in a citizen's message, and must
    # not raise either — a notification is never worth failing an application over.
    safe = {key: ("" if value is None else str(value)) for key, value in context.items()}
    try:
        rendered = text.format_map(_Blank(safe))
    except Exception:  # noqa: BLE001 - a broken template must not break the transition
        logger.exception("Template %s failed to render; sending the raw English", event)
        rendered = block.get(FALLBACK_LANGUAGE, "")

    # Collapse the double spaces an empty placeholder leaves behind.
    return " ".join(rendered.split())


class _Blank(dict):
    def __missing__(self, key: str) -> str:
        logger.warning("Notification template referenced missing placeholder %r", key)
        return ""


# --- drivers ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Delivery:
    """What a driver reports back."""

    status: NotificationStatus
    error: str | None = None


class Driver(Protocol):
    """One contract, four implementations. Swapping channel is configuration."""

    channel: NotificationChannel

    def send(self, body: str, recipient: str | None) -> Delivery: ...


class DatabaseDriver:
    """Stores the message for the citizen to read on their tracking page.

    The default, and the one the demo runs on. Needs no address, no network, and no
    third party — the row *is* the delivery.
    """

    channel = NotificationChannel.IN_APP

    def send(self, body: str, recipient: str | None) -> Delivery:  # noqa: ARG002
        return Delivery(NotificationStatus.SENT)


class ConsoleDriver:
    """Prints to the application log. For local development and `scripts/chaos.sh`."""

    channel = NotificationChannel.CONSOLE

    def send(self, body: str, recipient: str | None) -> Delivery:
        segments, encoding = sms_segments(body)
        logger.info(
            "notification.console",
            extra={
                "recipient_hint": recipient,
                "body": body,
                "sms_segments": segments,
                "sms_encoding": encoding,
            },
        )
        return Delivery(NotificationStatus.SENT)


class SmsDriver:
    """SMS gateway adapter.

    Wired and callable; it refuses rather than pretends. Sending needs a dialable
    number, and this system stores four digits by design (Phase 5). Raising here is the
    point: a driver that silently returned SENT would put a green tick beside a message
    nobody received.
    """

    channel = NotificationChannel.SMS

    def send(self, body: str, recipient: str | None) -> Delivery:
        if not recipient or len(recipient) <= 4:
            raise ContactUnavailable(
                "SMS needs a full mobile number. SamarthSetu stores only the last four digits, "
                "so this message cannot be sent until a delivery number is collected "
                "under its own consent purpose (see OPEN_ITEMS OI-43)."
            )
        segments, encoding = sms_segments(body)
        logger.info("sms.send", extra={"segments": segments, "encoding": encoding})
        raise NotificationError("No SMS gateway is configured for this deployment.")


class WhatsAppDriver:
    """WhatsApp Business API adapter.

    Same shape, same refusal, plus WhatsApp's own rule: outside a 24-hour customer
    service window only a pre-approved template may be sent, so "just post the text"
    is not an implementation even with a number in hand.
    """

    channel = NotificationChannel.WHATSAPP

    def send(self, body: str, recipient: str | None) -> Delivery:  # noqa: ARG002
        if not settings.WHATSAPP_TOKEN:
            raise ContactUnavailable(
                "WhatsApp Business API needs a token and a pre-approved message template. "
                "Neither is configured, and SamarthSetu holds no dialable number to send to."
            )
        raise NotificationError("WhatsApp delivery is not implemented in this build.")


DRIVERS: dict[str, Driver] = {
    "database": DatabaseDriver(),
    "console": ConsoleDriver(),
    "sms": SmsDriver(),
    "whatsapp": WhatsAppDriver(),
}


def get_driver(name: str | None = None) -> Driver:
    key = (name or settings.NOTIFICATION_DRIVER or "database").strip().lower()
    driver = DRIVERS.get(key)
    if driver is None:
        logger.error("Unknown notification driver %r; falling back to database", key)
        return DRIVERS["database"]
    return driver


# --- the entry point ---------------------------------------------------------------------


async def notify(
    session: AsyncSession,
    *,
    event: str,
    application: Application,
    reason: str | None = None,
    driver_name: str | None = None,
    actor: str = "system",
) -> Notification | None:
    """Render and record one notification for an application's citizen.

    **Never raises into the caller.** This runs inside application submission and status
    transitions, and a message that cannot be delivered must not roll back a citizen's
    application. Failure is recorded on the row and logged; the transition stands.
    """
    try:
        citizen = (
            await session.execute(select(Citizen).where(Citizen.id == application.citizen_id))
        ).scalar_one_or_none()
        if citizen is None:
            logger.warning("No citizen for application %s; nothing to notify", application.id)
            return None

        scheme = (
            await session.execute(select(Scheme).where(Scheme.id == application.scheme_id))
        ).scalar_one_or_none()
        partner_name = "the Channel Partner"
        if application.partner_id:
            found = (
                await session.execute(
                    select(ChannelPartner.name).where(ChannelPartner.id == application.partner_id)
                )
            ).scalar_one_or_none()
            partner_name = found or partner_name

        language = citizen.preferred_language or FALLBACK_LANGUAGE
        context = {
            "ref": application.reference_no,
            "partner": partner_name,
            # Official names pass through verbatim; they are never translated.
            "scheme": scheme.official_name if scheme else "",
            "reason": (reason or "").strip(),
            # `/applications/<ref>`, not the old `/track/<ref>`. Tracking by reference
            # number with no login went with the anonymous journey; this link now lands on
            # the signed-in application detail screen, which shows the same status and the
            # same document checklist. A link to a route that no longer exists is a 404 in
            # an SMS a citizen cannot retry.
            "link": f"{settings.PUBLIC_WEB_URL}/{language}/applications/{application.reference_no}",
        }
        body = render(event, language, context)

        # A reason typed by a branch officer is free text and reaches a citizen's phone.
        # It must not carry an ID number through this path.
        body = redaction.mask_text(body)
        redaction.assert_no_government_id({"body": body, "context": context}, "notification")

        segments, _ = sms_segments(body)
        driver = get_driver(driver_name)

        notification = Notification(
            citizen_id=citizen.id,
            application_id=application.id,
            event=event,
            channel=driver.channel,
            language=language,
            body=body,
            context=context,
            recipient_hint=citizen.phone_last4,
            status=NotificationStatus.PENDING,
            sms_segments=segments,
            # Set here rather than left to the column default: a Python-side
            # `default=` is only applied at flush, so reading the attribute before
            # then yields None and `attempts += 1` raises. That failure was caught
            # by the guard below — the transition stood — but the message was lost.
            attempts=0,
        )
        session.add(notification)

        try:
            delivery = driver.send(body, citizen.phone_last4)
            notification.status = delivery.status
            notification.error = delivery.error
        except (ContactUnavailable, NotificationError) as exc:
            notification.status = NotificationStatus.FAILED
            notification.error = str(exc)
            logger.warning("notification.failed event=%s: %s", event, exc)
        except Exception as exc:  # noqa: BLE001 - a driver bug must not lose the application
            notification.status = NotificationStatus.FAILED
            notification.error = f"Driver raised unexpectedly: {exc}"
            logger.exception("notification driver %s raised", driver.channel)

        notification.attempts = (notification.attempts or 0) + 1
        if notification.status is NotificationStatus.SENT:
            notification.sent_at = datetime.now(UTC)

        await session.flush()
        await audit.record(
            session,
            actor=actor,
            action="NOTIFICATION_QUEUED",
            entity="notification",
            entity_id=str(notification.id),
            meta={
                "event": event,
                "channel": str(driver.channel),
                "language": language,
                "status": str(notification.status),
                "sms_segments": segments,
                "reference_no": application.reference_no,
            },
        )
        return notification

    except Exception:  # noqa: BLE001 - notification never breaks the thing it reports on
        logger.exception("notify(%s) failed; the application transition still stands", event)
        return None


async def for_application(
    session: AsyncSession, application_id: uuid.UUID
) -> list[Notification]:
    """Every message sent about one application, newest first."""
    return list(
        (
            await session.execute(
                select(Notification)
                .where(Notification.application_id == application_id)
                .order_by(Notification.created_at.desc())
            )
        ).scalars()
    )
