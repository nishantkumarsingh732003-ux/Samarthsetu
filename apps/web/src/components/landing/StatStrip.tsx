"use client";

/**
 * The four numbers under the hero, read from the API rather than written down.
 *
 * The design drop had these as literals — "12,480+ entrepreneurs guided", "1,240 channel
 * partners", "42 schemes indexed". On a page carrying a ministry's name those are not
 * placeholder copy, they are false claims, and CLAUDE.md rule 6 puts the demo path off
 * limits for invented data. So three of them come from `/schemes` and
 * `/partners/coverage`, and the fourth — languages — is counted from the locale list,
 * split into the two a speaker has reviewed and the four still machine-drafted, because
 * "six languages" and "two reviewed languages" are different claims.
 *
 * "Entrepreneurs guided" has no honest source: there is no public endpoint that counts
 * citizens, and there should not be one. The tile in that position shows districts with
 * a Channel Partner instead, which is both real and the thing a citizen actually wants
 * to know.
 *
 * Until the numbers arrive the tiles show a dash — not a spinner and not a guess. A
 * number that appears and then changes is worse than one that arrives late.
 */

import { Building2, Languages, MapPin, ScrollText } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { getCatalogue, getCoverage } from "@/lib/citizenApi";
import { LOCALES, REVIEWED_LOCALES } from "@/i18n/config";

import type { Locale } from "@/i18n/config";

interface Stats {
  schemes: number;
  partners: number;
  districts: number;
}

export function StatStrip({ locale }: { locale: Locale }) {
  const t = useTranslations("landing");
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([getCatalogue(locale), getCoverage()]).then(([catalogue, coverage]) => {
      if (cancelled || !catalogue.ok || !coverage.ok) return;
      setStats({
        schemes: catalogue.data.schemes.length,
        partners: coverage.data.total_partners,
        districts: coverage.data.states.reduce((sum, s) => sum + s.district_count, 0),
      });
    });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const reviewed = REVIEWED_LOCALES.length;

  const tiles = [
    { Icon: MapPin, label: t("statDistricts"), value: stats?.districts ?? null, hint: null },
    { Icon: ScrollText, label: t("statSchemes"), value: stats?.schemes ?? null, hint: null },
    { Icon: Building2, label: t("statPartners"), value: stats?.partners ?? null, hint: null },
    {
      Icon: Languages,
      label: t("statLanguages"),
      value: t("statLanguagesValue", {
        verified: reviewed,
        draft: LOCALES.length - reviewed,
      }),
      hint: t("statLanguagesHint"),
    },
  ];

  return (
    <ul className="grid grid-cols-2 gap-3.5 lg:grid-cols-4">
      {tiles.map((tile) => (
        <li key={tile.label} className="panel p-4 lg:p-5">
          <tile.Icon className="h-5 w-5 text-teal-700" aria-hidden="true" />
          <p className="numeric mt-3 font-display text-2xl font-extrabold tracking-tight">
            {tile.value ?? "—"}
          </p>
          <p className="mt-1 text-ink-faint">{tile.label}</p>
          {tile.hint ? <p className="text-sm text-ink-faint">{tile.hint}</p> : null}
        </li>
      ))}
    </ul>
  );
}
