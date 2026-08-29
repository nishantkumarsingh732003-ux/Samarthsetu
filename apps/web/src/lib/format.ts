/**
 * Indian digit grouping: 12,00,000 — not 1,200,000.
 *
 * A citizen reads lakhs, and a figure grouped the Western way is misread at a glance,
 * which for an amount of money is not a cosmetic problem.
 */
export function formatRupees(amount: number, locale = "en-IN"): string {
  return new Intl.NumberFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
    maximumFractionDigits: 0,
  }).format(Math.round(amount));
}

export function formatDistance(km: number | null): string {
  if (km === null) return "—";
  return km < 10 ? km.toFixed(1) : String(Math.round(km));
}
