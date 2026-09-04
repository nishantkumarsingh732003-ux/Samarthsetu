"use client";

/**
 * Change the language of the whole app, from wherever you are.
 *
 * This replaces a full-page picker at `/` that every "change language" link bounced back
 * to. Sending someone to a separate screen to change one setting loses their place —
 * a citizen halfway through the partner list had to find it again afterwards — so the
 * control lives in the page furniture and swaps the locale segment **in place**:
 * `/ta/partners` becomes `/hi/partners`, not `/hi`.
 *
 * A native `<select>` on purpose. It is one tap on Android, renders as the platform's own
 * wheel, is reachable by switch control and screen reader without any ARIA of ours, and
 * costs nothing. A custom dropdown here would be worse in every one of those ways.
 *
 * Every option is written in its own script, because someone who cannot read the current
 * language cannot read "Tamil" either — only "தமிழ்". Unreviewed languages carry the same
 * `draft` marker the old picker used: these strings tell a citizen why they were refused
 * government credit, and it matters whether a speaker has read them.
 */

import { Languages } from "lucide-react";
import { useTranslations } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { useId, useTransition } from "react";

import { LOCALES, LOCALE_NAMES, isLocale, isReviewed, type Locale } from "@/i18n/config";

export function LanguageSwitcher({
  locale,
  className = "",
  tone = "light",
}: {
  locale: Locale;
  className?: string;
  /** `dark` for the two navy panels, where the light control would disappear. */
  tone?: "light" | "dark";
}) {
  const t = useTranslations("common");
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();
  const id = useId();

  function switchTo(next: string) {
    if (!isLocale(next) || next === locale) return;

    // `usePathname` from next/navigation keeps the locale prefix, so the first segment is
    // replaced rather than prepended. Guarded on the segment actually being a locale so a
    // path that somehow lost its prefix does not get a stray one spliced in.
    const segments = pathname.split("/");
    if (segments[1] && isLocale(segments[1])) segments[1] = next;
    else segments.splice(1, 0, next);

    startTransition(() => router.push(segments.join("/") || `/${next}`));
  }

  const dark = tone === "dark";

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Languages
        className={`h-4 w-4 shrink-0 ${dark ? "text-white/70" : "text-ink-faint"}`}
        aria-hidden="true"
      />
      {/* The visible label is the icon; the accessible name is here. */}
      <label className="sr-only" htmlFor={id}>
        {t("changeLanguage")}
      </label>
      <select
        id={id}
        value={locale}
        disabled={pending}
        onChange={(event) => switchTo(event.target.value)}
        className={`min-h-touch cursor-pointer rounded-card border-2 bg-transparent px-2
                    text-base font-medium disabled:opacity-60 ${
                      dark
                        ? "border-white/25 text-white [&>option]:text-ink"
                        : "border-line text-ink hover:border-accent-600"
                    }`}
      >
        {LOCALES.map((option) => (
          <option key={option} value={option} lang={option}>
            {LOCALE_NAMES[option]}
            {isReviewed(option) ? "" : ` · ${t("draftLanguage")}`}
          </option>
        ))}
      </select>
    </span>
  );
}
