
import { fontVariables } from "@/styles/fonts";
/**
 * The staff console shell.
 *
 * Deliberately outside `[locale]`. The citizen surface is localised into six languages,
 * carries a 200KB JS budget and needs no login; this is a desk tool for signed-in staff.
 * Keeping them in separate route trees makes that separation structural rather than a
 * convention someone has to remember — a console dependency cannot end up in a citizen
 * bundle if the citizen routes never import from here.
 *
 * Rule reasons shown in the partner queue *are* localised: they come from the API in
 * the officer's language, rebuilt from stable rule IDs. It is the chrome that is
 * English-only, and that is tracked in OPEN_ITEMS rather than pretended away.
 */
export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={fontVariables}>
      <body className="min-h-screen bg-canvas antialiased">{children}</body>
    </html>
  );
}
