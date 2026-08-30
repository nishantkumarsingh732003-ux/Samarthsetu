/**
 * Last-known-good state, kept on the device.
 *
 * The offline story is not "show an error". A citizen who answered six questions on a
 * 2G connection and then walked into a dead spot must still see what they were told.
 * Results and the session id are written here as they arrive and read back when the
 * network is gone.
 *
 * Nothing identifying is stored: the same masked eligibility profile the API keeps, and
 * never the citizen's raw words.
 */
import type { Explanation, MatchResult } from "./api";

const KEY = "setu.lastResults.v1";

export interface SavedResults {
  savedAt: number;
  language: string;
  profile: Record<string, unknown>;
  results: MatchResult[];
  explanations: Explanation[];
  sessionId: string | null;
  /** From the conversation context, used to pre-fill partner routing. */
  district: string | null;
  /** The engine run behind these results. An application is pinned to it, so a
   *  sanction can be replayed against the rules that were live at the time. */
  matchRunId: string | null;
}

function available(): boolean {
  try {
    return typeof window !== "undefined" && !!window.localStorage;
  } catch {
    // Private mode and blocked site data both throw on access, not on use.
    return false;
  }
}

export function saveResults(value: Omit<SavedResults, "savedAt">): void {
  if (!available()) return;
  try {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({ ...value, savedAt: Date.now() } satisfies SavedResults),
    );
  } catch {
    // A full quota must not break the flow the citizen is in the middle of.
  }
}

export function loadResults(): SavedResults | null {
  if (!available()) return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SavedResults) : null;
  } catch {
    return null;
  }
}

export function clearResults(): void {
  if (!available()) return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* nothing to do */
  }
}
