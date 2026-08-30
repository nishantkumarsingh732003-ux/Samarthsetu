import { beforeEach, describe, expect, it, vi } from "vitest";

import { clearResults, loadResults, saveResults } from "./storage";

const RESULTS = {
  language: "hi",
  profile: { annual_family_income: 180000 },
  results: [],
  explanations: [],
  sessionId: "abc",
  district: "Nagpur",
  matchRunId: "run-1",
};

function withStorage(store: Storage | undefined): void {
  vi.stubGlobal("window", store ? { localStorage: store } : {});
}

function memoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
    removeItem: (key) => void map.delete(key),
    clear: () => map.clear(),
    key: (index) => [...map.keys()][index] ?? null,
    get length() {
      return map.size;
    },
  } as Storage;
}

describe("saved results", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("round-trips what the results page needs", () => {
    withStorage(memoryStorage());
    saveResults(RESULTS);
    const loaded = loadResults();
    expect(loaded?.district).toBe("Nagpur");
    expect(loaded?.matchRunId).toBe("run-1");
    expect(loaded?.savedAt).toBeGreaterThan(0);
  });

  it("clears", () => {
    withStorage(memoryStorage());
    saveResults(RESULTS);
    clearResults();
    expect(loadResults()).toBeNull();
  });

  it("survives a browser that throws on localStorage access", () => {
    // Private mode and blocked site data both throw on *access*, not on use. A citizen
    // in incognito must still get through the flow, just without the offline copy.
    vi.stubGlobal("window", {
      get localStorage(): Storage {
        throw new Error("blocked");
      },
    });
    expect(() => saveResults(RESULTS)).not.toThrow();
    expect(loadResults()).toBeNull();
    expect(() => clearResults()).not.toThrow();
  });

  it("survives a full quota without breaking the flow the citizen is in", () => {
    const failing = memoryStorage();
    failing.setItem = () => {
      throw new Error("QuotaExceededError");
    };
    withStorage(failing);
    expect(() => saveResults(RESULTS)).not.toThrow();
  });

  it("returns null rather than throwing on corrupted stored JSON", () => {
    const store = memoryStorage();
    store.setItem("setu.lastResults.v1", "{not json");
    withStorage(store);
    expect(loadResults()).toBeNull();
  });
});
