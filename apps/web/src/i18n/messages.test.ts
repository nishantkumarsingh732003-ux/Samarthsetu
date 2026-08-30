import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

/**
 * ICU placeholder parity across the six catalogues.
 *
 * `scripts/check-i18n.mjs` proves every locale has every *key*. It does not prove the
 * values are usable: a Tamil string that drops `{count}`, or spells it `{counts}`,
 * renders a citizen a sentence with a hole in it — or throws inside next-intl. Key
 * parity passes and the page is still broken, which is exactly the class of bug worth
 * a test.
 */
const LOCALES = ["en", "hi", "mr", "bn", "ta", "te"] as const;
const MESSAGES = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "messages");

type Catalogue = Record<string, unknown>;

function load(locale: string): Catalogue {
  return JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), "utf8")) as Catalogue;
}

function flatten(object: Catalogue, prefix = ""): Map<string, string> {
  const out = new Map<string, string>();
  for (const [key, value] of Object.entries(object)) {
    if (key === "_meta") continue;
    if (value && typeof value === "object") {
      for (const [k, v] of flatten(value as Catalogue, `${prefix}${key}.`)) out.set(k, v);
    } else if (typeof value === "string") {
      out.set(`${prefix}${key}`, value);
    }
  }
  return out;
}

function placeholders(value: string): Set<string> {
  return new Set([...value.matchAll(/\{(\w+)/g)].map((match) => match[1]));
}

const catalogues = Object.fromEntries(
  LOCALES.map((locale) => [locale, flatten(load(locale))]),
) as Record<(typeof LOCALES)[number], Map<string, string>>;

describe("message catalogues", () => {
  it.each(LOCALES.filter((locale) => locale !== "en"))(
    "%s uses exactly the placeholders English does",
    (locale) => {
      const problems: string[] = [];
      for (const [key, english] of catalogues.en) {
        const expected = placeholders(english);
        const actual = placeholders(catalogues[locale].get(key) ?? "");
        const missing = [...expected].filter((name) => !actual.has(name));
        const extra = [...actual].filter((name) => !expected.has(name));
        if (missing.length) problems.push(`${key}: missing {${missing.join("}, {")}}`);
        if (extra.length) problems.push(`${key}: unexpected {${extra.join("}, {")}}`);
      }
      expect(problems).toEqual([]);
    },
  );

  it.each(LOCALES)("%s has no empty strings", (locale) => {
    const empty = [...catalogues[locale]].filter(([, value]) => !value.trim()).map(([key]) => key);
    expect(empty).toEqual([]);
  });

  it.each(LOCALES.filter((locale) => locale !== "en"))(
    "%s keeps the official scheme names it is not allowed to translate",
    (locale) => {
      // CLAUDE.md: official scheme names stay verbatim. Nothing in a catalogue should
      // be a translated rendering of one — those come from the API, not from here.
      for (const [, value] of catalogues[locale]) {
        expect(value).not.toMatch(/Micro Finance Scheme|Educational Loan Scheme/);
      }
    },
  );

  it("declares a review status for every locale", () => {
    for (const locale of LOCALES) {
      const meta = load(locale)._meta as { status?: string } | undefined;
      expect(meta?.status, `${locale} has no _meta.status`).toMatch(/^(verified|draft)$/);
    }
  });
});
