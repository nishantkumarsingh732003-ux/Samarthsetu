/**
 * The last four digits of a government ID, and nothing else — ever.
 *
 * WHY THIS EXISTS. A Channel Partner matching a file asks "which Aadhaar did you
 * register?", and the citizen should be able to answer without hunting for the card.
 * Four digits are enough to recognise a record; they are not enough to identify a person,
 * which is exactly why CLAUDE.md rule 4 names them as the part that may be kept.
 *
 * WHY IT WILL NOT TAKE THE WHOLE NUMBER. `redaction.py` masks a full ID at ingestion on
 * the server, layered three deep, because a full Aadhaar reaching storage is "not a trade
 * this project gets to make". The cheapest way to honour that is to never let the number
 * into the browser in the first place: `parseLast4` accepts four digits and rejects
 * everything longer, so a citizen who pastes all twelve is stopped in the field with an
 * explanation rather than having eight digits silently trimmed off and the rest sent.
 * Silently trimming would be the worse bug — it looks like it worked.
 *
 * WHAT IS STORED, and where. Four digits and an id type, in `localStorage` on the
 * citizen's own device. Nothing is sent anywhere. The server keeps its own masked record
 * when an application is actually raised (`gov_id_last4` + a salted `gov_id_hash`, set by
 * the application route); this is a convenience so that form arrives pre-filled, not a
 * second copy of a government record.
 *
 * There is deliberately no hash here. A salted hash of four digits is not a
 * privacy measure — the whole space is ten thousand values and falls to a moment's brute
 * force — so storing one would imply a protection it does not provide.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const GOV_ID_KEY = "setu.govIdLast4.v1";

/** The id types the application form accepts, mirroring the API's own enum. */
export const ID_TYPES = ["AADHAAR", "PAN", "VOTER_ID", "OTHER"] as const;
export type IdType = (typeof ID_TYPES)[number];

/** Same-tab notification, so the profile row updates when the dialog saves. */
const CHANGED = "setu:gov-id-changed";

export interface GovIdRef {
  idType: IdType;
  last4: string;
  savedAt: number;
}

/** Why a typed value was refused. `tooLong` is the one that matters. */
export type Last4Problem = "empty" | "notDigits" | "tooLong" | "tooShort";

export interface Last4Result {
  ok: boolean;
  value: string | null;
  problem: Last4Problem | null;
}

/**
 * Validate what the citizen typed as a *last four*.
 *
 * Exactly four digits. Anything longer is refused rather than trimmed — see the header:
 * a paste of a full Aadhaar must fail loudly, because trimming it would look like success
 * while having briefly held the whole number.
 */
export function parseLast4(raw: string): Last4Result {
  const trimmed = raw.trim();
  if (trimmed === "") return { ok: false, value: null, problem: "empty" };

  // Spaces and hyphens are how people group digits on a card; strip them before judging
  // length, so "12 34" is four digits and "1234 5678 9012" is still twelve.
  const compact = trimmed.replace(/[\s-]/g, "");

  if (!/^\d+$/.test(compact)) return { ok: false, value: null, problem: "notDigits" };
  if (compact.length > 4) return { ok: false, value: null, problem: "tooLong" };
  if (compact.length < 4) return { ok: false, value: null, problem: "tooShort" };

  return { ok: true, value: compact, problem: null };
}

/** How the reference is shown back: the masked form a bank statement uses. */
export function maskedDisplay(last4: string, idType: IdType = "AADHAAR"): string {
  // Aadhaar is 12 digits in three groups; the others vary, so they get one group.
  return idType === "AADHAAR" ? `•••• •••• ${last4}` : `•••• ${last4}`;
}

function available(): boolean {
  try {
    return typeof window !== "undefined" && !!window.localStorage;
  } catch {
    return false;
  }
}

export function readGovId(): GovIdRef | null {
  try {
    if (!available()) return null;
    const raw = window.localStorage.getItem(GOV_ID_KEY);
    if (!raw) return null;

    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;
    const record = parsed as Partial<GovIdRef>;

    // Validated on read as well as on write. The key is editable by hand, and a value
    // that is not four digits must not reach a screen that presents it as an id.
    if (typeof record.last4 !== "string" || !/^\d{4}$/.test(record.last4)) return null;
    if (!ID_TYPES.includes(record.idType as IdType)) return null;

    return {
      idType: record.idType as IdType,
      last4: record.last4,
      savedAt: typeof record.savedAt === "number" ? record.savedAt : 0,
    };
  } catch {
    return null;
  }
}

export function writeGovId(idType: IdType, last4: string): boolean {
  const parsed = parseLast4(last4);
  // The store refuses too, not only the form. A caller that skipped validation must not
  // be able to put twelve digits in here.
  if (!parsed.ok || !parsed.value) return false;

  try {
    if (!available()) return false;
    const record: GovIdRef = { idType, last4: parsed.value, savedAt: Date.now() };
    window.localStorage.setItem(GOV_ID_KEY, JSON.stringify(record));
    window.dispatchEvent(new CustomEvent(CHANGED));
    return true;
  } catch {
    return false;
  }
}

export function clearGovId(): void {
  try {
    if (!available()) return;
    window.localStorage.removeItem(GOV_ID_KEY);
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Nothing stored, nothing to clear.
  }
}

/** Subscribe to changes from this tab and from others. Returns an unsubscribe. */
export function onGovIdChanged(listener: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === GOV_ID_KEY) listener();
  };
  window.addEventListener(CHANGED, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(CHANGED, listener);
    window.removeEventListener("storage", onStorage);
  };
}
