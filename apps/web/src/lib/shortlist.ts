/**
 * The schemes a citizen has set aside to look at again.
 *
 * Deliberately on the device and not on the server. A shortlist is a bookmark, not a
 * declaration: nothing about it belongs in a government record, nobody should have to
 * consent to storing it, and the DPDP surface stays exactly as wide as it was. It is
 * also the only way the feature works for the anonymous journey, which is still the
 * front door — someone comparing three schemes before they decide whether to create an
 * account keeps their comparison.
 *
 * What is stored is a list of scheme *codes*. Never a name, an amount or a verdict:
 * those belong to the published catalogue and to the engine respectively, and a cached
 * copy of either is a copy that goes stale and starts lying. The shortlist page reads
 * the codes and looks everything else up fresh.
 *
 * Every read and write is wrapped, because `localStorage` throws on *access* — not on
 * use — in a private window and wherever site data is blocked. A citizen in that state
 * simply has no shortlist, which is a working app rather than a blank screen.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const SHORTLIST_KEY = "setu.shortlist.v1";

/** How many a shortlist holds. Past this it is a catalogue, not a shortlist, and
 *  /compare takes three at a time anyway. */
export const SHORTLIST_MAX = 12;

/** Same-tab notification. The `storage` event fires in *other* tabs only, so a page with
 *  a bookmark button and a count in the sidebar needs this to keep the two in step. */
const CHANGED = "setu:shortlist-changed";

function isCode(value: unknown): value is string {
  // Scheme codes are engine identifiers — `NSFDC_TERM_LOAN`, not free text. Anything
  // else in the stored array came from a tampered or stale key and is dropped.
  return typeof value === "string" && /^[A-Z0-9_]{2,64}$/.test(value);
}

export function readShortlist(): string[] {
  try {
    if (typeof window === "undefined") return [];
    const raw = window.localStorage.getItem(SHORTLIST_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    // Deduplicated on read as well as on write: a key edited by hand, or written by an
    // older build, must not produce two identical rows on the page.
    return [...new Set(parsed.filter(isCode))].slice(0, SHORTLIST_MAX);
  } catch {
    return [];
  }
}

export function writeShortlist(codes: string[]): string[] {
  const next = [...new Set(codes.filter(isCode))].slice(0, SHORTLIST_MAX);
  try {
    window.localStorage.setItem(SHORTLIST_KEY, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data. The in-memory state still updates for this page view, so the
    // button the citizen just pressed still looks pressed.
  }
  return next;
}

/** Add if absent, remove if present. Returns the list as it now stands. */
export function toggleShortlist(code: string): string[] {
  const current = readShortlist();
  return writeShortlist(
    current.includes(code)
      ? current.filter((entry) => entry !== code)
      : // Newest first: the thing just saved is the thing being thought about.
        [code, ...current],
  );
}

export function removeFromShortlist(code: string): string[] {
  return writeShortlist(readShortlist().filter((entry) => entry !== code));
}

/** Subscribe to changes from this tab and from any other. Returns the unsubscriber. */
export function onShortlistChange(listener: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === SHORTLIST_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(CHANGED, listener);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(CHANGED, listener);
  };
}
