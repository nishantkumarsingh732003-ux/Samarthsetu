/**
 * Citizen-route JS budget.
 *
 * CLAUDE.md: assume 2G and a Rs 6,000 phone, budget < 200KB JS on the citizen route.
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

const BUDGET_KB = 200; // gzipped

// Routes a citizen actually walks. /track is included; the map chunk is deliberately
// not, because it is dynamically imported and only downloaded if they open it.
const CITIZEN_ROUTES = [
  "/page",
  "/[locale]/page",
  "/[locale]/assist/page",
  "/[locale]/results/page",
  "/[locale]/results/[scheme]/partners/page",
  "/[locale]/track/[ref]/page",
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

console.log(`Citizen route JS budget — ${BUDGET_KB}KB gzipped per route\n`);

let worst = 0;
let failed = false;

for (const route of CITIZEN_ROUTES) {
  const bytes = bytesFor(route);
  if (bytes === null) {
    console.log(`  ?  ${route} — not in manifest (skipped)`);
    continue;
  }
  const kb = bytes / 1024;
  worst = Math.max(worst, kb);
  const over = kb > BUDGET_KB;
  if (over) failed = true;
  console.log(`  ${over ? "✗" : "✓"}  ${route.padEnd(42)} ${kb.toFixed(1)} KB`);
}

console.log(`\nWorst route: ${worst.toFixed(1)} KB of ${BUDGET_KB} KB.`);

if (failed) {
  console.error(
    "\nBundle check FAILED. Move something behind a dynamic import, or justify raising\n" +
      "the budget — but remember who is downloading it.",
  );
  process.exit(1);
}
console.log("Bundle check passed.");
