"use client";

/**
 * The four numbers on the landing page, read from the API rather than written down.
 *
 * The design drop had these as literals — "12,480+ entrepreneurs guided", "1,240 channel
 * partners", "42 schemes indexed". On a page carrying a ministry's name those are not
 * placeholder copy, they are false claims, and CLAUDE.md rule 6 puts the demo path off
 * limits for invented data.
 *
 * So they come from `/schemes` and `/partners/coverage`. Until they arrive the tiles show
 * a dash, not a spinner and not a guess: a number that appears and then changes is worse
 * than one that arrives late.
 */

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { getCatalogue, getCoverage } from "@/lib/citizenApi";
import { LOCALES } from "@/i18n/config";

import type { Locale } from "@/i18n/config";

interface Stats {
  schemes: number;
  partners: number;
  engineVersion: string;
}

export function LiveStats({ locale }: { locale: Locale }) {
  const t = useTranslations("landing");
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([getCatalogue(locale), getCoverage()]).then(([catalogue, coverage]) => {
      if (cancelled || !catalogue.ok || !coverage.ok) return;
      setStats({
        schemes: catalogue.data.schemes.length,
        partners: coverage.data.total_partners,
        engineVersion: catalogue.data.engine_version,
      });
    });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const tiles = [
    { label: t("statSchemes"), value: stats ? String(stats.schemes) : null },
    { label: t("statPartners"), value: stats ? String(stats.partners) : null },
    { label: t("statLanguages"), value: String(LOCALES.length) },
    { label: t("statEngine"), value: stats ? stats.engineVersion : null },
  ];

  return (
    <ul className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {tiles.map((tile) => (
        <li key={tile.label} className="panel p-5">
          <p className="text-sm font-medium text-ink-faint">{tile.label}</p>
          <p className="numeric mt-2 font-display text-2xl font-extrabold text-accent-700">
            {tile.value ?? "—"}
          </p>
        </li>
      ))}
    </ul>
  );
}
