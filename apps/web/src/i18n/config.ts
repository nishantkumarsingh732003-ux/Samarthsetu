/**
 * Supported locales, in the priority order CLAUDE.md sets.
 *
 * `status` mirrors packages/rules/translations: `verified` means a speaker of that
 * language has read the copy, `draft` means it was machine-written and has not been
 * reviewed. The UI surfaces that difference rather than hiding it — these strings tell
 * a citizen why they were refused government credit.
 */
export const LOCALES = ["en", "hi", "mr", "bn", "ta", "te"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";

/** Rendered in the language picker: always the language's own name, in its own script. */
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी",
  mr: "मराठी",
  bn: "বাংলা",
  ta: "தமிழ்",
  te: "తెలుగు",
};

/** BCP-47 tags for the Web Speech API and `lang` attributes. */
export const SPEECH_TAGS: Record<Locale, string> = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
  bn: "bn-IN",
  ta: "ta-IN",
  te: "te-IN",
};

export const REVIEWED_LOCALES: readonly Locale[] = ["en", "hi"];

export function isReviewed(locale: string): boolean {
  return (REVIEWED_LOCALES as readonly string[]).includes(locale);
}

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}
