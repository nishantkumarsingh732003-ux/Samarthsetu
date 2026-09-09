"use client";

/**
 * Starts the walkthrough. One component, used by both headers.
 *
 * It used to be a link to `/demo` — the pitch tool, which is a genuinely useful page and
 * is still there, but it is a page *about* the architecture rather than a walk through
 * the product. A judge with three minutes should be looking at the real screens with the
 * real seeded data, which is what this starts.
 *
 * Saffron is a background here and never the text colour: it is a 1.9:1 foreground on
 * white and there is no shade of it that is both saffron and legible. See
 * tailwind.config.ts, and scripts/check-contrast.mjs, which asserts this pair.
 */

import { Play } from "lucide-react";
import { useTranslations } from "next-intl";

import { useRouter } from "@/i18n/navigation";
import { TOUR_STEPS, writeTourStep } from "@/lib/judgeTour";
import { cn } from "@/lib/utils";

export function JudgeTourButton({ className = "" }: { className?: string }) {
  const t = useTranslations("judgeTour");
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={() => {
        writeTourStep(0);
        router.push(TOUR_STEPS[0].href);
      }}
      className={cn(
        `inline-flex min-h-touch items-center gap-2 rounded-full border-2 border-saffron-line
         bg-saffron-bg px-4 text-sm font-bold text-saffron-fg
         transition-[border-color,transform] duration-200 ease-out hover:border-saffron
         focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-600/40
         active:translate-y-px`,
        className,
      )}
    >
      <Play className="h-3.5 w-3.5 shrink-0 fill-current" aria-hidden="true" />
      {t("start")}
    </button>
  );
}
