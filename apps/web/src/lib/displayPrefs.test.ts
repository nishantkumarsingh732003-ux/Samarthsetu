/**
 * The display-preference store, and the one thing it must never do: throw.
 *
 * This runs on `<html>` before React exists, on every page, for every citizen. A
 * malformed key, a private window or a browser with site data blocked has to degrade to
 * the defaults and a working page — never to a blank screen, and never to a text scale
 * nobody asked for.
 *
 * There is no jsdom in this project — vitest runs on node with no config — so the window
 * and the document are stubbed here. That is enough: this module touches exactly
 * `localStorage`, `documentElement` and the three event methods.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_DISPLAY_PREFS,
  DISPLAY_PREFS_BOOT,
  DISPLAY_PREFS_KEY,
  applyDisplayPrefs,
  onDisplayPrefsChange,
  readDisplayPrefs,
  writeDisplayPrefs,
} from "./displayPrefs";

type Listener = () => void;

function installWindow(options: { throws?: boolean } = {}) {
  const store = new Map<string, string>();
  const listeners = new Map<string, Set<Listener>>();
  const attributes = new Map<string, string>();

  vi.stubGlobal("window", {
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
  });
  vi.stubGlobal("document", {
    documentElement: {
      setAttribute: (name: string, value: string) => void attributes.set(name, value),
      removeAttribute: (name: string) => void attributes.delete(name),
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
  return { store, attributes };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("display preferences survive whatever is in the key", () => {
  it("starts at the defaults with nothing stored", () => {
    installWindow();
    expect(readDisplayPrefs()).toEqual(DEFAULT_DISPLAY_PREFS);
  });

  it("round-trips a choice", () => {
    installWindow();
    expect(writeDisplayPrefs({ textScale: "lg" })).toEqual({
      textScale: "lg",
      contrast: "normal",
    });
    expect(readDisplayPrefs()).toEqual({ textScale: "lg", contrast: "normal" });
  });

  it("merges rather than replaces, so setting one does not clear the other", () => {
    installWindow();
    writeDisplayPrefs({ contrast: "high" });
    expect(writeDisplayPrefs({ textScale: "sm" })).toEqual({
      textScale: "sm",
      contrast: "high",
    });
  });

  it("falls back to the defaults on a key holding nonsense", () => {
    const { store } = installWindow();
    store.set(DISPLAY_PREFS_KEY, '{"textScale":"enormous","contrast":42}');
    expect(readDisplayPrefs()).toEqual(DEFAULT_DISPLAY_PREFS);
  });

  it("falls back to the defaults on a key holding invalid JSON", () => {
    const { store } = installWindow();
    store.set(DISPLAY_PREFS_KEY, "not json at all");
    expect(readDisplayPrefs()).toEqual(DEFAULT_DISPLAY_PREFS);
  });

  it("degrades to the defaults where site data is blocked, and still does not throw", () => {
    installWindow({ throws: true });
    expect(readDisplayPrefs()).toEqual(DEFAULT_DISPLAY_PREFS);
    expect(() => writeDisplayPrefs({ textScale: "lg" })).not.toThrow();
  });
});

describe("the preference reaches the document", () => {
  it("writes the attributes CSS keys on", () => {
    const { attributes } = installWindow();
    applyDisplayPrefs({ textScale: "lg", contrast: "high" });
    expect(attributes.get("data-text-scale")).toBe("lg");
    expect(attributes.get("data-contrast")).toBe("high");
  });

  it("leaves the default off the element rather than writing it out", () => {
    const { attributes } = installWindow();
    applyDisplayPrefs({ textScale: "lg", contrast: "high" });
    applyDisplayPrefs(DEFAULT_DISPLAY_PREFS);
    expect(attributes.has("data-text-scale")).toBe(false);
    expect(attributes.has("data-contrast")).toBe(false);
  });

  it("notifies this tab, so a second control on screen stays in step", () => {
    installWindow();
    const seen = vi.fn();
    const stop = onDisplayPrefsChange(seen);
    writeDisplayPrefs({ contrast: "high" });
    expect(seen).toHaveBeenCalledTimes(1);
    stop();
    writeDisplayPrefs({ contrast: "normal" });
    expect(seen).toHaveBeenCalledTimes(1);
  });
});

describe("the pre-paint script", () => {
  it("reads the same key the store writes", () => {
    expect(DISPLAY_PREFS_BOOT).toContain(JSON.stringify(DISPLAY_PREFS_KEY));
  });

  it("carries nothing the bundler would have had to transpile", () => {
    // It is inlined into the HTML verbatim, so it never sees a build step.
    expect(DISPLAY_PREFS_BOOT).not.toMatch(/=>|`|\bconst\b|\blet\b/);
  });
});
