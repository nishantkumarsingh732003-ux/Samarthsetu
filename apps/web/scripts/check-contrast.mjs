/**
 * WCAG AA contrast check for the palette.
 *
 * CLAUDE.md requires WCAG AA. Lighthouse catches contrast failures only on colours that
 * happen to be on the page it audited, which means a palette value used on one rarely
 * visited screen can ship broken. This checks every foreground/background pair the
 * design system actually pairs, whether or not a page currently uses it.
 *
 * It has already earned its keep: the SETU design drop specified #DC2626 for errors
 * (4.02:1 on white), #D97706 for warnings (3.18:1) and #667085 for captions (4.29:1).
 * All three read fine on a designer's monitor and none of them passes. They are darkened
 * in tailwind.config.ts, and this is what would catch a future revert.
 *
 *   node scripts/check-contrast.mjs
 */

// Mirrors tailwind.config.ts. Kept as literals so this script has no build dependency.
const COLOR = {
  canvas: "#F7F9FC",
  surface: "#FFFFFF",
  ink: "#172033",
  "ink-muted": "#414D63",
  "ink-faint": "#55617A",
  line: "#E2E8F0",
  "accent-50": "#EFF4FA",
  "accent-100": "#D6E4EF",
  "accent-600": "#1E4F8A",
  "accent-700": "#173B6C",
  "accent-800": "#112A4F",
  "teal-50": "#EAF6F4",
  "teal-600": "#0F766E",
  "teal-700": "#0B5D57",
  saffron: "#F59E0B",
  "saffron-bg": "#FFFBEB",
  "saffron-fg": "#7C4A03",
  "good-bg": "#DCFCE7",
  "good-fg": "#16803C",
  "warn-bg": "#FEF3C7",
  "warn-fg": "#7A4E0A",
  "stop-bg": "#FEE2E2",
  "stop-fg": "#B3261E",
  white: "#FFFFFF",
};

// [foreground, background, minimum ratio, where it is used]
// 4.5 for body text, 3.0 for large text (>=18.66px bold or >=24px).
const PAIRS = [
  ["ink", "canvas", 4.5, "body text"],
  ["ink", "surface", 4.5, "card text"],
  ["ink-muted", "canvas", 4.5, "secondary text"],
  ["ink-muted", "surface", 4.5, "secondary text on cards"],
  ["ink-faint", "canvas", 4.5, "labels, captions"],
  ["ink-faint", "surface", 4.5, "labels on cards"],
  ["white", "accent-600", 4.5, "secondary button"],
  ["white", "accent-700", 4.5, "primary button"],
  ["white", "accent-800", 4.5, "primary button, pressed"],
  ["accent-700", "surface", 4.5, "links"],
  ["accent-700", "canvas", 4.5, "links on the page ground"],
  ["accent-800", "accent-50", 4.5, "chips, callouts"],
  ["accent-800", "accent-100", 4.5, "active nav item"],
  ["white", "teal-600", 4.5, "second accent on a filled control"],
  ["white", "teal-700", 4.5, "second accent, pressed"],
  ["teal-700", "surface", 4.5, "explanation headings"],
  ["teal-700", "teal-50", 4.5, "explanation callouts"],
  ["saffron-fg", "saffron-bg", 4.5, "highlight chips"],
  // Saffron itself is only ever a background. There is no shade of it that is both
  // saffron and legible as text, so this is the only pair it appears in.
  ["ink", "saffron", 4.5, "text on a saffron highlight"],
  ["good-fg", "good-bg", 4.5, "eligible state"],
  ["good-fg", "surface", 4.5, "eligible label on a card"],
  ["warn-fg", "warn-bg", 4.5, "offline banner, warnings"],
  ["warn-fg", "surface", 4.5, "warning text on a card"],
  ["stop-fg", "stop-bg", 4.5, "errors"],
  ["stop-fg", "surface", 4.5, "blocked reasons on a card"],
];

function channel(value) {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex) {
  const n = parseInt(hex.slice(1), 16);
  return (
    0.2126 * channel((n >> 16) & 255) +
    0.7152 * channel((n >> 8) & 255) +
    0.0722 * channel(n & 255)
  );
}

function ratio(a, b) {
  const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
}

console.log("WCAG AA contrast — design system palette\n");

let failed = false;
for (const [fg, bg, min, usage] of PAIRS) {
  if (!(fg in COLOR) || !(bg in COLOR)) {
    console.error(`  ✗  unknown colour in pair ${fg}/${bg}`);
    failed = true;
    continue;
  }
  const value = ratio(COLOR[fg], COLOR[bg]);
  const ok = value >= min;
  if (!ok) failed = true;
  console.log(
    `  ${ok ? "✓" : "✗"}  ${`${fg} on ${bg}`.padEnd(28)} ${value.toFixed(2)}:1` +
      ` (min ${min})  ${usage}`,
  );
}

console.log("");
if (failed) {
  console.error("Contrast check FAILED. Darken the foreground or lighten the background.");
  process.exit(1);
}
console.log(`Contrast check passed — ${PAIRS.length} pairs.`);
