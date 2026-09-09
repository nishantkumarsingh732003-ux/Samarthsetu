/**
 * The date a citizen wants to be reminded about a scheme they set aside.
 *
 * On the device, for the same reasons as `lib/shortlist.ts`: a reminder is a personal
 * note, not a declaration. Nothing about it belongs in a government record, nobody should
 * have to consent to storing it, and the DPDP surface stays exactly as wide as it was.
 *
 * WHAT ACTUALLY DOES THE REMINDING. Not this app. There is no scheduler behind it and no
 * push channel — `/citizen/notifications` is a record of messages the service already
 * sent, not a queue it can add to. A date field that quietly promised a notification
 * nobody would ever send would be the worst kind of feature on a ministry-branded page,
 * so the date is paired with `calendarEvent` below: it builds an .ics the citizen saves
 * into whatever calendar their phone already has, and *that* is what alerts them. The
 * copy on the page says so.
 *
 * The .ics is generated on the device too. No round trip, works offline, and the file
 * never contains anything the citizen did not already have.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const REMINDERS_KEY = "setu.reminders.v1";

/** Same-tab notification, mirroring `lib/shortlist.ts` — the `storage` event fires in
 *  *other* tabs only. */
const CHANGED = "setu:reminders-changed";

/** code -> ISO date, `YYYY-MM-DD`. */
export type Reminders = Record<string, string>;

function isCode(value: string): boolean {
  // Scheme codes are engine identifiers — `NSFDC_TERM_LOAN`, not free text.
  return /^[A-Z0-9_]{2,64}$/.test(value);
}

/** A calendar date, and one the calendar actually has: `2026-02-30` parses as a string
 *  and is not a day. */
export function isCalendarDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function readReminders(): Reminders {
  try {
    if (typeof window === "undefined") return {};
    const raw = window.localStorage.getItem(REMINDERS_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed as Record<string, unknown>).filter(
        ([code, date]) => isCode(code) && isCalendarDate(date),
      ),
    ) as Reminders;
  } catch {
    return {};
  }
}

function write(next: Reminders): Reminders {
  try {
    window.localStorage.setItem(REMINDERS_KEY, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data. The in-memory state still updates for this page view, so the
    // field the citizen just filled in still shows what they typed.
  }
  return next;
}

/** Set a reminder, or clear it when `date` is empty or not a real day. */
export function setReminder(code: string, date: string): Reminders {
  const current = readReminders();
  if (!isCode(code)) return current;
  if (!isCalendarDate(date)) {
    const { [code]: _cleared, ...rest } = current;
    return write(rest);
  }
  return write({ ...current, [code]: date });
}

export function clearReminder(code: string): Reminders {
  return setReminder(code, "");
}

/** Subscribe to changes from this tab and from any other. Returns the unsubscriber. */
export function onRemindersChange(listener: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === REMINDERS_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(CHANGED, listener);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(CHANGED, listener);
  };
}

/** RFC 5545 escaping: commas, semicolons and backslashes are separators in a value, and
 *  a newline has to be written as its escape rather than sent literally. */
function escapeText(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

/**
 * An all-day VEVENT for one scheme, as an .ics document.
 *
 * All-day rather than timed: the citizen picked a date, not a moment, and inventing
 * "09:00" would put the alarm in a timezone nobody chose. `DTEND` is the day after
 * `DTSTART` because in iCalendar an all-day end date is exclusive.
 *
 * `uid` is passed in rather than generated here so the caller can keep it stable — the
 * same scheme and the same date re-saved should update the calendar entry rather than
 * add a second one.
 */
export function calendarEvent({
  uid,
  date,
  title,
  description,
  url,
  stamp = new Date(),
}: {
  uid: string;
  /** `YYYY-MM-DD`. */
  date: string;
  title: string;
  description: string;
  url: string;
  stamp?: Date;
}): string {
  const compact = date.replace(/-/g, "");
  const next = new Date(`${date}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  const end = next.toISOString().slice(0, 10).replace(/-/g, "");
  const dtstamp = `${stamp.toISOString().slice(0, 19).replace(/[-:]/g, "")}Z`;

  // CRLF between every line: RFC 5545 requires it, and some Android calendar importers
  // reject a file with bare newlines rather than repairing it.
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//SamarthSetu//Scheme reminder//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${escapeText(uid)}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART;VALUE=DATE:${compact}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${escapeText(title)}`,
    `DESCRIPTION:${escapeText(description)}`,
    `URL:${escapeText(url)}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
}
