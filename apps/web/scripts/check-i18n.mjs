/**
 * Translation completeness and hardcoded-string check.
 *
 * CLAUDE.md forbids hardcoded English strings in the citizen route. This is the CI-style
 * script that enforces it, plus key parity across all six catalogues — a missing key
 * does not crash next-intl, it silently renders the key name to a citizen, which is far
 * worse than a build failure.
 *
 *   node scripts/check-i18n.mjs
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MESSAGES = join(ROOT, "messages");
const SRC = join(ROOT, "src");

const LOCALES = ["en", "hi", "mr", "bn", "ta", "te"];
const REVIEWED = new Set(["en", "hi"]);

let failures = 0;
const fail = (message) => {
  console.error(`  ✗ ${message}`);
  failures += 1;
};

// --- 1. key parity ------------------------------------------------------------------

function flatten(object, prefix = "") {
  const keys = new Set();
  for (const [key, value] of Object.entries(object)) {
    if (key === "_meta") continue;
    if (value && typeof value === "object") {
      for (const nested of flatten(value, `${prefix}${key}.`)) keys.add(nested);
    } else {
      keys.add(`${prefix}${key}`);
    }
  }
  return keys;
}

const catalogues = Object.fromEntries(
  LOCALES.map((locale) => [
    locale,
    JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), "utf8")),
  ]),
);

const reference = flatten(catalogues.en);
console.log(`i18n check — ${reference.size} keys in en.json\n`);

console.log("1. key parity");
for (const locale of LOCALES) {
  const keys = flatten(catalogues[locale]);
  const missing = [...reference].filter((key) => !keys.has(key));
  const extra = [...keys].filter((key) => !reference.has(key));
  if (missing.length) fail(`${locale}: missing ${missing.length} key(s): ${missing.slice(0, 5)}`);
  if (extra.length) fail(`${locale}: ${extra.length} key(s) not in en: ${extra.slice(0, 5)}`);
  if (!missing.length && !extra.length) console.log(`  ✓ ${locale}`);
}

// --- 2. review status is declared ---------------------------------------------------

console.log("\n2. review status declared");
for (const locale of LOCALES) {
  const status = catalogues[locale]._meta?.status;
  if (!status) {
    fail(`${locale}: no _meta.status — every catalogue must say whether it was reviewed`);
    continue;
  }
  const expected = REVIEWED.has(locale) ? "verified" : "draft";
  if (status !== expected) {
    fail(`${locale}: _meta.status is "${status}", expected "${expected}"`);
  } else {
    console.log(`  ✓ ${locale}: ${status}`);
  }
}

// --- 3. no hardcoded user-facing strings --------------------------------------------

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.tsx?$/.test(full)) out.push(full);
  }
  return out;
}

// Files exempt from the string check, with a reason each.
const EXEMPT = new Set([
  // The language picker runs before a locale exists, so its few strings are the
  // language names themselves plus a bilingual heading.
  join(SRC, "app", "page.tsx"),
  // Locale metadata is data, not copy.
  join(SRC, "i18n", "config.ts"),
]);

// A JSX text node of two or more Latin words is almost certainly copy that should have
// come from a catalogue.
const JSX_TEXT = />\s*([A-Z][A-Za-z]+(?:\s+[a-zA-Z][A-Za-z']*){1,})\s*</g;

console.log("\n3. no hardcoded copy in components");
let offenders = 0;
for (const file of walk(SRC)) {
  if (EXEMPT.has(file)) continue;
  const source = readFileSync(file, "utf8");
  const stripped = source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "");
  for (const match of stripped.matchAll(JSX_TEXT)) {
    fail(`${relative(ROOT, file)}: hardcoded text "${match[1].trim()}" — use a message key`);
    offenders += 1;
  }
}
if (offenders === 0) console.log("  ✓ none found");

// --- result --------------------------------------------------------------------------

console.log("");
if (failures > 0) {
  console.error(`i18n check FAILED with ${failures} problem(s).`);
  process.exit(1);
}
console.log("i18n check passed.");
