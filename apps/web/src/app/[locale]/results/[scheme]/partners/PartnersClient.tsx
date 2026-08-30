"use client";

import dynamic from "next/dynamic";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n/config";
import { routePartners, type RouteResponse } from "@/lib/api";
import { formatDistance, formatRupees } from "@/lib/format";

// Leaflet is ~150KB and most citizens never open the map, so it is loaded on demand
// and excluded from server rendering entirely.
const PartnerMap = dynamic(() => import("@/components/PartnerMap"), {
  ssr: false,
  loading: () => <div className="h-72 w-full animate-pulse rounded-card bg-line/40" />,
});

const COMPONENT_LABELS: Record<string, string> = {
  distance: "scoreDistance",
  turnaround: "scoreTurnaround",
  type_affinity: "scoreAffinity",
  load: "scoreLoad",
};

export function PartnersClient({
  locale,
  schemeCode,
}: {
  locale: Locale;
  schemeCode: string;
}) {
  const t = useTranslations("partners");
  const c = useTranslations("common");
  const search = useSearchParams();
  const runId = search.get("run");
  const family = search.get("family") ?? "";

  const [data, setData] = useState<RouteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showMap, setShowMap] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const amount = Number(search.get("amount") ?? 0);
    const district = search.get("district") ?? undefined;
    const result = await routePartners({
      schemeCode,
      amount: amount > 0 ? amount : 50000,
      district,
    });
    if (result.ok) setData(result.data);
    else setError(result.error === "offline" ? c("offline") : c("error"));
  }, [c, schemeCode, search]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return (
      <div className="card p-5">
        <p role="alert" className="text-lg">
          {error}
        </p>
        <button type="button" onClick={() => void load()} className="btn-primary mt-4 w-full">
          {c("retry")}
        </button>
      </div>
    );
  }

  if (!data) return <p className="text-lg">{c("loading")}</p>;

  return (
    <div className="space-y-5">
      <p className="text-base text-ink-muted">
        {t("forScheme", { scheme: data.scheme_name })} · Rs{" "}
        {formatRupees(data.amount_requested, locale)}
      </p>

      <button
        type="button"
        onClick={() => setShowMap((value) => !value)}
        className="btn-secondary w-full"
      >
        {showMap ? t("showList") : t("showMap")}
      </button>

      {showMap ? <PartnerMap origin={data.origin} partners={data.partners} /> : null}

      {data.partners.length === 0 ? (
        <p className="card p-5 text-lg">{t("noPartners")}</p>
      ) : (
        <ul className="space-y-4">
          {data.partners.map((partner) => (
            <li key={partner.partner_id}>
              <article className="card p-5">
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-semibold text-accent-700">
                    #{partner.rank}
                  </span>
                  <h2 className="text-lg font-semibold">{partner.name}</h2>
                </div>
                <p className="mt-1 text-base text-ink-muted">
                  {t(`types.${partner.type}` as "types.SCA")} · {partner.district}
                </p>

                <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-base">
                  <div className="flex gap-1">
                    <dt className="text-ink-faint">📍</dt>
                    <dd>{t("distance", { km: formatDistance(partner.distance_km) })}</dd>
                  </div>
                  {partner.avg_turnaround_days !== null ? (
                    <div className="flex gap-1">
                      <dt className="text-ink-faint">⏱</dt>
                      <dd>{t("turnaround", { days: partner.avg_turnaround_days })}</dd>
                    </div>
                  ) : null}
                  {partner.active_load !== null ? (
                    <div className="flex gap-1">
                      <dt className="text-ink-faint">📊</dt>
                      <dd>{t("load", { pct: partner.active_load })}</dd>
                    </div>
                  ) : null}
                </dl>

                {/* The whole journey converges here: this partner, for this scheme,
                    for this amount. Everything the application needs travels in the
                    query string so the next screen never has to guess. */}
                <Link
                  href={{
                    pathname: `/${locale}/apply/${schemeCode}`,
                    query: {
                      partner: partner.partner_id,
                      partnerName: partner.name,
                      partnerType: partner.type,
                      ...(family ? { family } : {}),
                      amount: String(data.amount_requested),
                      ...(runId ? { run: runId } : {}),
                    },
                  }}
                  className="btn-primary mt-4 block w-full text-center"
                >
                  {t("applyHere")}
                </Link>

                <button
                  type="button"
                  onClick={() =>
                    setExpanded(expanded === partner.partner_id ? null : partner.partner_id)
                  }
                  aria-expanded={expanded === partner.partner_id}
                  className="btn-secondary mt-3 w-full text-base"
                >
                  {t("whyRankedHere")}
                </button>

                {expanded === partner.partner_id ? (
                  // Every component of the ranking, shown as a bar. The citizen can see
                  // that a closer branch lost because it was busy, rather than being
                  // handed one opaque number.
                  <ul className="mt-3 space-y-2">
                    {Object.entries(partner.score_breakdown).map(([key, component]) => (
                      <li key={key}>
                        <div className="flex justify-between text-sm">
                          <span>{t(COMPONENT_LABELS[key] as "scoreDistance")}</span>
                          <span className="text-ink-faint">
                            {String(component.value)} {component.unit === "km" ? "km" : ""}
                          </span>
                        </div>
                        <div
                          role="meter"
                          aria-valuenow={Math.round(component.score * 100)}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-label={t(COMPONENT_LABELS[key] as "scoreDistance")}
                          className="mt-1 h-2 w-full rounded-full bg-line"
                        >
                          <div
                            className="h-2 rounded-full bg-accent-600"
                            style={{ width: `${Math.round(component.score * 100)}%` }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            </li>
          ))}
        </ul>
      )}

      {/* The screen that proves misrouting is prevented: branches that are close but
          genuinely cannot take this application, each with the exact reason. */}
      {data.why_not.length > 0 ? (
        <section aria-labelledby="whynot-heading" className="card border-2 border-warn-line p-5">
          <h2 id="whynot-heading" className="text-lg font-semibold text-warn-fg">
            {t("nearbyNotAuthorised")}
          </h2>
          <p className="mt-1 text-base text-ink-muted">{t("nearbyExplainer")}</p>
          <ul className="mt-3 space-y-3">
            {data.why_not.map((entry) => (
              <li key={entry.partner_id} className="border-t border-line pt-3 text-base">
                <p className="font-medium">{entry.name}</p>
                <p className="text-ink-muted">{entry.reason}</p>
                <code className="mt-1 inline-block rounded bg-line/60 px-1.5 py-0.5 text-xs">
                  {entry.reason_code}
                </code>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <p className="px-1 text-sm text-ink-faint">{t("syntheticData")}</p>
    </div>
  );
}
