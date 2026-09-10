/**
 * The last-four-digits reference.
 *
 * The load-bearing test in this file is `refuses a full Aadhaar rather than trimming it`.
 * A "last four" field that silently keeps the last four of twelve typed digits looks like
 * it worked, and the citizen never learns that their whole number was in the page. The
 * server masks at ingestion three ways (`redaction.py`); this is the same rule applied one
 * step earlier, and it has to fail loudly to be worth anything.
 *
 * No jsdom in this project, so the window is stubbed, following `shortlist.test.ts`.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  GOV_ID_KEY,
  clearGovId,
  maskedDisplay,
  onGovIdChanged,
  parseLast4,
  readGovId,
  writeGovId,
} from "./govId";

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

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("what counts as a last four", () => {
  it("accepts exactly four digits", () => {
    expect(parseLast4("1234")).toEqual({ ok: true, value: "1234", problem: null });
    // Leading zeros are digits like any other and must survive.
    expect(parseLast4("0007").value).toBe("0007");
  });

  it("accepts the spacing people actually type", () => {
    expect(parseLast4(" 12 34 ").value).toBe("1234");
    expect(parseLast4("12-34").value).toBe("1234");
  });

  it("refuses a full Aadhaar rather than trimming it", () => {
    // The failure this whole module exists to prevent. Trimming would look like success
    // while the page had briefly held all twelve digits.
    for (const full of ["123456789012", "1234 5678 9012", "1234-5678-9012"]) {
      const result = parseLast4(full);
      expect(result.ok).toBe(false);
      expect(result.problem).toBe("tooLong");
      expect(result.value).toBeNull();
    }
  });

  it("refuses anything that is not four digits", () => {
    expect(parseLast4("").problem).toBe("empty");
    expect(parseLast4("   ").problem).toBe("empty");
    expect(parseLast4("12").problem).toBe("tooShort");
    expect(parseLast4("12a4").problem).toBe("notDigits");
    expect(parseLast4("abcd").problem).toBe("notDigits");
    expect(parseLast4("12345").problem).toBe("tooLong");
  });
});

describe("how it is shown back", () => {
  it("masks to the shape a bank statement uses", () => {
    expect(maskedDisplay("1234")).toBe("•••• •••• 1234");
    expect(maskedDisplay("1234", "AADHAAR")).toBe("•••• •••• 1234");
    // Other id types are not twelve digits, so they get one group rather than implying a
    // length they do not have.
    expect(maskedDisplay("1234", "PAN")).toBe("•••• 1234");
  });
});

describe("storing the reference", () => {
  it("reads back what was written", () => {
    installWindow();

    expect(writeGovId("AADHAAR", "1234")).toBe(true);
    const record = readGovId();

    expect(record).not.toBeNull();
    expect(record!.last4).toBe("1234");
    expect(record!.idType).toBe("AADHAAR");
  });

  it("is null when nothing was ever saved", () => {
    installWindow();
    expect(readGovId()).toBeNull();
  });

  it("is cleared by clearing", () => {
    installWindow();

    writeGovId("AADHAAR", "1234");
    clearGovId();

    expect(readGovId()).toBeNull();
  });

  it("stores nothing but the four digits and the type", () => {
    const { store } = installWindow();

    writeGovId("AADHAAR", "1234");
    const raw = store.get(GOV_ID_KEY)!;

    // No hash, no full number, no name — the whole record is three fields.
    expect(Object.keys(JSON.parse(raw)).sort()).toEqual(["idType", "last4", "savedAt"]);
  });

  it("refuses a full number even when the form is bypassed", () => {
    const { store } = installWindow();

    // The store validates too, so a caller that skipped `parseLast4` cannot get twelve
    // digits into localStorage.
    expect(writeGovId("AADHAAR", "123456789012")).toBe(false);
    expect(store.get(GOV_ID_KEY)).toBeUndefined();
    expect(readGovId()).toBeNull();
  });
});

describe("what it refuses to read back", () => {
  it("drops a stored value that is not four digits", () => {
    const { store } = installWindow();

    for (const bad of ["123456789012", "12", "abcd", ""]) {
      store.set(GOV_ID_KEY, JSON.stringify({ idType: "AADHAAR", last4: bad, savedAt: 1 }));
      expect(readGovId()).toBeNull();
    }
  });

  it("drops an unknown id type", () => {
    const { store } = installWindow();

    store.set(GOV_ID_KEY, JSON.stringify({ idType: "PASSPORT", last4: "1234", savedAt: 1 }));
    expect(readGovId()).toBeNull();
  });

  it("survives a key holding something that is not a record", () => {
    const { store } = installWindow();

    for (const junk of ["not json", "[]", "null", '"string"', "12"]) {
      store.set(GOV_ID_KEY, junk);
      expect(readGovId()).toBeNull();
    }
  });
});

describe("when the browser will not co-operate", () => {
  it("degrades quietly when site data is blocked", () => {
    installWindow({ throws: true });

    expect(writeGovId("AADHAAR", "1234")).toBe(false);
    expect(() => clearGovId()).not.toThrow();
    expect(readGovId()).toBeNull();
  });

  it("reads as null with no window at all", () => {
    vi.stubGlobal("window", undefined);

    expect(readGovId()).toBeNull();
    expect(writeGovId("AADHAAR", "1234")).toBe(false);
  });
});

describe("other places on the page stay in step", () => {
  it("notifies a subscriber on save and on clear", () => {
    installWindow();
    const seen = vi.fn();

    const stop = onGovIdChanged(seen);
    writeGovId("AADHAAR", "1234");
    expect(seen).toHaveBeenCalledTimes(1);

    clearGovId();
    expect(seen).toHaveBeenCalledTimes(2);

    stop();
    writeGovId("AADHAAR", "5678");
    expect(seen).toHaveBeenCalledTimes(2);
  });

  it("does not notify when the write was refused", () => {
    installWindow();
    const seen = vi.fn();

    onGovIdChanged(seen);
    writeGovId("AADHAAR", "123456789012");

    expect(seen).not.toHaveBeenCalled();
  });
});
