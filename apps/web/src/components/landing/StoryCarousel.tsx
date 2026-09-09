"use client";

/**
 * Three journeys, advancing on their own.
 *
 * An auto-rotating carousel is a hostile default: it moves the sentence someone is
 * halfway through reading, and the people this is built for are not fast readers of
 * English. It rotates here because it was asked for, and everything below is what makes
 * that safe rather than merely possible:
 *
 *   - **A pause button.** WCAG 2.2.2 requires a mechanism to pause any motion that starts
 *     by itself and runs longer than five seconds. Hover is not that mechanism — it does
 *     not exist on a touchscreen and it is not reachable from a keyboard.
 *   - **Pause on hover and on focus.** Reading with a pointer resting on the card, or
 *     tabbing into the controls, holds the slide where it is.
 *   - **`prefers-reduced-motion` stops it entirely.** Someone who has asked their device
 *     for less motion gets a static card and the arrows, not a slower carousel.
 *   - **The timer restarts on every change**, including a manual one, so tapping "next"
 *     never leaves you two seconds before it moves again.
 *   - **`aria-live` is off while it rotates.** A live region that changes every seven
 *     seconds interrupts a screen reader continuously; it becomes polite again the moment
 *     the carousel is paused and a person is driving it.
 *
 * The people, districts, schemes and amounts come from `lib/stories.ts`, which is pinned
 * to the demo seed by a test. The sentences each person says are written — hence the
 * "Illustrative · Demo data" badge, in every language, right next to the heading.
 */

import { ChevronLeft, ChevronRight, Pause, Play, Quote } from "lucide-react";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useEffect, useState } from "react";

import { formatRupees } from "@/lib/format";
import { schemeFact } from "@/lib/schemeFacts";
import { STORIES } from "@/lib/stories";

import type { Locale } from "@/i18n/config";

/** Long enough to read a two-line quote and the scheme under it, unhurried. */
const DWELL_MS = 7000;

export function StoryCarousel({ locale }: { locale: Locale }) {
  const t = useTranslations("landing");
  const tCommon = useTranslations("common");

  const [index, setIndex] = useState(0);
  /** The explicit choice, made with the pause button. */
  const [playing, setPlaying] = useState(true);
  /** Transient: a pointer resting on the card, or focus inside it. */
  const [held, setHeld] = useState(false);
  /**
   * Starts `true` so nothing rotates before the media query has been read. The server
   * cannot know the preference, so assuming "reduce" until the client says otherwise
   * means the first frame after hydration is never a surprise movement.
   */
  const [reduceMotion, setReduceMotion] = useState(true);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReduceMotion(query.matches);
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, []);

  const rotating = playing && !held && !reduceMotion;

  useEffect(() => {
    if (!rotating) return;
    // `index` is a dependency on purpose: every change — automatic or from a tap —
    // restarts the clock, so a slide is always shown for its full dwell.
    const timer = window.setInterval(
      () => setIndex((current) => (current + 1) % STORIES.length),
      DWELL_MS,
    );
    return () => window.clearInterval(timer);
  }, [rotating, index]);

  const story = STORIES[index];
  const scheme = schemeFact(story.schemeCode);
  const go = (next: number) => setIndex((next + STORIES.length) % STORIES.length);

  return (
    <div>
      <div
        className="grid gap-5 lg:grid-cols-2 lg:items-stretch"
        onMouseEnter={() => setHeld(true)}
        onMouseLeave={() => setHeld(false)}
        // React synthesises focusin/focusout here, so these fire for anything inside.
        onFocus={() => setHeld(true)}
        onBlur={() => setHeld(false)}
      >
        <div className="relative min-h-[16rem] overflow-hidden rounded-panel bg-accent-800 lg:min-h-[22rem]">
          {/* Keyed on the story so each slide mounts fresh and fades in. The base layer's
              prefers-reduced-motion rule switches the animation off by itself. */}
          <Image
            key={story.photo.url}
            src={story.photo.url}
            alt={t(`story${cap(story.id)}Alt`)}
            fill
            sizes="(min-width: 1024px) 46vw, 100vw"
            className="ss-fade-in object-cover"
            priority={false}
          />
          {/* The scrim is what makes the white name legible over an unknown photograph.
              Without it the contrast of the caption depends on whatever is behind it. */}
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-t from-[#0B1729]/90 via-[#0B1729]/35 to-transparent"
          />
          <div key={story.id} className="ss-fade-up absolute inset-x-0 bottom-0 p-5 text-white sm:p-6">
            <span className="chip bg-white/20 text-white backdrop-blur">
              {story.state} · {story.category}
            </span>
            <p className="mt-2.5 font-display text-xl font-extrabold">{story.name}</p>
            <p className="text-white/80">{t(`story${cap(story.id)}Trade`)}</p>
          </div>
        </div>

        <div className="panel flex flex-col p-5 sm:p-6">
          <Quote className="h-7 w-7 shrink-0 text-saffron" aria-hidden="true" />

          <blockquote
            // Silent while it rotates on its own; polite once a person is driving it.
            aria-live={rotating ? "off" : "polite"}
            className="mt-4 flex-1"
          >
            <div key={story.id} className="ss-fade-up">
              {/* The written sentence is in the reader's language; the line under it is
                  what this person would actually have said, in their own script. Marked
                  with the right `lang` so a screen reader switches voice for it. */}
              <p className="font-display text-lg font-bold leading-snug sm:text-xl">
                “{t(`story${cap(story.id)}Quote`)}”
              </p>
              <p lang={story.language} className="mt-3 italic text-ink-faint">
                — {story.quoteNative}
              </p>
            </div>
          </blockquote>

          <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-line pt-4">
            <div>
              <dt className="text-sm font-medium uppercase tracking-wide text-ink-faint">
                {t("storyScheme")}
              </dt>
              <dd className="mt-1 font-display font-bold" lang="en">
                {scheme?.agency} {scheme?.officialName}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-wide text-ink-faint">
                {t("storyAmount")}
              </dt>
              <dd className="numeric mt-1 font-display font-bold text-teal-700">
                {tCommon("rupees", { amount: formatRupees(story.amount, locale) })}
              </dd>
            </div>
          </dl>

          <div className="mt-5 flex items-center justify-between gap-4">
            <ul className="flex items-center gap-2">
              {STORIES.map((item, i) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => go(i)}
                    aria-current={i === index}
                    className="grid h-touch w-6 place-items-center"
                  >
                    <span className="sr-only">{t("storyGoTo", { n: i + 1 })}</span>
                    <span
                      aria-hidden="true"
                      className={`block h-1.5 rounded-full transition-all ${
                        i === index ? "w-6 bg-accent-700" : "w-2 bg-line"
                      }`}
                    />
                  </button>
                </li>
              ))}
            </ul>

            <div className="flex items-center gap-2">
              {/* Hidden when the device has asked for reduced motion: there is nothing
                  running, so a pause button would be a control over nothing. */}
              {!reduceMotion && (
                <button
                  type="button"
                  onClick={() => setPlaying((on) => !on)}
                  aria-pressed={!playing}
                  className="grid h-touch w-touch place-items-center rounded-full border-2
                             border-line text-ink-muted hover:border-accent-600 hover:text-accent-700"
                >
                  <span className="sr-only">
                    {playing ? t("storyPause") : t("storyPlay")}
                  </span>
                  {playing ? (
                    <Pause className="h-4 w-4 fill-current" aria-hidden="true" />
                  ) : (
                    <Play className="h-4 w-4 fill-current" aria-hidden="true" />
                  )}
                </button>
              )}
              <button
                type="button"
                onClick={() => go(index - 1)}
                className="grid h-touch w-touch place-items-center rounded-full border-2
                           border-line text-ink-muted hover:border-accent-600 hover:text-accent-700"
              >
                <span className="sr-only">{t("storyPrevious")}</span>
                <ChevronLeft className="h-5 w-5" aria-hidden="true" />
              </button>
              <button
                type="button"
                onClick={() => go(index + 1)}
                className="grid h-touch w-touch place-items-center rounded-full border-2
                           border-line text-ink-muted hover:border-accent-600 hover:text-accent-700"
              >
                <span className="sr-only">{t("storyNext")}</span>
                <ChevronRight className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* CC BY-SA 4.0 asks for attribution in a reasonable manner. This is it. */}
      <p className="mt-4 text-sm text-ink-faint">{t("storyCredit")}</p>
    </div>
  );
}

/** `sunita` -> `Sunita`, so the message keys read `storySunitaQuote`. */
function cap(id: string): string {
  return id.charAt(0).toUpperCase() + id.slice(1);
}
