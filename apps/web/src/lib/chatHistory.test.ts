/**
 * The assistant thread store, against a `localStorage` that behaves like the real ones.
 *
 * The load-bearing tests here are the ones about *bad* stored data. This key survives
 * between builds, is editable by hand, and feeds entries straight into a renderer — so
 * an `action` the client cannot render, or an entry with no text, must be dropped on
 * read rather than reaching the page. The other is expiry: a reply restating a verdict
 * is only true against the rule pack that produced it, so a stale thread is discarded
 * rather than shown as if it were current.
 *
 * There is no jsdom in this project — vitest runs on node with no config — so the window
 * is stubbed, following `shortlist.test.ts`.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CHAT_KEY,
  CHAT_MAX_ENTRIES,
  CHAT_MAX_TEXT,
  CHAT_TTL_MS,
  type ChatEntry,
  clearThread,
  onThreadChanged,
  readThread,
  writeThread,
} from "./chatHistory";

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
  return { store, listeners };
}

const said = (who: "citizen" | "assistant", text: string): ChatEntry => ({
  kind: "said",
  who,
  text,
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("a thread survives the visit", () => {
  it("reads back what was written, in order", () => {
    installWindow();

    const thread: ChatEntry[] = [
      said("assistant", "Namaste."),
      said("citizen", "am I eligible?"),
      { kind: "said", who: "assistant", text: "Yes.", ruleIds: ["TL_INCOME_CEILING"] },
      { kind: "action", action: "open_scheme", schemeCode: "NSFDC_TERM_LOAN" },
    ];

    writeThread(thread);

    expect(readThread()).toEqual(thread);
  });

  it("starts empty when nothing was ever stored", () => {
    installWindow();

    expect(readThread()).toEqual([]);
  });

  it("is emptied by clearing, so 'new chat' actually starts a new one", () => {
    installWindow();

    writeThread([said("citizen", "hello")]);
    clearThread();

    expect(readThread()).toEqual([]);
  });
});

describe("what it refuses to render back", () => {
  it("drops an action the client cannot render", () => {
    const { store } = installWindow();

    // `approve_loan` is not in the set. Restored blindly it would reach the renderer and
    // become a button that goes nowhere — the same guarantee the API enforces server-side.
    store.set(
      CHAT_KEY,
      JSON.stringify({
        savedAt: Date.now(),
        entries: [said("citizen", "hi"), { kind: "action", action: "approve_loan", schemeCode: null }],
      }),
    );

    expect(readThread()).toEqual([said("citizen", "hi")]);
  });

  it("drops entries with no text, an unknown kind, or a bad shape", () => {
    const { store } = installWindow();

    store.set(
      CHAT_KEY,
      JSON.stringify({
        savedAt: Date.now(),
        entries: [
          { kind: "said", who: "citizen", text: "" },
          { kind: "said", who: "nobody", text: "x" },
          { kind: "mystery", text: "x" },
          { kind: "said", who: "citizen", text: "kept" },
          null,
          "not an object",
        ],
      }),
    );

    expect(readThread()).toEqual([said("citizen", "kept")]);
  });

  it("survives a key holding something that is not a thread", () => {
    const { store } = installWindow();

    for (const junk of ["not json at all", "[]", '"a string"', "null", '{"entries":"nope"}']) {
      store.set(CHAT_KEY, junk);
      expect(readThread()).toEqual([]);
    }
  });
});

describe("it does not grow without limit", () => {
  it("keeps the most recent entries and drops the oldest", () => {
    installWindow();

    const many = Array.from({ length: CHAT_MAX_ENTRIES + 20 }, (_, n) =>
      said("citizen", `turn ${n}`),
    );
    writeThread(many);

    const read = readThread();
    expect(read).toHaveLength(CHAT_MAX_ENTRIES);
    // The tail is what a citizen scrolls back to, so the tail is what is kept.
    expect(read.at(-1)).toEqual(said("citizen", `turn ${CHAT_MAX_ENTRIES + 19}`));
  });

  it("clips one very long message rather than dropping it", () => {
    installWindow();

    writeThread([said("citizen", "x".repeat(CHAT_MAX_TEXT + 5000))]);

    const [entry] = readThread();
    expect(entry.kind).toBe("said");
    expect(entry.kind === "said" && entry.text).toHaveLength(CHAT_MAX_TEXT);
  });
});

describe("a thread does not outlive the rules it was answered against", () => {
  it("discards a thread older than the time-to-live", () => {
    const { store } = installWindow();

    store.set(
      CHAT_KEY,
      JSON.stringify({
        savedAt: Date.now() - CHAT_TTL_MS - 1,
        entries: [said("assistant", "You are eligible for the Term Loan.")],
      }),
    );

    expect(readThread()).toEqual([]);
    // And it is removed, not merely hidden, so it cannot come back on a clock change.
    expect(store.get(CHAT_KEY)).toBeUndefined();
  });

  it("keeps a thread that is still inside it", () => {
    const { store } = installWindow();

    store.set(
      CHAT_KEY,
      JSON.stringify({
        savedAt: Date.now() - CHAT_TTL_MS + 60_000,
        entries: [said("assistant", "still current")],
      }),
    );

    expect(readThread()).toEqual([said("assistant", "still current")]);
  });
});

describe("when the browser will not co-operate", () => {
  it("degrades to an in-memory thread when site data is blocked", () => {
    installWindow({ throws: true });

    // A private window throws on access, not on use. None of these may propagate.
    expect(() => writeThread([said("citizen", "hello")])).not.toThrow();
    expect(() => clearThread()).not.toThrow();
    expect(readThread()).toEqual([]);
  });

  it("reads as empty when there is no window at all", () => {
    vi.stubGlobal("window", undefined);

    expect(readThread()).toEqual([]);
    expect(() => writeThread([said("citizen", "hello")])).not.toThrow();
  });
});

describe("other places on the page stay in step", () => {
  it("notifies a subscriber when the thread is written or cleared", () => {
    installWindow();
    const seen = vi.fn();

    const stop = onThreadChanged(seen);
    writeThread([said("citizen", "hello")]);
    expect(seen).toHaveBeenCalledTimes(1);

    clearThread();
    expect(seen).toHaveBeenCalledTimes(2);

    stop();
    writeThread([said("citizen", "again")]);
    expect(seen).toHaveBeenCalledTimes(2);
  });
});
