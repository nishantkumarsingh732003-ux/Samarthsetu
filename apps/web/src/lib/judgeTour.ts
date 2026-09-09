/**
 * The judge walkthrough: nine steps across the real screens, in three minutes.
 *
 * WHY IT WALKS THE PRODUCT INSTEAD OF DESCRIBING IT. A hackathon is judged in a few
 * minutes by someone who has already seen twenty submissions, and the thing that decides
 * this one is not a feature list — it is that the verdicts are reproducible and every one
 * of them names the rule that produced it. That is only convincing on the actual screens,
 * with the actual seeded data, so the tour navigates: each step routes to the page it is
 * about and says what to look at there.
 *
 * WHAT THE COPY MAY NOT DO. Every claim in these steps has to survive the judge clicking
 * the thing it describes. So the tour says "a deterministic rule engine decides", because
 * it does; it does not say "AI-driven matching", because the LLM is nowhere near a
 * verdict (CLAUDE.md rule 1). It says the map is the PostGIS registry, because it is; it
 * does not describe a hand-drawn SVG we do not ship. A walkthrough that oversells is the
 * fastest way to lose the room when the judge presses the button.
 *
 * STATE LIVES IN `sessionStorage`, not React. The tour navigates between routes, so it
 * has to survive a page transition — and it must NOT survive the tab, because a judge who
 * closes the window and comes back is not still on step six. `sessionStorage` is exactly
 * that lifetime. Every access is wrapped: it throws on access in a private window, and a
 * blocked-storage browser simply gets no tour rather than a thrown render.
 */

/** Versioned, so a shape change invalidates rather than misreads. */
export const JUDGE_TOUR_KEY = "setu.judgeTour.v1";

/** Same-tab notification. The `storage` event fires in *other* tabs only, and the button
 *  that starts the tour is in the same tree as the card that shows it. */
const CHANGED = "setu:judge-tour-changed";

export interface TourStep {
  /** Message-key stem: `judgeTour.<id>Title` / `Body` / `Tip`. */
  id: string;
  /** Locale-relative route this step is about. The tour navigates here on arrival. */
  href: string;
}

/**
 * Nine steps, in the order a citizen actually meets them: the problem, the intake, the
 * verdict, the explanation, the money, the partner, the assistant, the application.
 */
export const TOUR_STEPS: readonly TourStep[] = [
  { id: "problem", href: "/" },
  { id: "intake", href: "/onboarding" },
  { id: "dashboard", href: "/dashboard" },
  { id: "verdict", href: "/matches" },
  { id: "explain", href: "/matches" },
  { id: "calculator", href: "/calculator" },
  { id: "partners", href: "/partners" },
  { id: "assistant", href: "/assistant" },
  { id: "application", href: "/applications" },
] as const;

export const TOUR_LENGTH = TOUR_STEPS.length;

/** The current step index, or null when the tour is not running. */
export function readTourStep(): number | null {
  try {
    if (typeof window === "undefined") return null;
    const raw = window.sessionStorage.getItem(JUDGE_TOUR_KEY);
    if (raw === null) return null;
    const parsed = Number(raw);
    // A hand-edited or stale key must not index past the end of the array.
    return Number.isInteger(parsed) && parsed >= 0 && parsed < TOUR_LENGTH ? parsed : null;
  } catch {
    return null;
  }
}

/** Move to a step, or pass `null` to end the tour. Returns what is now stored. */
export function writeTourStep(step: number | null): number | null {
  const next =
    step === null || !Number.isInteger(step) || step < 0 || step >= TOUR_LENGTH ? null : step;
  try {
    if (next === null) window.sessionStorage.removeItem(JUDGE_TOUR_KEY);
    else window.sessionStorage.setItem(JUDGE_TOUR_KEY, String(next));
    window.dispatchEvent(new CustomEvent(CHANGED));
  } catch {
    // Blocked site data. Nothing to show, and nothing to crash over.
  }
  return next;
}

/** Subscribe to changes from this tab and from any other. Returns the unsubscriber. */
export function onTourChange(listener: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === JUDGE_TOUR_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(CHANGED, listener);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(CHANGED, listener);
  };
}
