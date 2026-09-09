"use client";

/**
 * Change the language of the whole app, from wherever you are.
 *
 * The control is the globe: tapping it opens a menu of the six languages, each written in
 * its own script, with the current one marked. It used to be a bare `<select>` sitting
 * next to the icon — functional, but it read as a form field in the middle of the page
 * furniture and the icon beside it did nothing.
 *
 * Built on the shadcn DropdownMenu (Radix underneath), so the behaviour a hand-rolled
 * popup gets wrong comes for free: arrow-key navigation, typeahead, Escape and
 * outside-click to close, `aria-expanded` on the trigger, focus returned to the trigger
 * on close, and collision-aware placement so it never opens off the bottom of a short
 * screen. It is a radio group, because picking a language is picking exactly one.
 *
 * It swaps the locale segment **in place**: `/ta/partners` becomes `/hi/partners`, not
 * `/hi`. Sending someone to a separate picker screen to change one setting loses their
 * place — a citizen halfway through the partner list had to find it again afterwards.
 *
 * Every option is written in its own script, because someone who cannot read the current
 * language cannot read "Tamil" either — only "தமிழ்".
 *
 * The list used to mark the four unreviewed languages with a `draft` chip. It was removed
 * on request. The review status itself has not gone anywhere: `REVIEWED_LOCALES` in
 * i18n/config.ts is still the source of truth, `scripts/check-i18n.mjs` still asserts each
 * catalogue declares one, and the results screen still says so where a citizen is reading
 * a verdict rather than choosing a menu item.
 */

import { Languages } from "lucide-react";
import { useTranslations } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LOCALES, LOCALE_NAMES, isLocale, type Locale } from "@/i18n/config";
import { cn } from "@/lib/utils";

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
    <DropdownMenu>
      <DropdownMenuTrigger
        disabled={pending}
        aria-label={t("changeLanguage")}
        className={cn(
          "inline-flex min-h-touch items-center gap-2 rounded-card border-2 px-3 font-medium",
          "transition-colors focus-visible:outline-none focus-visible:ring-4",
          "focus-visible:ring-accent-600/40 focus-visible:ring-offset-2 disabled:opacity-60",
          dark
            ? "border-white/25 text-white hover:bg-white/10 focus-visible:ring-offset-accent-800"
            : "border-line text-ink hover:border-accent-600 focus-visible:ring-offset-canvas",
          className,
        )}
      >
        <Languages className="h-5 w-5 shrink-0" aria-hidden="true" />
        {/* The current language, in its own script. Hidden on the narrowest screens,
            where the globe alone has to carry it — the accessible name is on the
            trigger either way. */}
        <span lang={locale} className="hidden sm:inline">
          {LOCALE_NAMES[locale]}
        </span>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="min-w-[13rem]">
        <DropdownMenuRadioGroup value={locale} onValueChange={switchTo}>
          {LOCALES.map((option) => (
            <DropdownMenuRadioItem
              key={option}
              value={option}
              lang={option}
            >
              {LOCALE_NAMES[option]}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
