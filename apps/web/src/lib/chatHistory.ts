/**
 * The Samarth AI thread, kept on the device between visits.
 *
 * WHY IT PERSISTS AT ALL. A citizen asks "am I eligible?", closes the app to go and find
 * their income certificate, and comes back. Before this, the thread was rebuilt from the
 * greeting on every mount and that whole exchange was gone — including the rule ids they
 * were about to check. The conversation is the citizen's own record of what they were
 * told, and it should survive the walk to the next room.
 *
 * WHY ON THE DEVICE AND NOT THE SERVER. Same reasoning as `shortlist.ts`: this is the
 * citizen's own reading history, not a government record. Keeping it local means the
 * DPDP surface stays exactly as wide as it was — no new consent to collect, no new table
 * of who asked what, nothing extra to disclose or to breach. The server already keeps an
 * audit row saying an answer was given (CLAUDE.md rule 4); it does not need the thread
 * as well.
 *
 * WHAT IS DEDUCED RATHER THAN STORED. Only what was *said* is written: the citizen's
 * questions, the assistant's replies, and the rule ids each reply leaned on. The
 * document checklist is not — it is live application state, refetched on mount, and a
 * cached copy is a copy that goes stale and starts lying about what has been uploaded.
 * A restored `docs` marker re-renders against whatever the API says today.
 *
 * Every read and write is wrapped, because `localStorage` throws on *access* — not on
 * use — in a private window and wherever site data is blocked. A citizen in that state
 * gets a thread that lasts for one page view, which is the behaviour they had before.
 */

import type { AssistantAction } from "./citizenApi";

/** Versioned, so a shape change invalidates rather than misreads. */
export const CHAT_KEY = "setu.assistantThread.v1";

/**
 * How many entries are kept. Past this the oldest are dropped.
 *
 * The API already caps what it will read back to eight turns, so a longer tail buys the
 * model nothing; this is about what the citizen can scroll to. Forty is generous for
 * that and still small enough that the write stays well inside a 5MB quota.
 */
export const CHAT_MAX_ENTRIES = 40;

/** Longest single message kept. A pasted wall of text is clipped rather than dropped. */
export const CHAT_MAX_TEXT = 4000;

/**
 * How long a thread outlives its visit.
 *
 * Seven days, because a conversation older than that is not context any more — the
 * citizen's profile may have changed, and worse, the *rules* may have: a reply restating
 * a verdict is only true against the rule pack that produced it. Expiring is the honest
 * default. Deliberately not "forever".
 */
export const CHAT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

/** Same-tab notification, so a "new chat" pressed in one place updates another. */
const CHANGED = "setu:assistant-thread-changed";

/** One thing in the thread. Mirrors the client's own `Entry`, minus the live-state parts. */
export type ChatEntry =
  | { kind: "said"; who: "citizen" | "assistant"; text: string; ruleIds?: string[] }
  | { kind: "action"; action: AssistantAction; schemeCode: string | null };

interface StoredThread {
  savedAt: number;
  entries: ChatEntry[];
}

const ACTIONS: readonly AssistantAction[] = [
  "open_scheme",
  "find_partners",
  "start_application",
  "upload_documents",
  "plan_repayment",
];

/**
 * Validate on read, not just on write.
 *
 * The key is editable by hand and may have been written by an older build. An entry that
 * does not match the shape is dropped rather than rendered — a malformed `action` would
 * otherwise reach `ProposedAction` and render a button that goes nowhere.
 */
function isEntry(value: unknown): value is ChatEntry {
  if (typeof value !== "object" || value === null) return false;
  const entry = value as Record<string, unknown>;

  if (entry.kind === "said") {
    return (
      (entry.who === "citizen" || entry.who === "assistant") &&
      typeof entry.text === "string" &&
      entry.text.length > 0 &&
      (entry.ruleIds === undefined ||
        (Array.isArray(entry.ruleIds) && entry.ruleIds.every((id) => typeof id === "string")))
    );
  }

  if (entry.kind === "action") {
    return (
      ACTIONS.includes(entry.action as AssistantAction) &&
      (entry.schemeCode === null || typeof entry.schemeCode === "string")
    );
  }

  return false;
}

/** Trim to the cap, clipping any single message that is too long. */
function normalise(entries: ChatEntry[]): ChatEntry[] {
  return entries.slice(-CHAT_MAX_ENTRIES).map((entry) =>
    entry.kind === "said" && entry.text.length > CHAT_MAX_TEXT
      ? { ...entry, text: entry.text.slice(0, CHAT_MAX_TEXT) }
      : entry,
  );
}

export function readThread(): ChatEntry[] {
  try {
    if (typeof window === "undefined") return [];
    const raw = window.localStorage.getItem(CHAT_KEY);
    if (!raw) return [];

    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return [];

    const stored = parsed as Partial<StoredThread>;
    if (typeof stored.savedAt !== "number" || !Array.isArray(stored.entries)) return [];
    if (Date.now() - stored.savedAt > CHAT_TTL_MS) {
      clearThread();
      return [];
    }

    return normalise(stored.entries.filter(isEntry));
  } catch {
    return [];
  }
}

export function writeThread(entries: ChatEntry[]): void {
  try {
    if (typeof window === "undefined") return;
    const payload: StoredThread = { savedAt: Date.now(), entries: normalise(entries) };
    window.localStorage.setItem(CHAT_KEY, JSON.stringify(payload));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data, or a full quota. The in-memory thread still works for this page
    // view, which is exactly the behaviour before any of this existed.
  }
}

export function clearThread(): void {
  try {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(CHAT_KEY);
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Nothing to do: there is no stored thread to clear.
  }
}

/** Subscribe to changes from this tab and from others. Returns an unsubscribe. */
export function onThreadChanged(listener: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === CHAT_KEY) listener();
  };
  window.addEventListener(CHANGED, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(CHANGED, listener);
    window.removeEventListener("storage", onStorage);
  };
}
