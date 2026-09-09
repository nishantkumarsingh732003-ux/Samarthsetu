/**
 * Citizen-route JS budget.
 *
 * CLAUDE.md rule 5: budget < 300KB JS on the citizen route.
 * A budget nobody measures is a wish, so this reads the real build output and fails the
 * build when First Load JS crosses the line.
 *
 * Measured GZIPPED, because that is what actually travels over the citizen's connection
 * and what Next reports as "First Load JS". Measuring raw bytes overstates it by ~3x and
 * would have this failing a build that is comfortably inside budget.
 *
 * Run after `next build`:
 *   node scripts/check-bundle.mjs
 */
import { readFileSync, existsSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = join(ROOT, ".next", "app-build-manifest.json");

/**
 * Raised from 200KB to 300KB, deliberately and with a reason — the thing the note at the
 * foot of this file asks for rather than deleting the line.
 *
 * The original figure came from "assume 2G and a Rs 6,000 phone". That assumption was
 * revisited: 4G reaches the great majority of India now, including the citizens this
 * service is for, and the anonymous journey was being held to a ceiling that cost it the
 * product's own design — no header, no brand, no shared chrome on the four screens where
 * a citizen actually decides something.
 *
 * 300KB, not "no budget". A ceiling that is never enforced is the same as no ceiling, and
 * the point of this file is that a chart library or a component kit cannot be added later
 * without someone seeing the cost. What changed is the number, not the discipline.
 */
const BUDGET_KB = 300; // gzipped

// What a signed-out visitor downloads: the landing page and the sign-in form. The
// Leaflet chunk is deliberately absent everywhere below because it is dynamically
// imported and only fetched if someone opens the map.
const CITIZEN_ROUTES = [
  // "/page" is absent on purpose: "/" is a middleware redirect into a locale now, not a
  // rendered page, so it has no entry in the manifest and nothing to weigh.
  //
  // This list used to be the whole anonymous journey — /assist, /results, /apply, /track.
  // That journey has been removed: it duplicated the signed-in surface screen for screen,
  // and everything now begins at sign-in. What a signed-out visitor can still download is
  // the landing page and the sign-in form, so that is what this measures. The screens
  // that survived the removal (/apply/[scheme] and the per-scheme partner list) kept
  // their URLs but moved into the account group, and are weighed below with the rest.
  "/[locale]/page",
  "/[locale]/signin/page",
];

// The signed-in surface, which is now the whole product past sign-in, so it is held to
// the same ceiling rather than treated as a place the budget stops applying.
// Holding it here is what stops a chart library or a component kit being added later
// without anyone noticing the cost. If a route genuinely needs to exceed this, raise it
// deliberately with a reason rather than by deleting the line.
// Manifest keys, not URLs: `(account)` is a route group, so it appears here and never
// in an address bar.
const ACCOUNT_ROUTES = [
  "/[locale]/(account)/dashboard/page",
  "/[locale]/(account)/onboarding/page",
  "/[locale]/(account)/matches/page",
  "/[locale]/(account)/schemes/page",
  "/[locale]/(account)/schemes/[code]/page",
  "/[locale]/(account)/shortlist/page",
  "/[locale]/(account)/compare/page",
  "/[locale]/(account)/calculator/page",
  "/[locale]/(account)/partners/page",
  "/[locale]/(account)/applications/page",
  "/[locale]/(account)/documents/page",
  "/[locale]/(account)/profile/page",
  // Kept their URLs when the anonymous journey was removed; gated by the group now.
  "/[locale]/(account)/apply/[scheme]/page",
  "/[locale]/(account)/results/[scheme]/partners/page",
];

if (!existsSync(MANIFEST)) {
  console.error("No build manifest found. Run `next build` first.");
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));

function bytesFor(route) {
  const files = manifest.pages[route];
  if (!files) return null;
  let total = 0;
  for (const file of new Set(files)) {
    if (!file.endsWith(".js")) continue;
    const full = join(ROOT, ".next", file);
    if (existsSync(full)) total += gzipSync(readFileSync(full)).length;
  }
  return total;
}

console.log(`Route JS budget — ${BUDGET_KB}KB gzipped per route\n`);

let worst = 0;
let failed = false;

function measure(heading, routes) {
  console.log(heading);
  for (const route of routes) {
    const bytes = bytesFor(route);
    if (bytes === null) {
      // Not a skip. A renamed route that nobody updated here is a budget that stopped
      // being enforced, which is exactly how a route quietly grows past the ceiling.
      console.log(`  ✗  ${route} — not in the build manifest`);
      failed = true;
      continue;
    }
    const kb = bytes / 1024;
    worst = Math.max(worst, kb);
    const over = kb > BUDGET_KB;
    if (over) failed = true;
    console.log(`  ${over ? "✗" : "✓"}  ${route.padEnd(42)} ${kb.toFixed(1)} KB`);
  }
  console.log("");
}

measure("signed out — everything before an account exists", CITIZEN_ROUTES);
measure("optional account surface", ACCOUNT_ROUTES);

console.log(`\nWorst route: ${worst.toFixed(1)} KB of ${BUDGET_KB} KB.`);

if (failed) {
  console.error(
    "\nBundle check FAILED. Move something behind a dynamic import, or justify raising\n" +
      "the budget — but remember who is downloading it.",
  );
  process.exit(1);
}
console.log("Bundle check passed.");
