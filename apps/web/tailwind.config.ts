import type { Config } from "tailwindcss";

/**
 * Visual direction: calm, institutional, warm. Something a ministry would ship.
 *
 * The palette is the SETU brand direction — a deep government navy, a teal second
 * accent, saffron used only as a highlight, on a cool paper ground — with three colours
 * darkened from the design drop because they failed WCAG AA as drawn:
 *
 *   danger  #DC2626 → #B3261E   (4.02:1 on white, below the 4.5 body-text floor)
 *   warning #D97706 → #7A4E0A   (3.18:1; unreadable as text on white)
 *   muted   #667085 → #55617A   (4.29:1; the caption colour, used everywhere)
 *
 * Saffron is deliberately not a text colour at any weight. It is a 1.9:1 foreground on
 * white and there is no shade of it that is both saffron and legible, so it appears as a
 * background with ink on top, or as a 2px rule, and nowhere else.
 *
 * Every pair the system actually pairs is asserted by scripts/check-contrast.mjs, which
 * runs in `pnpm check`. Add a colour there when you add one here, or it ships unverified.
 *
 * One accent, one ground, a restrained semantic set. No purple, and gradients only on
 * the two dark display panels — this is a public service, not a SaaS landing page.
 */
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F7F9FC", // cool paper, not clinical white
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#172033",
          muted: "#414D63",
          faint: "#55617A",
        },
        line: "#E2E8F0",
        // The primary accent: NSFDC/ministry navy.
        accent: {
          50: "#EFF4FA",
          100: "#D6E4EF",
          600: "#1E4F8A",
          700: "#173B6C", // 11.18:1 on white
          800: "#112A4F",
        },
        // The second accent. Carries "explained", "verified", "routed" — the states that
        // are informational rather than a verdict, which is why it is not green.
        teal: {
          50: "#EAF6F4",
          600: "#0F766E",
          700: "#0B5D57",
        },
        // Highlight only. `saffron` is a background; `saffron-fg` is the text on it.
        saffron: {
          DEFAULT: "#F59E0B",
          bg: "#FFFBEB",
          fg: "#7C4A03",
          line: "#FCD34D",
        },
        good: { bg: "#DCFCE7", fg: "#16803C", line: "#A7E5BC" },
        warn: { bg: "#FEF3C7", fg: "#7A4E0A", line: "#EFD9AE" },
        stop: { bg: "#FEE2E2", fg: "#B3261E", line: "#F2C3BE" },
      },
      fontFamily: {
        // Noto Sans carries Devanagari, Bengali, Tamil and Telugu, so the six languages
        // share one typeface instead of falling back to whatever the phone has.
        sans: [
          "Noto Sans",
          "Noto Sans Devanagari",
          "Noto Sans Bengali",
          "Noto Sans Tamil",
          "Noto Sans Telugu",
          "system-ui",
          "sans-serif",
        ],
        // Headings. Falls back to the body stack, which matters: Plus Jakarta Sans has
        // no Devanagari or Tamil, so a Hindi heading must land on Noto rather than on
        // whatever the browser picks.
        display: [
          "Plus Jakarta Sans",
          "Noto Sans",
          "Noto Sans Devanagari",
          "Noto Sans Bengali",
          "Noto Sans Tamil",
          "Noto Sans Telugu",
          "system-ui",
          "sans-serif",
        ],
        // Amounts, rule ids and reference numbers — anything read out or compared
        // digit by digit.
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      fontSize: {
        // Base is larger than a typical web app: read at arm's length, in sunlight.
        base: ["1.0625rem", { lineHeight: "1.6" }],
        lg: ["1.1875rem", { lineHeight: "1.55" }],
        xl: ["1.375rem", { lineHeight: "1.4" }],
        "2xl": ["1.75rem", { lineHeight: "1.3" }],
        "3xl": ["2.125rem", { lineHeight: "1.2" }],
        "4xl": ["2.75rem", { lineHeight: "1.1" }],
      },
      spacing: {
        // Minimum comfortable touch target (WCAG 2.2 AA asks 24px; 48px is the
        // Android/iOS guidance and the right call for one-handed outdoor use).
        touch: "3rem",
      },
      borderRadius: { card: "0.75rem", panel: "1.125rem" },
      boxShadow: {
        card: "0 1px 2px rgba(23,32,51,0.05), 0 1px 8px rgba(23,32,51,0.04)",
        lift: "0 12px 28px -12px rgba(23,59,108,0.18), 0 4px 8px rgba(23,32,51,0.04)",
      },
      keyframes: {
        rise: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        // Used once per screen at most, and switched off entirely under
        // prefers-reduced-motion by the global rule in globals.css.
        rise: "rise 0.45s cubic-bezier(0.22,1,0.36,1) both",
      },
    },
  },
  plugins: [],
} satisfies Config;
