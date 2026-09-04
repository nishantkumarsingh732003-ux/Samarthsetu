"use client";

/**
 * Where the Channel Finance System actually reaches — state, then district, then branch.
 *
 * This is the district drilldown, and it is built on the real PostGIS partner registry
 * rather than the design drop's hand-drawn SVG map with a `STATE_HOTSPOTS` constant. That
 * matters because the interesting cell is the empty one: a district with five banks and
 * no State Channelising Agency cannot process the schemes that route only through an SCA,
 * and an applicant who learns that after a bus journey has been misrouted — which is the
 * failure this whole project exists to prevent. So the gap is called out in words, in the
 * district row, before anyone travels.
 *
 * Deliberately unranked. "Which one should I go to?" is `/results/[scheme]/partners`,
 * which scores on distance, ticket size and current load and shows its working. A
 * directory sorted by anything starts being read as advice.
 */

import { ArrowLeft, Building2, ChevronRight, Phone, TriangleAlert } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useCatalogue } from "@/components/account/useCitizenData";
import { Button, Chip, Field, SelectInput, TextInput } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { getCoverage, getDirectory, getStateCoverage } from "@/lib/citizenApi";

import type { Coverage, PartnerDirectory, StateDrilldown } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

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

  // The branch list is fetched whenever any filter moves, including from the search box
  // with no state chosen — someone who knows their PIN code should not have to find
  // their state on a list first.
  useEffect(() => {
    if (!state && !query.trim() && !schemeCode) {
      setDirectory(null);
      return;
    }
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

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      <section className="panel grid gap-4 p-4 sm:grid-cols-2">
        <Field label={t("search")}>
          {({ id }) => (
            <TextInput
              id={id}
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          )}
        </Field>
        <Field label={t("filterScheme")}>
          {({ id }) => (
            <SelectInput
              id={id}
              value={schemeCode}
              onChange={(event) => setSchemeCode(event.target.value)}
            >
              <option value="">{t("allSchemes")}</option>
              {(catalogue.data?.schemes ?? []).map((scheme) => (
                <option key={scheme.code} value={scheme.code}>
                  {scheme.official_name}
                </option>
              ))}
            </SelectInput>
          )}
        </Field>
      </section>

      {!state ? (
        <section>
          <h2 className="font-display text-lg font-bold">{t("statesTitle")}</h2>
          {!coverage ? (
            <p role="status" className="panel mt-3 p-8 text-center text-ink-faint">
              {tCommon("loading")}
            </p>
          ) : (
            <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {coverage.states.map((entry) => (
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
                      <ChevronRight className="h-4 w-4 shrink-0 text-ink-faint" aria-hidden="true" />
                    </span>
                    <span className="numeric mt-1 block text-sm text-ink-faint">
                      {t("partnerCount", { count: entry.partner_count })} ·{" "}
                      {t("districtCount", { count: entry.district_count })}
                    </span>
                    <span className="mt-2 flex flex-wrap gap-1.5">
                      {Object.entries(entry.by_type).map(([type, count]) => (
                        <Chip key={type} tone="accent">
                          {type} {count}
                        </Chip>
                      ))}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : (
        <section>
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
            <p role="status" className="panel mt-3 p-8 text-center text-ink-faint">
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
                        <span className="font-display font-bold">{entry.district}</span>
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
                      {/* The empty cell, said out loud. A district with banks but no
                          State Channelising Agency routes differently, and finding that
                          out at the counter is the misrouting this project prevents. */}
                      {noSca && (
                        <span className="mt-3 flex items-start gap-2 rounded-card bg-warn-bg px-3 py-2 text-sm text-warn-fg">
                          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
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
        </section>
      )}

      {directory && (
        <section>
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="font-display text-lg font-bold">{t("title")}</h2>
            <p className="numeric text-sm text-ink-faint">
              {t("showing", { shown: directory.partners.length, total: directory.total })}
              {directory.truncated ? ` · ${t("truncated")}` : ""}
            </p>
          </div>

          {directory.partners.length === 0 ? (
            <p className="panel mt-3 p-8 text-center text-ink-faint">{t("noneHere")}</p>
          ) : (
            <ul className="mt-3 grid gap-3 lg:grid-cols-2">
              {directory.partners.map((partner) => {
                const phone =
                  typeof partner.contact?.phone === "string" ? partner.contact.phone : null;
                return (
                  <li key={partner.partner_id} className="panel p-5">
                    <div className="flex items-start gap-3">
                      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-card bg-teal-50 text-teal-700">
                        <Building2 className="h-5 w-5" aria-hidden="true" />
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold uppercase tracking-wide text-ink-faint">
                          {partner.type}
                        </p>
                        <h3 className="font-display font-bold">{partner.name}</h3>
                        <p className="mt-0.5 text-ink-muted">
                          {partner.district}, {partner.state}
                          {partner.pincode ? ` · ${partner.pincode}` : ""}
                        </p>
                        <ul className="mt-2 flex flex-wrap gap-1.5">
                          {partner.scheme_codes.map((code) => (
                            <li key={code}>
                              <Chip tone="accent">{code}</Chip>
                            </li>
                          ))}
                        </ul>
                        <div className="mt-3 flex flex-wrap items-center gap-3">
                          <Chip tone="good">{t("accepting")}</Chip>
                          {phone && (
                            <a href={`tel:${phone}`} className="btn-quiet min-h-0 px-2 py-1">
                              <Phone className="h-4 w-4" aria-hidden="true" />
                              {t("call")}
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Link href="/matches" className="btn-secondary text-base">
              {t("routeMe")}
            </Link>
            <p className="text-sm text-ink-faint">{t("routeMeHint")}</p>
          </div>

          <p className="mt-4 text-sm text-ink-faint">{directory.data_disclaimer}</p>
        </section>
      )}
    </div>
  );
}
