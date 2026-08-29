import Link from "next/link";

import { LOCALES, LOCALE_NAMES, isReviewed } from "@/i18n/config";

/**
 * The language picker.
 *
 * Deliberately outside the locale segment: we do not know the citizen's language yet,
 * so this page is almost entirely native-script names and needs no translation. One
 * decision, six large targets, no wall of text.
 */
export default function LanguagePicker() {
  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas text-ink antialiased">
        <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
          <header className="mb-8">
            <p className="text-sm font-medium uppercase tracking-widest text-ink-faint">
              भारत सरकार · Government of India
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">SETU</h1>
            <p className="mt-1 text-lg text-ink-muted">सेतु</p>
          </header>

          <h2 className="mb-4 text-xl font-medium">
            अपनी भाषा चुनें
            <span className="block text-base font-normal text-ink-muted">
              Choose your language
            </span>
          </h2>

          <nav aria-label="Choose your language">
            <ul className="space-y-3">
              {LOCALES.map((locale) => (
                <li key={locale}>
                  <Link
                    href={`/${locale}`}
                    lang={locale}
                    className="btn-secondary w-full justify-between text-xl"
                  >
                    <span>{LOCALE_NAMES[locale]}</span>
                    {!isReviewed(locale) && (
                      // Honest labelling: this copy has not been read by a speaker of
                      // the language. See packages/rules/translations/README.md.
                      <span className="rounded bg-warn-bg px-2 py-1 text-xs font-medium text-warn-fg">
                        draft
                      </span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <p className="mt-8 text-sm text-ink-faint">
            Marked <span className="font-medium">draft</span> means the wording has not
            yet been checked by a speaker of that language.
          </p>
        </main>
      </body>
    </html>
  );
}
