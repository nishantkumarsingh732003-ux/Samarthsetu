/**
 * Text size and contrast, chosen by the citizen and remembered on the device.
 *
 * WHY THIS IS REAL AND NOT THREE DECORATIVE TILES. The design drop draws "−A / A / +A"
 * and a high-contrast switch on the profile page. Drawing them without wiring them is
 * worse than leaving them out: a low-vision citizen presses +A, nothing happens, and the
 * one control on the page that was addressed to them turns out to be a picture of a
 * control. So these write a preference, the preference lands on `<html>` as a data
 * attribute, and globals.css does the rest.
 *
 * WHAT IT DOES NOT REPLACE. Browser zoom and the OS font-size setting still work and are
 * still the better tools — the viewport deliberately allows zoom to 5x (see the root
 * layout). This is for the citizen who does not know those exist, which on a Rs 6,000
 * Android phone handed over at a partner branch is most of them.
 *
 * ON THE DEVICE, not the server. A display preference is not a fact about a person's
 * eligibility, nobody should have to consent to storing it, and it must apply on the
 * anonymous journey too — which has no account to store it against. `localStorage`, the
 * same posture as the shortlist.
 *
 * Every access is wrapped, because `localStorage` throws on *access* in a private window
 * and wherever site data is blocked. A citizen in that state gets the defaults, which is
 * a working app.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const DISPLAY_PREFS_KEY = "setu.display.v1";

/**
 * Three steps, not a slider. `sm` is 0.875x, `lg` is 1.25x — see globals.css, where the
 * multiplier is applied to the root percentage rather than to a pixel value, so it
 * composes with whatever the reader already set as their browser default instead of
 * overriding it.
 */
export const TEXT_SCALES = ["sm", "base", "lg"] as const;
export type TextScale = (typeof TEXT_SCALES)[number];

export type Contrast = "normal" | "high";

export interface DisplayPrefs {
  textScale: TextScale;
  contrast: Contrast;
}

export const DEFAULT_DISPLAY_PREFS: DisplayPrefs = { textScale: "base", contrast: "normal" };

/** Same-tab notification. The `storage` event fires in *other* tabs only. */
const CHANGED = "setu:display-changed";

function coerce(value: unknown): DisplayPrefs {
  const raw = (value ?? {}) as Partial<Record<keyof DisplayPrefs, unknown>>;
  return {
    textScale: TEXT_SCALES.includes(raw.textScale as TextScale)
      ? (raw.textScale as TextScale)
      : DEFAULT_DISPLAY_PREFS.textScale,
    contrast: raw.contrast === "high" ? "high" : DEFAULT_DISPLAY_PREFS.contrast,
  };
}

export function readDisplayPrefs(): DisplayPrefs {
  try {
    if (typeof window === "undefined") return DEFAULT_DISPLAY_PREFS;
    const raw = window.localStorage.getItem(DISPLAY_PREFS_KEY);
    return raw ? coerce(JSON.parse(raw)) : DEFAULT_DISPLAY_PREFS;
  } catch {
    return DEFAULT_DISPLAY_PREFS;
  }
}

/**
 * Put the preference where CSS can see it.
 *
 * The default is written as the *absence* of the attribute rather than as
 * `data-text-scale="base"`, so a citizen who has never touched this gets markup
 * identical to the server's and nothing to explain.
 */
export function applyDisplayPrefs(prefs: DisplayPrefs): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (prefs.textScale === "base") root.removeAttribute("data-text-scale");
  else root.setAttribute("data-text-scale", prefs.textScale);
  if (prefs.contrast === "high") root.setAttribute("data-contrast", "high");
  else root.removeAttribute("data-contrast");
}

/** Merge a change in, apply it, persist it, and tell this tab. Returns the new state. */
export function writeDisplayPrefs(change: Partial<DisplayPrefs>): DisplayPrefs {
  const next = coerce({ ...readDisplayPrefs(), ...change });
  applyDisplayPrefs(next);
  try {
    window.localStorage.setItem(DISPLAY_PREFS_KEY, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data. The attribute is already on `<html>`, so the change the citizen
    // just made is visible for this page view — it simply will not survive a reload.
  }
  return next;
}

/** Subscribe to changes from this tab and from any other. Returns the unsubscriber. */
export function onDisplayPrefsChange(listener: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === DISPLAY_PREFS_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(CHANGED, listener);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(CHANGED, listener);
  };
}

/**
 * The same thing again, as a string, to run before first paint.
 *
 * A `useEffect` cannot do this job. It runs after hydration, which means a citizen who
 * chose large text sees the page render at normal size and then jump — on a slow phone,
 * for most of a second, every single navigation. This is inlined into the document head
 * by the locale layout so the attribute is on `<html>` before the first pixel.
 *
 * Written in ES5 with no template literals or arrow functions: it ships as-is into the
 * HTML without passing through the bundler, so it must parse on the oldest browser this
 * product supports.
 */
export const DISPLAY_PREFS_BOOT = `
try {
  var p = JSON.parse(window.localStorage.getItem(${JSON.stringify(DISPLAY_PREFS_KEY)}) || "{}");
  var e = document.documentElement;
  if (p.textScale === "sm" || p.textScale === "lg") e.setAttribute("data-text-scale", p.textScale);
  if (p.contrast === "high") e.setAttribute("data-contrast", "high");
} catch (err) {}
`;
