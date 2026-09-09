/**
 * Every rule in the published pack must map to a criterion label, and every label the
 * mapping can produce must exist in all six catalogues.
 *
 * Without this, adding a rule to a YAML file silently degrades the matches card: the row
 * falls back to the engine sentence, the two-column grid goes ragged, and nobody finds
 * out until a screenshot. The fallback is the right *runtime* behaviour — verbose beats
 * blank — but it should never be reached in a shipped build, and that is what this pins.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { criterionKey } from "./criteriaLabels";

const LOCALES = ["en", "hi", "mr", "bn", "ta", "te"] as const;

const RULES = join(__dirname, "..", "..", "..", "..", "..", "packages", "rules", "dist", "rules.json");
const MESSAGES = (locale: string) =>
  join(__dirname, "..", "..", "..", "messages", `${locale}.json`);

interface RulePack {
  schemes: { rules: { id: string }[] }[];
}

function ruleIds(): string[] {
  const pack = JSON.parse(readFileSync(RULES, "utf8")) as RulePack;
  return pack.schemes.flatMap((scheme) => scheme.rules.map((rule) => rule.id));
}

describe("criterionKey", () => {
  it("covers every rule id in the published pack", () => {
    const unmapped = ruleIds().filter((id) => criterionKey(id) === null);
    expect(unmapped).toEqual([]);
  });

  it("resolves to a message that exists in every locale", () => {
    const keys = new Set(ruleIds().map((id) => criterionKey(id)!));
    expect(keys.size).toBeGreaterThan(0);

    for (const locale of LOCALES) {
      const messages = JSON.parse(readFileSync(MESSAGES(locale), "utf8"));
      for (const key of keys) {
        expect(
          messages.matches?.criteria?.[key],
          `matches.criteria.${key} missing from ${locale}.json`,
        ).toBeTruthy();
      }
    }
  });

  it("returns null for a rule it has not been taught, so the caller can fall back", () => {
    expect(criterionKey("XX_SOMETHING_NEW")).toBeNull();
  });
});
