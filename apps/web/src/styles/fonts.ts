/**
 * The three typefaces the design drop asked for, self-hosted.
 *
 * The drop pulled them from `fonts.googleapis.com` with an `@import`, which costs a DNS
 * lookup, a TLS handshake and a render-blocking stylesheet to a third party before the
 * first word appears. `next/font/google` fetches the same files at build time and serves
 * them from this origin: same typefaces, one hop instead of three, no third-party
 * connection from a citizen's phone, and `size-adjust` fallback metrics computed for each
 * so the swap does not shift the layout.
 *
 * Variable fonts, so each family is one file covering every weight rather than four or
 * five static cuts. Latin subset only — Devanagari, Bengali, Tamil and Telugu are not in
 * any of these three faces, and the stacks in tailwind.config.ts fall through to Noto
 * Sans for those scripts, which is where they were already going.
 *
 * `display: "swap"`: text is readable in the fallback face from the first paint, then
 * re-renders. On a slow connection a citizen reads the page rather than a blank space.
 */
import { Inter, JetBrains_Mono, Plus_Jakarta_Sans } from "next/font/google";

/** Headings. */
export const display = Plus_Jakarta_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
});

/** Body. */
export const body = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-body",
});

/** Amounts, rule ids and reference numbers — anything read out or compared digit by digit. */
export const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

/** Put on `<html>` so the variables are in scope for the whole document. */
export const fontVariables = `${display.variable} ${body.variable} ${mono.variable}`;
