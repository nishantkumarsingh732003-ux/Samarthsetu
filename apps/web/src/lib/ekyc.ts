/**
 * The e-KYC liveness capture, and what is honestly known after it.
 *
 * WHAT THIS IS. A citizen records a four-second selfie clip on their own device. The
 * capture is real: a real camera, a real MediaRecorder, real checks that a frame arrived
 * and that the clip has data. It is the step a Channel Partner would otherwise do at the
 * counter, and doing it first is what saves the trip.
 *
 * WHAT THIS IS NOT, and the distinction is the whole point. It does NOT verify anyone
 * against their Aadhaar record. There is no UIDAI Aadhaar Face Auth integration behind
 * this product, so nothing here can compare a face to a government photograph. The same
 * reasoning `DbtCheckDialog` is built on applies exactly: a citizen told they are
 * "verified against Aadhaar" when no such check ran will present that at a counter and
 * be turned away, and will not understand why.
 *
 * So `matched_against_aadhaar` is not a field this module has. What is stored is what
 * actually happened — a capture was completed on this device, at this time — and every
 * screen that reads it is required to say so. `simulated: true` is written into the
 * record itself rather than left to the UI, so a future reader cannot mistake it for a
 * government verification even if the label is lost.
 *
 * WHAT LEAVES THE DEVICE: nothing. No frame, no clip, no biometric template, no
 * descriptor. The video is recorded into memory and dropped; only the flags below are
 * kept, in `localStorage`. That is the DPDP-minimal record — CLAUDE.md rule 4 permits
 * storing what is needed, and a video of someone's face is not needed to remember that
 * they completed a step.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const EKYC_KEY = "setu.ekyc.v1";

/**
 * How long a capture stands before it is asked for again.
 *
 * Ninety days. A liveness check is evidence about a moment, not a permanent property of
 * a person, and an indefinitely valid one is the kind of stale assurance that gets a
 * file rejected at the counter.
 */
export const EKYC_TTL_MS = 90 * 24 * 60 * 60 * 1000;

/** Same-tab notification, so the profile card updates when the flow finishes. */
const CHANGED = "setu:ekyc-changed";

/** The checks the capture can actually make on the device. */
export interface EkycChecks {
  /** A video track was live and producing frames. */
  cameraLive: boolean;
  /** The recorder produced a clip of usable length. */
  clipRecorded: boolean;
  /** The clip carried data rather than arriving empty. */
  clipHasData: boolean;
}

export interface EkycRecord {
  /** When the capture completed, epoch ms. */
  capturedAt: number;
  /** A reference the citizen can quote. Local to this device; not a government id. */
  reference: string;
  /** Which device-side checks passed. */
  checks: EkycChecks;
  /** Recorded clip length in seconds, as measured. */
  seconds: number;
  /**
   * Always true, and stored rather than assumed.
   *
   * No UIDAI integration exists here. This flag travels with the record so that a screen,
   * an export, or a future reader cannot present the capture as a government
   * verification. If real Aadhaar Face Auth is ever integrated, that path writes its own
   * record and this stays what it is.
   */
  simulated: true;
}

function available(): boolean {
  try {
    return typeof window !== "undefined" && !!window.localStorage;
  } catch {
    // Private mode and blocked site data both throw on access, not on use.
    return false;
  }
}

/** A quotable reference. Random, device-local, and deliberately not derived from any
 *  identifier — deriving it from an Aadhaar or an email would put that identifier in
 *  `localStorage` in reversible form. */
export function newReference(): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no I/O/0/1
  let out = "";
  const bytes = new Uint8Array(8);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  }
  for (const byte of bytes) out += alphabet[byte % alphabet.length];
  return `EKYC-${out}`;
}

/** True when every device-side check passed. */
export function allChecksPassed(checks: EkycChecks): boolean {
  return checks.cameraLive && checks.clipRecorded && checks.clipHasData;
}

export function readEkyc(): EkycRecord | null {
  try {
    if (!available()) return null;
    const raw = window.localStorage.getItem(EKYC_KEY);
    if (!raw) return null;

    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;
    const record = parsed as Partial<EkycRecord>;

    if (
      typeof record.capturedAt !== "number" ||
      typeof record.reference !== "string" ||
      typeof record.seconds !== "number" ||
      typeof record.checks !== "object" ||
      record.checks === null
    ) {
      return null;
    }

    // A record that does not declare itself simulated was not written by this module.
    // Rather than trust it, drop it: the alternative is rendering an unknown record as a
    // completed identity check.
    if (record.simulated !== true) return null;

    if (Date.now() - record.capturedAt > EKYC_TTL_MS) {
      clearEkyc();
      return null;
    }

    const checks = record.checks as Partial<EkycChecks>;
    return {
      capturedAt: record.capturedAt,
      reference: record.reference,
      seconds: record.seconds,
      simulated: true,
      checks: {
        cameraLive: checks.cameraLive === true,
        clipRecorded: checks.clipRecorded === true,
        clipHasData: checks.clipHasData === true,
      },
    };
  } catch {
    return null;
  }
}

export function writeEkyc(record: Omit<EkycRecord, "simulated">): void {
  try {
    if (!available()) return;
    const payload: EkycRecord = { ...record, simulated: true };
    window.localStorage.setItem(EKYC_KEY, JSON.stringify(payload));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data or a full quota. The flow still showed its result for this page
    // view; the citizen is simply asked again next time.
  }
}

export function clearEkyc(): void {
  try {
    if (!available()) return;
    window.localStorage.removeItem(EKYC_KEY);
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Nothing stored, nothing to clear.
  }
}

/** Subscribe to changes from this tab and from others. Returns an unsubscribe. */
export function onEkycChanged(listener: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === EKYC_KEY) listener();
  };
  window.addEventListener(CHANGED, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(CHANGED, listener);
    window.removeEventListener("storage", onStorage);
  };
}
