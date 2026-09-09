"use client";

/**
 * The application draft as a document — what "Download PDF" produces.
 *
 * Rendered into the page and hidden until print, exactly like `RepaymentPlanSheet`, and
 * for the same reason: the browser's own Save as PDF makes a real file on a ₹6,000
 * Android phone with no library and no bytes, and a client-side PDF generator would cost
 * ~300KB to do the job worse. See that file for the full argument.
 *
 * Amounts print as "Rs" and not "₹" — the reference PDF renders the rupee sign as a
 * superscript "1" throughout because its embedded font has no glyph for it, and a page of
 * money is the last place to accept that. "Rs" is the rule pack's own house style.
 *
 * NOTHING HERE IS AN APPLICATION. It is the citizen's own answers laid out in the order a
 * partner's form asks for them, so they can be checked before anyone walks to a counter.
 * The footer says so. A document with a ministry name across the top that reads like a
 * sanction letter would be a serious thing to hand someone.
 */

import { useTranslations } from "next-intl";

import { formatRupees } from "@/lib/format";

import type { CitizenProfile } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export interface DraftSection {
  heading: string;
  /** Teal rather than navy, so the three bands are told apart at a glance. */
  tone?: "navy" | "teal";
  rows: { label: string; value: string }[];
}

export function ApplicationDraftSheet({
  sections,
  reference,
  scheme,
  generatedAt,
}: {
  sections: DraftSection[];
  /** The application id, once there is one. A draft has not got one yet. */
  reference: string | null;
  scheme: string | null;
  generatedAt: string;
}) {
  const t = useTranslations("applicationDraft");
  const tApp = useTranslations("app");

  return (
    <section className="print-only text-ink" aria-hidden="true">
      <header
        className="bg-accent-800 px-8 py-7 text-white"
        style={{ printColorAdjust: "exact", WebkitPrintColorAdjust: "exact" }}
      >
        <p className="font-display text-3xl font-extrabold">{tApp("title")}</p>
        <p className="mt-1.5 text-sm text-white/80">{t("sheetOrgLine")}</p>
      </header>

      <div className="px-8 py-7">
        <p className="border-b border-line pb-4 font-semibold">{t("sheetTitle")}</p>

        <div className="mt-5 space-y-1">
          {reference && (
            <p className="numeric text-ink-muted">{t("sheetReference", { reference })}</p>
          )}
          {scheme && (
            <p className="text-ink-muted" lang="en">
              {t("sheetScheme", { scheme })}
            </p>
          )}
        </div>

        {sections.map((section) => (
          <table key={section.heading} className="mt-6 w-full border-collapse text-left">
            <thead>
              <tr
                className={`text-white ${
                  section.tone === "teal" ? "bg-teal-700" : "bg-accent-800"
                }`}
                style={{ printColorAdjust: "exact", WebkitPrintColorAdjust: "exact" }}
              >
                <th scope="col" colSpan={2} className="border border-line px-3 py-2">
                  {section.heading}
                </th>
              </tr>
            </thead>
            <tbody>
              {section.rows.map((row) => (
                <tr key={row.label}>
                  <th
                    scope="row"
                    className="w-1/3 border border-line px-3 py-2 font-semibold"
                  >
                    {row.label}
                  </th>
                  <td className="border border-line px-3 py-2">{row.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

        <div className="mt-8 border-t border-line pt-4 text-sm text-ink-faint">
          <p>{t("sheetDisclaimer")}</p>
          <p className="numeric mt-1">{t("generatedAt", { when: generatedAt })}</p>
        </div>
      </div>
    </section>
  );
}

/** Money as this document prints it. Exported so the page builds its rows with the same
 *  formatting the sheet would have used. */
export function sheetMoney(value: number | null | undefined, locale: Locale): string {
  return value == null ? "—" : `Rs ${formatRupees(value, locale)}`;
}

/** The profile fields a partner's form asks for, in the order it asks for them. */
export function draftValue(
  profile: CitizenProfile | null | undefined,
  field: keyof CitizenProfile,
): string {
  const value = profile?.[field];
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return String(value);
  return String(value);
}
