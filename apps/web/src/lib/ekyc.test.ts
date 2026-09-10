/**
 * The e-KYC capture record.
 *
 * The load-bearing tests here are the ones about what the record refuses to be. This key
 * is editable by hand and survives between builds, and what it feeds is a card that says
 * an identity step is complete. A record that does not declare itself simulated must be
 * dropped rather than rendered, or a hand-edited key becomes a claim that someone was
 * verified against their Aadhaar — which nothing in this product can do.
 *
 * No jsdom in this project, so the window is stubbed, following `shortlist.test.ts`.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  EKYC_KEY,
  EKYC_TTL_MS,
  type EkycChecks,
  allChecksPassed,
  clearEkyc,
  newReference,
  onEkycChanged,
  readEkyc,
  writeEkyc,
} from "./ekyc";

type Listener = () => void;

function installWindow(options: { throws?: boolean } = {}) {
  const store = new Map<string, string>();
  const listeners = new Map<string, Set<Listener>>();

  const win = {
    localStorage: {
      getItem(key: string) {
        if (options.throws) throw new Error("site data is blocked");
        return store.get(key) ?? null;
      },
      setItem(key: string, value: string) {
        if (options.throws) throw new Error("site data is blocked");
        store.set(key, value);
      },
      removeItem(key: string) {
        if (options.throws) throw new Error("site data is blocked");
        store.delete(key);
      },
    },
    addEventListener(type: string, listener: Listener) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type)!.add(listener);
    },
    removeEventListener(type: string, listener: Listener) {
      listeners.get(type)?.delete(listener);
    },
    dispatchEvent(event: { type: string }) {
      for (const listener of listeners.get(event.type) ?? []) listener();
      return true;
    },
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
  return { store };
}

const PASSED: EkycChecks = { cameraLive: true, clipRecorded: true, clipHasData: true };

const capture = (overrides: Record<string, unknown> = {}) => ({
  capturedAt: Date.now(),
  reference: "EKYC-ABCD2345",
  seconds: 4,
  checks: PASSED,
  ...overrides,
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("a completed capture is remembered", () => {
  it("reads back what was written, and marks it simulated", () => {
    installWindow();

    writeEkyc(capture());
    const record = readEkyc();

    expect(record).not.toBeNull();
    expect(record!.reference).toBe("EKYC-ABCD2345");
    expect(record!.seconds).toBe(4);
    expect(record!.checks).toEqual(PASSED);
    // Stored, not assumed by the UI.
    expect(record!.simulated).toBe(true);
  });

  it("is null when nothing was ever captured", () => {
    installWindow();

    expect(readEkyc()).toBeNull();
  });

  it("is cleared by clearing, so 'verify again' really starts over", () => {
    installWindow();

    writeEkyc(capture());
    clearEkyc();

    expect(readEkyc()).toBeNull();
  });
});

describe("what it refuses to present as a completed check", () => {
  it("drops a record that does not declare itself simulated", () => {
    const { store } = installWindow();

    // The failure this exists to prevent: a hand-edited or foreign record read back as
    // though someone had been verified against a government photograph.
    store.set(
      EKYC_KEY,
      JSON.stringify({ ...capture(), simulated: false }),
    );
    expect(readEkyc()).toBeNull();

    store.set(EKYC_KEY, JSON.stringify({ ...capture(), simulated: undefined }));
    expect(readEkyc()).toBeNull();
  });

  it("drops a record missing the fields it claims to have", () => {
    const { store } = installWindow();

    for (const bad of [
      { ...capture(), capturedAt: "yesterday" },
      { ...capture(), reference: 42 },
      { ...capture(), seconds: null },
      { ...capture(), checks: null },
    ]) {
      store.set(EKYC_KEY, JSON.stringify({ ...bad, simulated: true }));
      expect(readEkyc()).toBeNull();
    }
  });

  it("survives a key holding something that is not a record", () => {
    const { store } = installWindow();

    for (const junk of ["not json", "[]", '"a string"', "null", "7"]) {
      store.set(EKYC_KEY, junk);
      expect(readEkyc()).toBeNull();
    }
  });

  it("treats a missing check as failed rather than as passed", () => {
    const { store } = installWindow();

    store.set(
      EKYC_KEY,
      JSON.stringify({ ...capture({ checks: { cameraLive: true } }), simulated: true }),
    );

    expect(readEkyc()!.checks).toEqual({
      cameraLive: true,
      clipRecorded: false,
      clipHasData: false,
    });
  });
});

describe("a capture does not stand forever", () => {
  it("discards one past the time-to-live, and removes it", () => {
    const { store } = installWindow();

    store.set(
      EKYC_KEY,
      JSON.stringify({ ...capture({ capturedAt: Date.now() - EKYC_TTL_MS - 1 }), simulated: true }),
    );

    expect(readEkyc()).toBeNull();
    expect(store.get(EKYC_KEY)).toBeUndefined();
  });

  it("keeps one still inside it", () => {
    installWindow();

    writeEkyc(capture({ capturedAt: Date.now() - EKYC_TTL_MS + 60_000 }));

    expect(readEkyc()).not.toBeNull();
  });
});

describe("the reference", () => {
  it("is quotable, prefixed, and free of ambiguous characters", () => {
    installWindow();

    for (let n = 0; n < 50; n += 1) {
      const ref = newReference();
      expect(ref).toMatch(/^EKYC-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{8}$/);
      // A citizen reads this down a phone line; 0/O and 1/I must not appear.
      expect(ref.slice(5)).not.toMatch(/[OI01]/);
    }
  });

  it("does not repeat across captures", () => {
    installWindow();

    const seen = new Set(Array.from({ length: 200 }, () => newReference()));
    expect(seen.size).toBeGreaterThan(190);
  });
});

describe("summarising the device-side checks", () => {
  it("passes only when every check passed", () => {
    expect(allChecksPassed(PASSED)).toBe(true);
    expect(allChecksPassed({ ...PASSED, clipHasData: false })).toBe(false);
    expect(allChecksPassed({ cameraLive: false, clipRecorded: false, clipHasData: false })).toBe(
      false,
    );
  });
});

describe("when the browser will not co-operate", () => {
  it("degrades quietly when site data is blocked", () => {
    installWindow({ throws: true });

    expect(() => writeEkyc(capture())).not.toThrow();
    expect(() => clearEkyc()).not.toThrow();
    expect(readEkyc()).toBeNull();
  });

  it("reads as null when there is no window at all", () => {
    vi.stubGlobal("window", undefined);

    expect(readEkyc()).toBeNull();
    expect(() => writeEkyc(capture())).not.toThrow();
  });
});

describe("other places on the page stay in step", () => {
  it("notifies a subscriber on write and on clear", () => {
    installWindow();
    const seen = vi.fn();

    const stop = onEkycChanged(seen);
    writeEkyc(capture());
    expect(seen).toHaveBeenCalledTimes(1);

    clearEkyc();
    expect(seen).toHaveBeenCalledTimes(2);

    stop();
    writeEkyc(capture());
    expect(seen).toHaveBeenCalledTimes(2);
  });
});
