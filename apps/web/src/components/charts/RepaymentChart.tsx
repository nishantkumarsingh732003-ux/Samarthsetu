"use client";

/**
 * Principal against interest, year by year — the only chart in the citizen surface.
 *
 * Hand-drawn SVG rather than a charting library. Recharts, which the design drop used
 * for this and for three decorative pie charts, is ~95KB gzipped against a 200KB budget
 * for the entire route. One stacked bar chart does not justify a third of the budget on
 * a 2G connection.
 *
 * The other three charts in the drop were dropped, not ported. A donut showing a single
 * "92% match" is a number wearing a costume; it is a stat tile here. The ministry pies
 * were over categories with no part-to-whole meaning.
 *
 * Colour: `#2a78d6` / `#eb6834`, not the brand navy and saffron. Brand colours are tuned
 * for text contrast and are too dark and too grey to work as fills — navy fails the
 * chroma floor (0.095, reads as grey) and saffron sits at 2.09:1 on white. These two
 * clear every check in the palette validator on a white surface: adjacent CVD ΔE 24.7
 * (protan) against a target of 8, normal-vision ΔE 33.6 against a floor of 15, both
 * above 3:1 contrast. Identity is never carried by colour alone regardless — the two
 * series are direct-labelled inside the first bar, there is a legend, and the same
 * numbers are available as a table.
 */

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Disclosure } from "@/components/ui/Panel";
import { formatRupees } from "@/lib/format";

import type { YearSlice } from "@/lib/emi";
import type { Locale } from "@/i18n/config";

const SERIES = {
  principal: "#2a78d6",
  interest: "#eb6834",
} as const;

// Geometry in viewBox units. The SVG scales; the proportions do not.
const WIDTH = 640;
const HEIGHT = 260;
const PAD = { top: 16, right: 12, bottom: 34, left: 56 };
const PLOT_W = WIDTH - PAD.left - PAD.right;
const PLOT_H = HEIGHT - PAD.top - PAD.bottom;
// A 2px surface gap between stacked segments, so the boundary is a real edge rather
// than a colour change two adjacent hues have to carry on their own.
const SEGMENT_GAP = 2;

export function RepaymentChart({
  years,
  locale,
}: {
  years: YearSlice[];
  locale: Locale;
}) {
  const t = useTranslations("calculator");
  const [hovered, setHovered] = useState<number | null>(null);

  if (years.length === 0) return null;

  const max = Math.max(...years.map((year) => year.principal + year.interest));
  const bandWidth = PLOT_W / years.length;
  // Thin marks: the bar occupies 62% of its band, leaving the rest as breathing room.
  const barWidth = Math.min(bandWidth * 0.62, 64);
  const scale = (value: number) => (max === 0 ? 0 : (value / max) * PLOT_H);

  // Four gridlines. Recessive — they orient the eye and must not compete with the data.
  // The unit is chosen once from the maximum, so the axis does not read "1.8L, 1.3L,
  // 88K, 44K" and make the reader convert between scales mid-column.
  const unit = axisUnit(max);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((fraction) => ({
    y: PAD.top + PLOT_H - fraction * PLOT_H,
    label: unit(max * fraction),
  }));

  const active = hovered === null ? null : years[hovered];

  return (
    <figure className="m-0">
      <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-muted">
        <span className="inline-flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="inline-block h-3 w-3 rounded-sm"
            style={{ background: SERIES.principal }}
          />
          {t("seriesPrincipal")}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="inline-block h-3 w-3 rounded-sm"
            style={{ background: SERIES.interest }}
          />
          {t("seriesInterest")}
        </span>
      </figcaption>

      <div className="relative mt-2">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="h-56 w-full"
          role="img"
          aria-label={t("chartAlt")}
        >
          {ticks.map((tick) => (
            <g key={tick.y}>
              <line
                x1={PAD.left}
                x2={WIDTH - PAD.right}
                y1={tick.y}
                y2={tick.y}
                stroke="#E2E8F0"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 8}
                y={tick.y + 4}
                textAnchor="end"
                fontSize={11}
                fill="#55617A"
              >
                {tick.label}
              </text>
            </g>
          ))}

          {years.map((year, index) => {
            const x = PAD.left + index * bandWidth + (bandWidth - barWidth) / 2;
            const principalH = scale(year.principal);
            const interestH = Math.max(0, scale(year.interest) - SEGMENT_GAP);
            const principalY = PAD.top + PLOT_H - principalH;
            const interestY = principalY - SEGMENT_GAP - interestH;
            const dim = hovered !== null && hovered !== index;

            return (
              <g
                key={year.year}
                opacity={dim ? 0.45 : 1}
                onMouseEnter={() => setHovered(index)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(index)}
                onBlur={() => setHovered(null)}
              >
                {/* A full-height hit target, so the pointer does not have to find a
                    2px-wide segment on a phone. */}
                <rect
                  x={PAD.left + index * bandWidth}
                  y={PAD.top}
                  width={bandWidth}
                  height={PLOT_H}
                  fill="transparent"
                />
                {/* The bottom segment sits on the baseline and is square there; only
                    the data end — the top of the stack — is rounded. */}
                <rect
                  x={x}
                  y={principalY}
                  width={barWidth}
                  height={principalH}
                  fill={SERIES.principal}
                />
                <rect
                  x={x}
                  y={interestY}
                  width={barWidth}
                  height={interestH}
                  rx={4}
                  fill={SERIES.interest}
                />

                {/* Direct labels, on the first bar only and only where the segment is
                    tall enough to hold them. A number on every segment is noise. */}
                {index === 0 && principalH > 34 && (
                  <text
                    x={x + barWidth / 2}
                    y={principalY + 18}
                    textAnchor="middle"
                    fontSize={11}
                    fontWeight={600}
                    fill="#FFFFFF"
                  >
                    {t("seriesPrincipal")}
                  </text>
                )}
                {index === 0 && interestH > 34 && (
                  <text
                    x={x + barWidth / 2}
                    y={interestY + 18}
                    textAnchor="middle"
                    fontSize={11}
                    fontWeight={600}
                    fill="#FFFFFF"
                  >
                    {t("seriesInterest")}
                  </text>
                )}

                <text
                  x={PAD.left + index * bandWidth + bandWidth / 2}
                  y={HEIGHT - 12}
                  textAnchor="middle"
                  fontSize={11}
                  fill="#55617A"
                >
                  {year.year}
                </text>
              </g>
            );
          })}

          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={PAD.top + PLOT_H}
            y2={PAD.top + PLOT_H}
            stroke="#94A3B8"
            strokeWidth={1}
          />
        </svg>

        {active && (
          <div
            role="status"
            className="pointer-events-none absolute right-2 top-2 rounded-card border
                       border-line bg-surface/95 px-3 py-2 text-sm shadow-card"
          >
            <p className="font-medium">{t("yearLabel", { year: active.year })}</p>
            <p className="numeric text-ink-muted">
              {t("seriesPrincipal")} {formatRupees(active.principal, locale)}
            </p>
            <p className="numeric text-ink-muted">
              {t("seriesInterest")} {formatRupees(active.interest, locale)}
            </p>
          </div>
        )}
      </div>

      {/* The same numbers, readable without colour vision, a pointer, or a screen wide
          enough for the chart. Not a fallback — an equal path to the data. */}
      <Disclosure summary={t("showTable")} className="mt-3">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line text-ink-faint">
              <th scope="col" className="py-1.5 font-medium">
                {t("colYear")}
              </th>
              <th scope="col" className="py-1.5 text-right font-medium">
                {t("seriesPrincipal")}
              </th>
              <th scope="col" className="py-1.5 text-right font-medium">
                {t("seriesInterest")}
              </th>
              <th scope="col" className="py-1.5 text-right font-medium">
                {t("colBalance")}
              </th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year.year} className="border-b border-line/60">
                <th scope="row" className="py-1.5 font-normal">
                  {year.year}
                </th>
                <td className="numeric py-1.5 text-right">
                  {formatRupees(year.principal, locale)}
                </td>
                <td className="numeric py-1.5 text-right">
                  {formatRupees(year.interest, locale)}
                </td>
                <td className="numeric py-1.5 text-right text-ink-muted">
                  {formatRupees(year.closingBalance, locale)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Disclosure>
    </figure>
  );
}

/**
 * One unit for the whole axis, picked from its largest value.
 *
 * "3L" reads at a glance where "3,00,000" does not — but only if every label on the axis
 * uses the same scale. Choosing per label produced "1.8L, 1.3L, 88K, 44K", which makes
 * the reader do arithmetic to compare two gridlines.
 */
function axisUnit(max: number): (value: number) => string {
  if (max >= 100000) {
    return (value) => (value === 0 ? "0" : `${(value / 100000).toFixed(1)}L`);
  }
  if (max >= 1000) {
    return (value) => (value === 0 ? "0" : `${Math.round(value / 1000)}K`);
  }
  return (value) => String(Math.round(value));
}
