/**
 * The reminder store, and the calendar file that makes it a reminder rather than a note.
 *
 * The .ics assertions are the ones that matter. Nothing in this app rings the alarm — the
 * citizen's own calendar does — so a malformed file is a reminder that silently never
 * arrives, which is worse than no reminder at all. The all-day end date being exclusive
 * is the classic way to get that wrong: an event on the 9th written with `DTEND` of the
 * 9th is a zero-length event and some clients drop it.
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  REMINDERS_KEY,
  calendarEvent,
  clearReminder,
  isCalendarDate,
  readReminders,
  setReminder,
} from "./reminders";

/**
 * There is no jsdom in this project — vitest runs on node with no config — so the window
 * is stubbed the same way `shortlist.test.ts` stubs it. That is enough: this module
 * touches exactly `localStorage`, `addEventListener`, `removeEventListener` and
 * `dispatchEvent`.
 */
function installWindow() {
  const store = new Map<string, string>();
  const win = {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
      removeItem: (key: string) => void store.delete(key),
    },
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent: () => true,
  };
  vi.stubGlobal("window", win);
  vi.stubGlobal(
    "CustomEvent",
    class {
      type: string;
      constructor(type: string) {
        this.type = type;
      }
    },
  );
  return store;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("isCalendarDate", () => {
  it("accepts a real day", () => {
    expect(isCalendarDate("2026-09-09")).toBe(true);
    expect(isCalendarDate("2026-02-28")).toBe(true);
  });

  it("rejects a day the calendar does not have", () => {
    expect(isCalendarDate("2026-02-30")).toBe(false);
    expect(isCalendarDate("2026-13-01")).toBe(false);
  });

  it("rejects anything that is not YYYY-MM-DD", () => {
    expect(isCalendarDate("09-09-2026")).toBe(false);
    expect(isCalendarDate("")).toBe(false);
    expect(isCalendarDate(20260909)).toBe(false);
    expect(isCalendarDate(null)).toBe(false);
  });
});

describe("the store", () => {
  it("round-trips a reminder", () => {
    installWindow();
    setReminder("NSFDC_TERM_LOAN", "2026-09-09");
    expect(readReminders()).toEqual({ NSFDC_TERM_LOAN: "2026-09-09" });
  });

  it("clears rather than storing an empty or impossible date", () => {
    installWindow();
    setReminder("NSFDC_TERM_LOAN", "2026-09-09");
    setReminder("NSFDC_TERM_LOAN", "");
    expect(readReminders()).toEqual({});

    setReminder("NSFDC_TERM_LOAN", "2026-09-09");
    setReminder("NSFDC_TERM_LOAN", "2026-02-30");
    expect(readReminders()).toEqual({});
  });

  it("clearReminder removes one without touching the others", () => {
    installWindow();
    setReminder("NSFDC_TERM_LOAN", "2026-09-09");
    setReminder("NSFDC_MICRO_FINANCE", "2026-10-01");
    clearReminder("NSFDC_TERM_LOAN");
    expect(readReminders()).toEqual({ NSFDC_MICRO_FINANCE: "2026-10-01" });
  });

  it("drops entries a tampered or stale key left behind", () => {
    const store = installWindow();
    store.set(
      REMINDERS_KEY,
      JSON.stringify({
        NSFDC_TERM_LOAN: "2026-09-09",
        "not a code": "2026-09-09",
        NSFDC_MICRO_FINANCE: "whenever",
      }),
    );
    expect(readReminders()).toEqual({ NSFDC_TERM_LOAN: "2026-09-09" });
  });

  it("survives a key holding something that is not an object", () => {
    const store = installWindow();
    store.set(REMINDERS_KEY, "[1,2,3]");
    expect(readReminders()).toEqual({});
    store.set(REMINDERS_KEY, "not json");
    expect(readReminders()).toEqual({});
  });
});

describe("calendarEvent", () => {
  const ics = calendarEvent({
    uid: "setu-NSFDC_TERM_LOAN-2026-09-09",
    date: "2026-09-09",
    title: "Apply: Term Loan",
    description: "Saved in SamarthSetu; commas, and semicolons; included",
    url: "https://example.gov.in/en/schemes/NSFDC_TERM_LOAN",
    stamp: new Date("2026-09-06T10:30:00Z"),
  });

  it("is a single all-day VEVENT", () => {
    expect(ics).toContain("BEGIN:VCALENDAR");
    expect(ics).toContain("BEGIN:VEVENT");
    expect(ics).toContain("END:VCALENDAR");
    expect(ics.match(/BEGIN:VEVENT/g)).toHaveLength(1);
    expect(ics).toContain("DTSTART;VALUE=DATE:20260909");
  });

  it("ends the day after it starts, because an all-day DTEND is exclusive", () => {
    expect(ics).toContain("DTEND;VALUE=DATE:20260910");
  });

  it("rolls the end date over a month boundary", () => {
    const endOfMonth = calendarEvent({
      uid: "u",
      date: "2026-09-30",
      title: "t",
      description: "d",
      url: "https://example.gov.in",
    });
    expect(endOfMonth).toContain("DTEND;VALUE=DATE:20261001");
  });

  it("escapes the separators RFC 5545 reserves", () => {
    expect(ics).toContain("Saved in SamarthSetu\\; commas\\, and semicolons\\; included");
  });

  it("separates every line with CRLF, which strict importers require", () => {
    expect(ics.includes("\r\n")).toBe(true);
    expect(ics.split("\r\n").join("")).not.toContain("\n");
  });
});
