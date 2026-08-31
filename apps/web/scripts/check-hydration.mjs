/**
 * Catch values that differ between the server render and the client render.
 *
 * A `"use client"` component is still rendered on the server. A `useState` initialiser
 * therefore runs twice — once during SSR, once during hydration — and if it calls
 * `Math.random()` the two passes disagree and React throws:
 *
 *     Text content does not match server-rendered HTML.
 *     Server: "919876532191" Client: "919876560190"
 *
 * That is a real bug this project shipped in the WhatsApp simulator. It passed
 * TypeScript, ESLint, `next build` and every test, because it only existed in a browser.
 * So it needs its own check.
 *
 * The rule: nothing non-deterministic in a `useState` initialiser or interpolated
 * straight into JSX. Generate it in a `useEffect`, which runs on the client only.
 *
 *   node scripts/check-hydration.mjs
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(ROOT, "src");

// Anything whose value depends on *when* or *where* it ran.
const NON_DETERMINISTIC = [
  { pattern: /\bMath\.random\s*\(/, name: "Math.random()" },
  { pattern: /\bDate\.now\s*\(/, name: "Date.now()" },
  { pattern: /\bnew Date\s*\(\s*\)/, name: "new Date()" },
  { pattern: /\bcrypto\.randomUUID\s*\(/, name: "crypto.randomUUID()" },
  { pattern: /\bperformance\.now\s*\(/, name: "performance.now()" },
];

const ADVICE =
  "It runs during SSR and again on the client, and the two values differ. " +
  "Initialise to a stable placeholder and set it in a useEffect.";

let failures = 0;
const fail = (message) => {
  console.error(`  ✗ ${message}`);
  failures += 1;
};

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.tsx?$/.test(full)) out.push(full);
  }
  return out;
}

/** The argument list of a call whose `(` is at `open`, by counting parentheses. */
function callArguments(source, open) {
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === "(") depth += 1;
    else if (source[i] === ")") {
      depth -= 1;
      if (depth === 0) return source.slice(open + 1, i);
    }
  }
  return "";
}

const lineOf = (source, index) => source.slice(0, index).split("\n").length;

console.log("hydration check — non-deterministic values in a server-rendered path\n");

const files = walk(SRC);
let checked = 0;

for (const file of files) {
  const raw = readFileSync(file, "utf8");
  // Only client components are rendered twice. A server component runs once.
  if (!/^\s*["']use client["']/m.test(raw)) continue;
  checked += 1;

  // Comments explaining this very rule would otherwise trip it.
  const source = raw.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
  const where = relative(ROOT, file);

  // --- helpers in this file that are themselves non-deterministic ---------------
  // Without this, moving the randomness one call away hides it. `useState(newId())`
  // is exactly the shape the real bug took after a first pass at tidying it up.
  const tainted = new Map();
  const declarations = [
    /\bfunction\s+([A-Za-z_$][\w$]*)\s*\(/g,
    /\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*(?:\([^)]*\)|[\w$]+)\s*=>/g,
  ];
  for (const declaration of declarations) {
    for (const match of source.matchAll(declaration)) {
      const body = source.slice(match.index, match.index + 600);
      for (const { pattern, name } of NON_DETERMINISTIC) {
        if (pattern.test(body)) tainted.set(match[1], name);
      }
    }
  }

  // --- useState initialisers ------------------------------------------------------
  for (const match of source.matchAll(/\buseState\s*\(/g)) {
    const args = callArguments(source, match.index + match[0].length - 1);
    const line = lineOf(source, match.index);

    for (const { pattern, name } of NON_DETERMINISTIC) {
      if (pattern.test(args)) {
        fail(`${where}:${line} — ${name} in a useState initialiser. ${ADVICE}`);
      }
    }
    for (const [helper, name] of tainted) {
      if (new RegExp(`\\b${helper}\\s*\\(`).test(args)) {
        fail(`${where}:${line} — useState(${helper}()), and ${helper} uses ${name}. ${ADVICE}`);
      }
    }
  }

  // --- interpolated straight into JSX ------------------------------------------------
  // Anchored between `>` and `<` so an ordinary block — a function body, an if — is not
  // mistaken for JSX text. Telling the two apart properly needs a parser; this is the
  // same position test `check-i18n.mjs` uses.
  for (const match of source.matchAll(/>\s*\{([^{}]*)\}\s*</g)) {
    for (const { pattern, name } of NON_DETERMINISTIC) {
      if (pattern.test(match[1])) {
        fail(
          `${where}:${lineOf(source, match.index)} — ${name} interpolated into JSX. ` +
            "Server and client will render different text.",
        );
      }
    }
  }
}

console.log(`  scanned ${checked} client component(s) of ${files.length} files\n`);

if (failures > 0) {
  console.error(`hydration check FAILED with ${failures} problem(s).`);
  process.exit(1);
}
console.log("hydration check passed.");
