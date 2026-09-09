/**
 * The tour store, and the two things that must not happen: an index past the end of the
 * step list, and a thrown render in a browser with site data blocked.
 *
 * There is no jsdom in this project — vitest runs on node with no config — so the window
 * is stubbed here. That is enough: this module touches exactly `sessionStorage` and the
 * three event methods.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  JUDGE_TOUR_KEY,
  TOUR_LENGTH,
  TOUR_STEPS,
  onTourChange,
  readTourStep,
  writeTourStep,
} from "./judgeTour";

type Listener = () => void;

function installWindow(options: { throws?: boolean } = {}) {
  const store = new Map<string, string>();
  const listeners = new Map<string, Set<Listener>>();

  vi.stubGlobal("window", {
    sessionStorage: {
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
  });
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

describe("the walkthrough is nine steps of real screens", () => {
  it("has nine of them, matching the counter the card prints", () => {
    expect(TOUR_STEPS).toHaveLength(9);
    expect(TOUR_LENGTH).toBe(9);
  });

  it("gives every step a distinct message-key stem", () => {
    expect(new Set(TOUR_STEPS.map((s) => s.id)).size).toBe(TOUR_STEPS.length);
  });

  it("routes every step to a locale-relative path", () => {
    // A leading slash and no locale segment: `Link` from i18n/navigation adds it, and a
    // hardcoded `/en/...` here would strand a judge reading the tour in Hindi.
    for (const step of TOUR_STEPS) {
      expect(step.href.startsWith("/")).toBe(true);
      expect(step.href).not.toMatch(/^\/(en|hi|mr|bn|ta|te)(\/|$)/);
    }
  });

  it("opens on the landing page, where the problem is stated", () => {
    expect(TOUR_STEPS[0]).toEqual({ id: "problem", href: "/" });
  });
});

describe("the tour store", () => {
  it("is not running until something starts it", () => {
    installWindow();
    expect(readTourStep()).toBeNull();
  });

  it("round-trips a step", () => {
    installWindow();
    expect(writeTourStep(3)).toBe(3);
    expect(readTourStep()).toBe(3);
  });

  it("ends on null, and forgets the step", () => {
    installWindow();
    writeTourStep(3);
    expect(writeTourStep(null)).toBeNull();
    expect(readTourStep()).toBeNull();
  });

  it("refuses a step past the end rather than indexing off the array", () => {
    installWindow();
    expect(writeTourStep(TOUR_LENGTH)).toBeNull();
    expect(writeTourStep(-1)).toBeNull();
    expect(readTourStep()).toBeNull();
  });

  it("ignores a key holding something that is not a step", () => {
    const { store } = installWindow();
    store.set(JUDGE_TOUR_KEY, "banana");
    expect(readTourStep()).toBeNull();
    store.set(JUDGE_TOUR_KEY, "99");
    expect(readTourStep()).toBeNull();
  });

  it("degrades to no tour where site data is blocked, and still does not throw", () => {
    installWindow({ throws: true });
    expect(readTourStep()).toBeNull();
    expect(() => writeTourStep(2)).not.toThrow();
  });

  it("notifies this tab, so the button and the card stay in step", () => {
    installWindow();
    const seen = vi.fn();
    const stop = onTourChange(seen);
    writeTourStep(1);
    expect(seen).toHaveBeenCalledTimes(1);
    stop();
    writeTourStep(2);
    expect(seen).toHaveBeenCalledTimes(1);
  });
});
