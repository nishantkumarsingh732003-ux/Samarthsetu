"use client";

/**
 * The one box in the top bar, over the two things a citizen actually looks for by name:
 * a scheme and an office.
 *
 * It searches real data, because that is the only version of this control worth having.
 * The design drop drew a "Search schemes, partners…" field and the first pass of this
 * shell left it out rather than ship a box that searched nothing — a search field that
 * returns nothing on a ministry-branded page teaches the citizen that the page is a
 * mock-up. This is that field, wired up:
 *
 *   - **Schemes** are filtered in the browser from the published catalogue, fetched
 *     once on the first focus of the box and not before. It is three rows today and a
 *     few dozen at its worst, so a round trip per keystroke would be slower than the
 *     filter — but a citizen who never uses the search should not pay for it on every
 *     page either, and most of them never will.
 *   - **Partners** go to `/partners/directory?q=`, which already exists and already does
 *     name, district and state matching in Postgres. There are 100+ of them and they are
 *     the half of the problem statement this product exists to solve, so they are not
 *     something to hold in the client.
 *
 * The partner call is debounced by a quarter of a second and every in-flight response is
 * checked against the query that is current when it lands, so a slow reply for "jai"
 * cannot overwrite the results for "jaipur". On a 2G connection that reordering is not
 * an edge case, it is the normal case.
 *
 * The field is the shadcn `Input`, so it inherits the 48px height, the 2px border and
 * the focus ring from the same place every other field in the app does. The listbox
 * around it is hand-rolled rather than a shadcn Popover or Command, and deliberately:
 * both of those move focus into the panel when it opens, which is right for a menu and
 * wrong for a combobox — the caret has to stay in the input while the arrow keys walk
 * the results. This is the WAI-ARIA combobox pattern instead: `aria-activedescendant`
 * tells a screen reader which option is current without the focus ever leaving the box,
 * Enter opens it, Escape closes the list. A citizen on a switch or a keyboard gets the
 * same control as one with a mouse.
 */

import { Loader2, MapPin, ScrollText, Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useId, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { useRouter } from "@/i18n/navigation";
import { getCatalogue, getDirectory } from "@/lib/citizenApi";
import { cn } from "@/lib/utils";

import type { SchemeSummary } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

/** Long enough that one stray keypress does not fire a request, short enough that it
 *  does not feel like the box is ignoring you. */
const DEBOUNCE_MS = 250;
const MAX_PER_GROUP = 4;

interface Hit {
  key: string;
  kind: "scheme" | "partner";
  title: string;
  hint: string;
  href: string;
}

export function GlobalSearch({
  locale,
  className = "",
}: {
  locale: Locale;
  className?: string;
}) {
  const t = useTranslations("search");
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [schemes, setSchemes] = useState<SchemeSummary[]>([]);
  const [partners, setPartners] = useState<Hit[]>([]);
  const [searching, setSearching] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [woken, setWoken] = useState(false);

  const listId = useId();
  const boxRef = useRef<HTMLDivElement>(null);

  const term = query.trim();

  // The catalogue arrives on the first focus, once, and is re-fetched only if the
  // language changes under it — the official names are verbatim in every locale but the
  // glosses this searches are not.
  useEffect(() => {
    if (!woken) return;
    let cancelled = false;
    void getCatalogue(locale).then((result) => {
      if (!cancelled && result.ok) setSchemes(result.data.schemes);
    });
    return () => {
      cancelled = true;
    };
  }, [woken, locale]);

  useEffect(() => {
    if (term.length < 2) {
      setPartners([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    // Declared out here, not inside the timeout: the cleanup below is the only thing
    // that can flip it, and it is what makes a reply for "jai" landing after one for
    // "jaipur" a no-op rather than a flicker back to the older results.
    let stale = false;
    const timer = setTimeout(() => {
      void getDirectory({ q: term }).then((result) => {
        if (stale) return;
        setSearching(false);
        if (!result.ok) {
          // Offline, or the directory is down. The scheme half of this box is local and
          // still works, so the right answer is fewer results, not an error banner in
          // the middle of the top bar.
          setPartners([]);
          return;
        }
        setPartners(
          result.data.partners.slice(0, MAX_PER_GROUP).map((partner) => ({
            key: `partner:${partner.partner_id}`,
            kind: "partner" as const,
            title: partner.name,
            hint: `${partner.type} · ${partner.district}, ${partner.state}`,
            // The partner pages filter from the query string, so a hit lands on that
            // office in context rather than on a detail page that does not exist.
            href: `/partners?state=${encodeURIComponent(partner.state)}&district=${encodeURIComponent(partner.district)}`,
          })),
        );
      });
    }, DEBOUNCE_MS);
    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [term]);

  const needle = term.toLowerCase();
  const schemeHits: Hit[] =
    needle.length < 2
      ? []
      : schemes
          .filter(
            (scheme) =>
              scheme.official_name.toLowerCase().includes(needle) ||
              (scheme.name_gloss ?? "").toLowerCase().includes(needle) ||
              scheme.family.toLowerCase().includes(needle.replace(/\s+/g, "_")) ||
              scheme.code.toLowerCase().includes(needle),
          )
          .slice(0, MAX_PER_GROUP)
          .map((scheme) => ({
            key: `scheme:${scheme.code}`,
            kind: "scheme" as const,
            // Official names are never machine-translated (CLAUDE.md), so this is the
            // name as published, in every locale.
            title: scheme.official_name,
            hint: t("partnersAuthorised", { count: scheme.authorised_partner_count }),
            href: `/schemes/${scheme.code}`,
          }));

  const hits = [...schemeHits, ...partners];
  const expanded = open && needle.length >= 2;

  // Keep the highlighted row inside the list as it shrinks under a longer query.
  useEffect(() => setActive(0), [term]);

  useEffect(() => {
    if (!expanded) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [expanded]);

  function go(hit: Hit) {
    setOpen(false);
    setQuery("");
    router.push(hit.href);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!expanded || hits.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => (index + 1) % hits.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => (index - 1 + hits.length) % hits.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      go(hits[active]);
    }
  }

  return (
    <div ref={boxRef} className={cn("relative", className)}>
      <Search
        className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint"
        aria-hidden="true"
      />
      <Input
        type="search"
        role="combobox"
        aria-expanded={expanded}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          expanded && hits.length > 0 ? `${listId}-${active}` : undefined
        }
        aria-label={t("label")}
        placeholder={t("placeholder")}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          setOpen(true);
          setWoken(true);
        }}
        onKeyDown={onKeyDown}
        // A pill on the page ground, so it reads as a field rather than as a panel, and
        // room on both sides for the magnifier and the spinner.
        className="rounded-full bg-canvas pl-11 pr-10 transition-colors duration-200
                   ease-out focus:bg-surface"
      />
      {searching && (
        <Loader2
          className="pointer-events-none absolute right-3.5 top-1/2 h-5 w-5 -translate-y-1/2
                     animate-spin text-ink-faint"
          aria-hidden="true"
        />
      )}

      {expanded && (
        <div
          className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-40 overflow-hidden
                     rounded-panel border border-line bg-surface shadow-lift
                     animate-in fade-in-0 zoom-in-95 duration-150"
        >
          <ul id={listId} role="listbox" aria-label={t("results")} className="max-h-96 overflow-y-auto py-1">
            {hits.map((hit, index) => {
              const Icon = hit.kind === "scheme" ? ScrollText : MapPin;
              return (
                <li key={hit.key}>
                  <button
                    type="button"
                    id={`${listId}-${index}`}
                    role="option"
                    aria-selected={index === active}
                    // `onMouseDown` and not `onClick`: the input's blur fires first and
                    // would close the list out from under the pointer.
                    onMouseDown={(event) => {
                      event.preventDefault();
                      go(hit);
                    }}
                    onMouseEnter={() => setActive(index)}
                    className={cn(
                      "flex min-h-touch w-full items-center gap-3 px-3.5 text-left",
                      "transition-colors duration-150 ease-out",
                      index === active ? "bg-accent-50" : "bg-transparent",
                    )}
                  >
                    <span
                      className={cn(
                        "grid h-9 w-9 shrink-0 place-items-center rounded-card",
                        hit.kind === "scheme"
                          ? "bg-accent-50 text-accent-700"
                          : "bg-teal-50 text-teal-700",
                      )}
                    >
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span className="min-w-0 flex-1 py-1.5">
                      <span className="block truncate font-medium" lang="en">
                        {hit.title}
                      </span>
                      <span className="block truncate text-sm text-ink-faint">
                        {hit.hint}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}

            {hits.length === 0 && (
              <li
                // Not a listbox option: there is nothing here to select, and announcing
                // it as one tells a screen reader there is a result when there is not.
                role="presentation"
                className="px-4 py-3 text-ink-faint"
              >
                {searching ? t("searching") : t("noResults", { term })}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
