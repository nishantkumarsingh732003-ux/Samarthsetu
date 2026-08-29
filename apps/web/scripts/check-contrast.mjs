/**
 * WCAG AA contrast check for the palette.
 *
 * CLAUDE.md requires WCAG AA. Lighthouse catches contrast failures only on colours that
 * happen to be on the page it audited, which means a palette value used on one rarely
 * visited screen can ship broken. This checks every foreground/background pair the
 * design system actually pairs, whether or not a page currently uses it.
 *
 *   node scripts/check-contrast.mjs
 */

// Mirrors tailwind.config.ts. Kept as literals so this script has no build dependency.
const COLOR = {
  canvas: "#F7F5F1",
  surface: "#FFFFFF",
  ink: "#1A1D21",
  "ink-muted": "#4A5159",
  "ink-faint": "#5E6672",
  line: "#DFDBD4",
  "accent-50": "#EDF3F8",
  "accent-600": "#12557F",
  "accent-700": "#0E4266",
  "accent-800": "#0A3350",
  "good-bg": "#E8F3EC",
  "good-fg": "#1B5E33",
  "warn-bg": "#FDF3E3",
  "warn-fg": "#7A4E0A",
  "stop-bg": "#FBECEA",
  "stop-fg": "#8A2318",
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
  ["white", "accent-700", 4.5, "primary button"],
  ["white", "accent-800", 4.5, "primary button, pressed"],
  ["accent-700", "surface", 4.5, "links"],
  ["accent-700", "canvas", 4.5, "links on the page ground"],
  ["accent-800", "accent-50", 4.5, "chips, callouts"],
  ["good-fg", "good-bg", 4.5, "eligible state"],
  ["good-fg", "surface", 4.5, "eligible label on a card"],
  ["warn-fg", "warn-bg", 4.5, "offline banner, warnings"],
  ["stop-fg", "stop-bg", 4.5, "errors"],
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
    0.0722 * (n & 255 ? channel(n & 255) : channel(0))
  );
}

function ratio(a, b) {
  const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
}

console.log("WCAG AA contrast — design system palette\n");

let failed = false;
for (const [fg, bg, min, usage] of PAIRS) {
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
console.log("Contrast check passed.");
