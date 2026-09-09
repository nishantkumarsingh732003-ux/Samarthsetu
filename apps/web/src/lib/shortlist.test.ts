/**
 * The shortlist store, against a `localStorage` that behaves like the real ones do.
 *
 * Two of these tests exist because of how browsers actually fail rather than how the
 * spec reads: a private window throws on *access* to `localStorage`, and a key can hold
 * whatever an older build or a curious user left in it. Both must degrade to an empty
 * shortlist and a working page, never to a thrown render.
 *
 * There is no jsdom in this project — vitest runs on node with no config — so the window
 * is stubbed here. That is enough: this module touches exactly `localStorage`,
 * `addEventListener`, `removeEventListener` and `dispatchEvent`.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SHORTLIST_KEY,
  SHORTLIST_MAX,
  onShortlistChange,
  readShortlist,
  removeFromShortlist,
  toggleShortlist,
  writeShortlist,
} from "./shortlist";

type Listener = () => void;

/** A `Storage` that works, plus the event plumbing `onShortlistChange` subscribes to. */
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
  // `new CustomEvent(...)` is constructed inside the module, and node 18+ has it — but
  // only reachable as a global, which is exactly how the module reaches it.
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

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the shortlist stores codes and nothing else", () => {
  it("adds, removes and re-adds by toggling the same code", () => {
    installWindow();

    expect(readShortlist()).toEqual([]);
    expect(toggleShortlist("NSFDC_TERM_LOAN")).toEqual(["NSFDC_TERM_LOAN"]);
    expect(readShortlist()).toEqual(["NSFDC_TERM_LOAN"]);
    expect(toggleShortlist("NSFDC_TERM_LOAN")).toEqual([]);
    expect(toggleShortlist("NSFDC_TERM_LOAN")).toEqual(["NSFDC_TERM_LOAN"]);
  });

  it("puts the most recently saved scheme first", () => {
    installWindow();

    toggleShortlist("NSFDC_MICRO_FINANCE");
    toggleShortlist("NSFDC_TERM_LOAN");

    expect(readShortlist()).toEqual(["NSFDC_TERM_LOAN", "NSFDC_MICRO_FINANCE"]);
  });

  it("removes a single code and leaves the rest alone", () => {
    installWindow();

    writeShortlist(["A_ONE", "B_TWO", "C_THREE"]);
    expect(removeFromShortlist("B_TWO")).toEqual(["A_ONE", "C_THREE"]);
  });

  it("never stores the same scheme twice", () => {
    installWindow();

    expect(writeShortlist(["NSFDC_TERM_LOAN", "NSFDC_TERM_LOAN"])).toEqual([
      "NSFDC_TERM_LOAN",
    ]);
  });

  it("caps the list rather than growing without limit", () => {
    installWindow();

    const many = Array.from({ length: SHORTLIST_MAX + 5 }, (_, index) => `SCHEME_${index}`);
    expect(writeShortlist(many)).toHaveLength(SHORTLIST_MAX);
  });
});

describe("a stored value written by something else", () => {
  it("drops anything that is not a scheme code", () => {
    const { store } = installWindow();
    store.set(
      SHORTLIST_KEY,
      JSON.stringify(["NSFDC_TERM_LOAN", { name: "not a code" }, 42, "<script>", null]),
    );

    expect(readShortlist()).toEqual(["NSFDC_TERM_LOAN"]);
  });

  it("returns an empty list rather than throwing on unparseable JSON", () => {
    const { store } = installWindow();
    store.set(SHORTLIST_KEY, "{ this is not json");

    expect(readShortlist()).toEqual([]);
  });

  it("returns an empty list when the key holds an object rather than an array", () => {
    const { store } = installWindow();
    store.set(SHORTLIST_KEY, JSON.stringify({ NSFDC_TERM_LOAN: true }));

    expect(readShortlist()).toEqual([]);
  });
});

describe("a browser with site data blocked", () => {
  it("reads as empty instead of throwing", () => {
    installWindow({ throws: true });

    expect(() => readShortlist()).not.toThrow();
    expect(readShortlist()).toEqual([]);
  });

  it("still reports what the citizen just pressed, so the button is not dead", () => {
    installWindow({ throws: true });

    // The write cannot persist, but it must still hand back the intended list — the
    // bookmark the citizen tapped stays looking tapped for this page view.
    expect(writeShortlist(["NSFDC_TERM_LOAN"])).toEqual(["NSFDC_TERM_LOAN"]);
  });
});

describe("keeping two places on one page in step", () => {
  it("notifies subscribers when the list changes in this tab", () => {
    installWindow();
    const seen = vi.fn();
    const stop = onShortlistChange(seen);

    toggleShortlist("NSFDC_TERM_LOAN");
    expect(seen).toHaveBeenCalledTimes(1);

    stop();
    toggleShortlist("NSFDC_MICRO_FINANCE");
    expect(seen).toHaveBeenCalledTimes(1);
  });
});
