"use client";

/**
 * Where the Channel Finance System actually reaches — on a map, then state, then district.
 *
 * The map is the real one: every pin is a branch at its own latitude and longitude out of
 * the PostGIS registry, not the design drop's hand-drawn outline with a `STATE_HOTSPOTS`
 * constant behind it. That matters because the interesting thing here is the *absence* —
 * a district with five banks and no State Channelising Agency cannot process the schemes
 * that route only through an SCA, and an applicant who learns that after a bus journey
 * has been misrouted, which is the failure this whole project exists to prevent. An
 * illustration cannot show a gap it was never given; a map of the actual registry can.
 *
 * The drilldown behind the map says the same thing in words, in the district row, before
 * anyone travels.
 *
 * Deliberately unranked. "Which one should I go to?" is `/results/[scheme]/partners`,
 * which scores on distance, ticket size and current load and shows its working. A
 * directory sorted by anything starts being read as advice.
 */

import { ArrowLeft, ArrowRight, ChevronRight, MapPin, Phone, Search, TriangleAlert } from "lucide-react";
import dynamic from "next/dynamic";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useCatalogue } from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Link } from "@/i18n/navigation";
import { getCoverage, getDirectory, getStateCoverage } from "@/lib/citizenApi";

import type { Coverage, PartnerDirectory, StateDrilldown } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

/** Leaflet is ~150KB and only arrives once the map is on screen. A citizen who never
 *  opens this page never pays for it. */
const CoverageMap = dynamic(() => import("@/components/CoverageMap"), {
  ssr: false,
  loading: () => <div className="h-[26rem] w-full animate-pulse rounded-card bg-canvas" />,
});

/** The select's "no filter" option. Radix Select cannot hold an empty string as a value,
 *  so the sentinel is explicit rather than "" masquerading as one. */
const ANY = "__any__";

/** Branches per page. Twelve is roughly two phone screens of cards — enough that paging
 *  is rare once a state is chosen, small enough that the unfiltered national directory
 *  does not arrive as a few thousand DOM nodes. */
const PAGE = 12;

export function CoverageClient({ locale }: { locale: Locale }) {
  const t = useTranslations("coverage");
  const tCommon = useTranslations("common");
  const catalogue = useCatalogue(locale);

  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [state, setState] = useState<string | null>(null);
  const [drilldown, setDrilldown] = useState<StateDrilldown | null>(null);
  const [district, setDistrict] = useState<string | null>(null);
  const [directory, setDirectory] = useState<PartnerDirectory | null>(null);
  const [query, setQuery] = useState("");
  const [schemeCode, setSchemeCode] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showDrilldown, setShowDrilldown] = useState(false);
  const [shown, setShown] = useState(PAGE);

  useEffect(() => {
    void getCoverage().then((result) => result.ok && setCoverage(result.data));
  }, []);

  useEffect(() => {
    if (!state) {
      setDrilldown(null);
      return;
    }
    let cancelled = false;
    void getStateCoverage(state).then((result) => {
      if (!cancelled && result.ok) setDrilldown(result.data);
    });
    return () => {
      cancelled = true;
    };
  }, [state]);

  // The branch list is fetched whenever any filter moves, including with no state chosen
  // — someone who knows their PIN code should not have to find their state on a list
  // first, and the map needs something to draw before anyone has filtered anything.
  useEffect(() => {
    let cancelled = false;
    void getDirectory({
      state: state ?? undefined,
      district: district ?? undefined,
      schemeCode: schemeCode || undefined,
      q: query.trim() || undefined,
    }).then((result) => {
      if (!cancelled && result.ok) setDirectory(result.data);
    });
    return () => {
      cancelled = true;
    };
  }, [state, district, schemeCode, query]);

  // Back to the first page whenever the filters move: "show more" three times and then
  // pick a state should not leave someone thirty-six rows into a list of eleven.
  useEffect(() => {
    setShown(PAGE);
  }, [state, district, schemeCode, query]);

  const partners = directory?.partners ?? [];
  const visible = partners.slice(0, shown);
  const remaining = partners.length - visible.length;
  const states = coverage?.states ?? [];
  const selectedState = states.find((entry) => entry.state === state) ?? null;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      <Card>
        <CardContent className="grid gap-3 p-4 lg:grid-cols-[minmax(0,1fr)_14rem_14rem] lg:p-5">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint"
              aria-hidden="true"
            />
            <Input
              type="search"
              aria-label={t("search")}
              placeholder={t("searchPlaceholder")}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pl-10"
            />
          </div>

          <Select
            value={state ?? ANY}
            onValueChange={(next) => {
              setState(next === ANY ? null : next);
              setDistrict(null);
              setShowDrilldown(false);
            }}
          >
            <SelectTrigger aria-label={t("filterState")}>
              <SelectValue placeholder={t("allStates")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ANY}>{t("allStates")}</SelectItem>
              {states.map((entry) => (
                <SelectItem key={entry.state} value={entry.state}>
                  {entry.state}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={schemeCode || ANY}
            onValueChange={(next) => setSchemeCode(next === ANY ? "" : next)}
          >
            <SelectTrigger aria-label={t("filterScheme")}>
              <SelectValue placeholder={t("allSchemes")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ANY}>{t("allSchemes")}</SelectItem>
              {(catalogue.data?.schemes ?? []).map((scheme) => (
                <SelectItem key={scheme.code} value={scheme.code}>
                  {scheme.official_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* `items-start` plus a sticky map. The list is the tall column now that it pages
          rather than scrolling inside itself, and without these the map card stretched to
          match it — a 400px map sitting at the top of 1,700px of white. Sticky keeps the
          map beside whichever branches are being read, which is the whole point of having
          them side by side. */}
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <Card className="lg:sticky lg:top-4">
          <CardContent className="p-3 lg:p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm font-medium">
                <MapPin className="h-4 w-4 shrink-0 text-saffron" aria-hidden="true" />
                {state ?? t("allIndia")}
                {" · "}
                <span className="numeric">
                  {t("partnerCount", {
                    count: selectedState?.partner_count ?? directory?.total ?? 0,
                  })}
                </span>
              </span>
              <Button
                variant="primary"
                onClick={() => setShowDrilldown((open) => !open)}
                aria-expanded={showDrilldown}
                className="shrink-0 rounded-full text-base"
              >
                {t("districtDrilldown")}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>

            <CoverageMap
              partners={partners}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </CardContent>
        </Card>

        {/* The same partners in text, which is what a screen reader reads — the map is
            aria-hidden precisely because this list exists.

            PAGED, NOT SCROLLED. With no filter applied this is the whole national
            directory. A desktop scroll column used to hold it, which left the phone —
            where there is no such column — rendering a page 64,000 pixels tall: not a
            layout problem so much as a few thousand DOM nodes on the Rs 6,000 Android
            this product is built for (CLAUDE.md rule 5). Twelve at a time, and a button
            for the rest, fixes both and needs no nested scroller — which on touch is the
            worst of the available answers anyway. */}
        <div className="space-y-3 lg:pr-1">
          {!directory ? (
            <Card>
              <CardContent role="status" className="p-8 text-center text-ink-faint">
                {tCommon("loading")}
              </CardContent>
            </Card>
          ) : partners.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-ink-muted">
                {t("noneHere")}
              </CardContent>
            </Card>
          ) : (
            <ul className="space-y-3">
              {visible.map((partner) => {
                const phone =
                  typeof partner.contact?.phone === "string" ? partner.contact.phone : null;
                return (
                  <li key={partner.partner_id}>
                    <Card
                      interactive
                      className={
                        partner.partner_id === selectedId ? "border-accent-700" : ""
                      }
                    >
                      <CardContent className="flex items-start gap-3 p-4 lg:p-5">
                        <span
                          aria-hidden="true"
                          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-teal-50 text-teal-700"
                        >
                          <MapPin className="h-5 w-5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                            {t(`type.${partner.type}`)}
                          </p>
                          <h3 className="mt-0.5 font-display text-lg font-bold">
                            {partner.name}
                          </h3>
                          <p className="mt-0.5 text-ink-faint">
                            {partner.district}, {partner.state}
                            {partner.pincode ? ` · ${partner.pincode}` : ""}
                          </p>
                          <ul className="mt-2.5 flex flex-wrap gap-1.5">
                            {partner.scheme_codes.map((code) => (
                              <li key={code}>
                                <Chip tone="accent">{code}</Chip>
                              </li>
                            ))}
                          </ul>
                          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                            <Chip tone={partner.is_accepting ? "good" : "warn"}>
                              {partner.is_accepting ? t("accepting") : t("paused")}
                            </Chip>
                            <span className="flex items-center gap-1">
                              {phone && (
                                <Button
                                  asChild
                                  variant="ghost"
                                  size="icon"
                                  className="rounded-full text-ink-faint"
                                >
                                  <a href={`tel:${phone}`} aria-label={t("call")}>
                                    <Phone className="h-4 w-4" aria-hidden="true" />
                                  </a>
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setSelectedId(partner.partner_id)}
                                aria-label={t("showOnMap", { name: partner.name })}
                                className="rounded-full text-accent-700"
                              >
                                <ArrowRight className="h-4 w-4" aria-hidden="true" />
                              </Button>
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </li>
                );
              })}
            </ul>
          )}

          {remaining > 0 && (
            <Button
              variant="secondary"
              onClick={() => setShown((current) => current + PAGE)}
              className="w-full"
            >
              {t("showMore", { count: remaining })}
            </Button>
          )}

          {directory && (
            <p className="numeric px-1 text-sm text-ink-faint">
              {t("showing", { shown: visible.length, total: directory.total })}
              {directory.truncated ? ` · ${t("truncated")}` : ""}
            </p>
          )}
        </div>
      </div>

      {showDrilldown && (
        <Card>
          <CardContent className="p-5 lg:p-6">
            {!state ? (
              <>
                <h2 className="font-display text-lg font-bold">{t("statesTitle")}</h2>
                {!coverage ? (
                  <p role="status" className="mt-3 text-center text-ink-faint">
                    {tCommon("loading")}
                  </p>
                ) : (
                  <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {states.map((entry) => (
                      <li key={entry.state}>
                        <button
                          type="button"
                          onClick={() => {
                            setState(entry.state);
                            setDistrict(null);
                          }}
                          className="panel-link w-full p-4 text-left"
                        >
                          <span className="flex items-center justify-between gap-3">
                            <span className="font-display font-bold">{entry.state}</span>
                            <ChevronRight
                              className="h-4 w-4 shrink-0 text-ink-faint"
                              aria-hidden="true"
                            />
                          </span>
                          <span className="numeric mt-1 block text-sm text-ink-faint">
                            {t("partnerCount", { count: entry.partner_count })} ·{" "}
                            {t("districtCount", { count: entry.district_count })}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="font-display text-lg font-bold">
                    {t("districtsIn", { state: drilldown?.state ?? state })}
                  </h2>
                  <Button
                    variant="quiet"
                    onClick={() => {
                      setState(null);
                      setDistrict(null);
                    }}
                  >
                    <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                    {t("backToStates")}
                  </Button>
                </div>

                {!drilldown ? (
                  <p role="status" className="mt-3 text-center text-ink-faint">
                    {tCommon("loading")}
                  </p>
                ) : (
                  <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {drilldown.districts.map((entry) => {
                      const noSca = !("SCA" in entry.by_type);
                      const active = district === entry.district;
                      return (
                        <li key={entry.district}>
                          <button
                            type="button"
                            aria-pressed={active}
                            onClick={() => setDistrict(active ? null : entry.district)}
                            className={`panel-link w-full p-4 text-left ${
                              active ? "border-accent-700" : ""
                            }`}
                          >
                            <span className="flex items-center justify-between gap-3">
                              <span className="font-display font-bold">
                                {entry.district}
                              </span>
                              <span className="numeric text-sm text-ink-faint">
                                {entry.partner_count}
                              </span>
                            </span>
                            <span className="mt-2 flex flex-wrap gap-1.5">
                              {Object.entries(entry.by_type).map(([type, count]) => (
                                <Chip key={type} tone="accent">
                                  {type} {count}
                                </Chip>
                              ))}
                            </span>
                            {/* The empty cell, said out loud. A district with banks but
                                no State Channelising Agency routes differently, and
                                finding that out at the counter is the misrouting this
                                project prevents. */}
                            {noSca && (
                              <span className="mt-3 flex items-start gap-2 rounded-card bg-warn-bg px-3 py-2 text-sm text-warn-fg">
                                <TriangleAlert
                                  className="mt-0.5 h-4 w-4 shrink-0"
                                  aria-hidden="true"
                                />
                                <span>
                                  {t("gapWarning")} {t("gapExplain")}
                                </span>
                              </span>
                            )}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Link href="/matches" className="btn-secondary text-base">
          {t("routeMe")}
        </Link>
        <p className="text-sm text-ink-faint">{t("routeMeHint")}</p>
      </div>

      {directory && <p className="text-sm text-ink-faint">{directory.data_disclaimer}</p>}
    </div>
  );
}
