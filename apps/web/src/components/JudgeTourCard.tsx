"use client";

/**
 * The walkthrough card: a progress strip, one claim, one thing to look at, and a way on.
 *
 * THE BACKDROP DOES NOT CAPTURE THE POINTER. It dims the page so the card reads as the
 * thing to attend to, and it is `pointer-events-none` so everything behind it still
 * works. That is not a shortcut around a focus trap — it is the whole design. Half these
 * steps end with "open View eligibility on any scheme", and a modal that has to be
 * dismissed before the judge can do the thing it just asked for would make the tour an
 * obstacle to the demo it exists to give.
 *
 * Because it is not modal it is `role="region"`, not `role="dialog"`, and it does not
 * steal focus on every step — a judge tabbing through the page underneath keeps their
 * place. The heading is `aria-live="polite"` instead, so a screen reader hears the new
 * step without the focus ring jumping across the viewport. Escape ends the tour and the
 * arrow keys move through it, which is what anyone tries first.
 */

import { ArrowLeft, ArrowRight, Lightbulb, Sparkles, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { TOUR_LENGTH, TOUR_STEPS, writeTourStep } from "@/lib/judgeTour";
import { cn } from "@/lib/utils";

export function JudgeTourCard({ step }: { step: number }) {
  const t = useTranslations("judgeTour");
  const router = useRouter();
  const current = TOUR_STEPS[step];
  const last = step === TOUR_LENGTH - 1;

  const go = useCallback(
    (next: number | null) => {
      const stored = writeTourStep(next);
      if (stored === null) return;
      // Push rather than replace: a judge who overshoots can use the browser Back button
      // and land where they expect, with the tour still on that page's step.
      router.push(TOUR_STEPS[stored].href);
    },
    [router],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // Never hijack a key someone is using to type — the tour sits over live pages with
      // a search box, a chat composer and four screens of form fields.
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable]")) return;
      if (event.key === "Escape") go(null);
      else if (event.key === "ArrowRight" && !last) go(step + 1);
      else if (event.key === "ArrowLeft" && step > 0) go(step - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, last, step]);

  return (
    <>
      {/* Blurred and dimmed, but only mildly, and the tuning is the interesting part.
          The dialog and the sheet use this same colour at 60% because they are modal and
          the page behind them is genuinely out of play. This one is not: half the steps
          end with "open View eligibility on any scheme", and the judge has to be able to
          find that button through the backdrop. 35% with a 4px blur pushes the page back
          far enough that the card is obviously the thing to read, and not so far that the
          instruction on the card becomes unfollowable. */}
      <div
        aria-hidden="true"
        className="no-print pointer-events-none fixed inset-0 z-40 bg-[#0B1729]/35 backdrop-blur-sm"
      />

      <section
        role="region"
        aria-label={t("label", { current: step + 1, total: TOUR_LENGTH })}
        // `bottom-[3.75rem]` clears the phone's bottom nav, which is `min-h-touch` (3rem)
        // tall and lives at `bottom-0` until `lg` — see AppShell. At `lg` that nav is gone
        // and the card drops to the window edge.
        className="no-print fixed inset-x-3 bottom-[3.75rem] z-50 sm:inset-x-auto
                   sm:left-1/2 sm:w-[36rem] sm:-translate-x-1/2 lg:bottom-6"
      >
        <div className="panel overflow-hidden shadow-lg">
          {/* Progress as a strip across the top of the card rather than a number beside
              the title: at a glance it says "nearly done", which is the thing a judge
              with four submissions left actually wants to know. */}
          <div className="h-1.5 w-full bg-line">
            <div
              className="h-full bg-accent-700 transition-[width] duration-300 ease-out"
              style={{ width: `${((step + 1) / TOUR_LENGTH) * 100}%` }}
            />
          </div>

          <div className="p-5 lg:p-6">
            <div className="flex items-start justify-between gap-3">
              <Badge tone="saffron" className="uppercase tracking-wider">
                <Sparkles className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                {t("label", { current: step + 1, total: TOUR_LENGTH })}
              </Badge>
              <button
                type="button"
                onClick={() => go(null)}
                aria-label={t("close")}
                className="-mr-1.5 -mt-1.5 grid h-9 w-9 shrink-0 place-items-center rounded-full
                           text-ink-faint transition-colors hover:bg-canvas hover:text-ink"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            <div aria-live="polite">
              <h2 className="mt-2.5 font-display text-xl font-bold">
                {t(`${current.id}Title`)}
              </h2>
              <p className="mt-1.5 text-ink-muted">{t(`${current.id}Body`)}</p>

              <p className="mt-4 flex items-start gap-2 rounded-card bg-teal-50 px-4 py-3 text-teal-700">
                <Lightbulb className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                {t(`${current.id}Tip`)}
              </p>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3">
              <Button
                variant="secondary"
                onClick={() => go(step - 1)}
                disabled={step === 0}
                className="shrink-0"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">{t("back")}</span>
              </Button>

              {/* Decorative: the counter in the chip and the strip above both already say
                  where we are, and nine bullets read out one by one is noise. */}
              <ol aria-hidden="true" className="flex shrink items-center gap-1.5">
                {TOUR_STEPS.map((entry, index) => (
                  <li
                    key={entry.id}
                    className={cn(
                      "h-1.5 w-1.5 rounded-full transition-colors",
                      index <= step ? "bg-accent-700" : "bg-line",
                    )}
                  />
                ))}
              </ol>

              <Button
                onClick={() => (last ? go(null) : go(step + 1))}
                className="shrink-0"
              >
                {last ? t("finish") : t("next")}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
