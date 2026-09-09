"use client";

/**
 * Three settings that change how the app reads: language, text size, contrast.
 *
 * All three are real. The design drop draws them as tiles on the profile page, and a
 * drawn-but-dead "+A" is worse than no "+A" at all — the citizen it was put there for
 * presses it, nothing moves, and they conclude the app has nothing for them. So text size
 * and contrast write a device preference that lands on `<html>` (lib/displayPrefs.ts) and
 * the whole interface changes, including the pages they navigate to next.
 *
 * Two implementation notes worth keeping:
 *
 *   - The stored preference is read in an effect, never in a `useState` initialiser.
 *     `localStorage` does not exist during the server render, so an initialiser that
 *     read it would produce a different pressed button on the server than on the client
 *     and React would throw a hydration mismatch. Defaults render; the effect corrects.
 *     scripts/check-hydration.mjs exists because this project shipped that bug once.
 *   - The change is *previewed by the control itself*. Pressing +A enlarges this card
 *     along with everything else, which is the confirmation — no toast needed.
 */

import { Contrast, Globe, Type } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Card, CardContent } from "@/components/ui/card";
import { Toggle } from "@/components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { type Locale } from "@/i18n/config";
import {
  DEFAULT_DISPLAY_PREFS,
  onDisplayPrefsChange,
  readDisplayPrefs,
  writeDisplayPrefs,
  type DisplayPrefs,
  type TextScale,
} from "@/lib/displayPrefs";

/** The three steps, smallest first, with the letter drawn at the size it selects. */
const STEPS: { value: TextScale; label: string; className: string }[] = [
  { value: "sm", label: "A−", className: "text-sm" },
  { value: "base", label: "A", className: "text-base" },
  { value: "lg", label: "A+", className: "text-xl" },
];

function Tile({
  icon,
  title,
  hint,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-card border border-line bg-canvas p-4">
      <div className="flex items-center gap-2 text-accent-700">
        {icon}
        <p className="font-display text-base font-bold text-ink">{title}</p>
      </div>
      <p className="mt-1 text-sm text-ink-faint">{hint}</p>
      <div className="mt-3">{children}</div>
    </div>
  );
}

export function DisplayPreferences({ locale }: { locale: Locale }) {
  const t = useTranslations("display");
  const [prefs, setPrefs] = useState<DisplayPrefs>(DEFAULT_DISPLAY_PREFS);

  useEffect(() => {
    setPrefs(readDisplayPrefs());
    return onDisplayPrefsChange(() => setPrefs(readDisplayPrefs()));
  }, []);

  const set = (change: Partial<DisplayPrefs>) => setPrefs(writeDisplayPrefs(change));

  return (
    <Card interactive>
      <CardContent>
        <h2 className="font-display text-lg font-bold">{t("title")}</h2>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Tile
            icon={<Globe className="h-5 w-5" aria-hidden="true" />}
            title={t("language")}
            hint={t("languageHint")}
          >
            {/* No label beside it: the trigger already reads "English" / "हिन्दी" in the
                language it would switch you out of, and a second copy of the same word
                is one more thing to read on a page that is mostly reading. */}
            <LanguageSwitcher locale={locale} />
          </Tile>

          <Tile
            icon={<Type className="h-5 w-5" aria-hidden="true" />}
            title={t("textSize")}
            hint={t("textSizeHint")}
          >
            <ToggleGroup
              type="single"
              value={prefs.textScale}
              // Radix hands back "" when the pressed item is pressed again. A text size
              // has no "off", so that is read as "leave it where it is".
              onValueChange={(next) => next && set({ textScale: next as TextScale })}
              aria-label={t("textSize")}
            >
              {STEPS.map((step) => (
                <ToggleGroupItem
                  key={step.value}
                  value={step.value}
                  aria-label={t(`textSize_${step.value}`)}
                  className="w-touch justify-center px-0"
                >
                  <span className={step.className} aria-hidden="true">
                    {step.label}
                  </span>
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </Tile>

          <Tile
            icon={<Contrast className="h-5 w-5" aria-hidden="true" />}
            title={t("contrast")}
            hint={t("contrastHint")}
          >
            <Toggle
              pressed={prefs.contrast === "high"}
              onPressedChange={(on) => set({ contrast: on ? "high" : "normal" })}
            >
              {prefs.contrast === "high" ? t("contrastOn") : t("contrastOff")}
            </Toggle>
          </Tile>
        </div>
      </CardContent>
    </Card>
  );
}
