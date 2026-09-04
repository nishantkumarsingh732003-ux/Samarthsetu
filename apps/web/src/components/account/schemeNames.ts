/**
 * code -> official name, built from a match run.
 *
 * The engine returns internal codes in `redirect_suggestion` ("NSFDC_TERM_LOAN"). Showing
 * one to a citizen is both unreadable and not the scheme's legal name — the bug OI-25
 * closed on the explanation path. Every result in a run carries its own `official_name`,
 * so the run is its own lookup table and no extra request is needed.
 */
import type { MatchResult } from "@/lib/api";

export function schemeNamesFrom(results: MatchResult[] | undefined): Record<string, string> {
  const names: Record<string, string> = {};
  for (const result of results ?? []) names[result.scheme_code] = result.official_name;
  return names;
}
