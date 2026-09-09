import { ArrowLeft } from "lucide-react";
import Link from "next/link";

/**
 * The heading block on a signed-in page.
 *
 * `AppShell` owns the chrome — nav, header, language, notifications — so a page inside
 * `(account)` only ever renders its own title. Most of them build that inline; the two
 * that came in from the deleted anonymous journey (`/apply/[scheme]` and the per-scheme
 * partner list) need a back link as well, because they sit at the end of a path rather
 * than on the nav, and this is that shape written once.
 *
 * Matches `MatchesClient`'s heading exactly — `font-display text-2xl font-extrabold`
 * over a muted line — so a page using it is indistinguishable from one that does not.
 */
export function PageHeading({
  title,
  sub,
  back,
  children,
}: {
  title: string;
  sub?: string;
  /** Where "back" goes. Locale-prefixed routing is handled by `@/i18n/navigation`. */
  back?: { href: string; label: string };
  /** An action that belongs beside the title, like the account pages' "Compare". */
  children?: React.ReactNode;
}) {
  return (
    <header className="mb-5">
      {back ? (
        <Link
          href={back.href}
          className="mb-1 inline-flex min-h-touch items-center gap-1.5 font-medium
                     text-accent-700 transition-colors hover:text-accent-800"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {back.label}
        </Link>
      ) : null}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{title}</h1>
          {sub ? <p className="mt-1 text-ink-muted">{sub}</p> : null}
        </div>
        {children}
      </div>
    </header>
  );
}
