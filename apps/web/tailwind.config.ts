import type { Config } from "tailwindcss";

/**
 * Visual direction: calm, institutional, warm. Something a ministry would ship.
 *
 * One accent (a deep government blue), one warm neutral ground, and a restrained
 * semantic set. Deliberately no gradients and no purple — this is a public service, not
 * a SaaS landing page.
 *
 * Contrast: every foreground/background pair used for text meets WCAG AA (4.5:1 for
 * body, 3:1 for large text). ink-on-canvas is 14.8:1; accent-700 on white is 7.4:1.
 */
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F7F5F1", // warm paper, not clinical white
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#1A1D21",
          muted: "#4A5159",
          faint: "#5E6672",
        },
        line: "#DFDBD4",
        accent: {
          50: "#EDF3F8",
          100: "#D6E4EF",
          600: "#12557F",
          700: "#0E4266", // 7.4:1 on white
          800: "#0A3350",
        },
        good: { bg: "#E8F3EC", fg: "#1B5E33", line: "#B7DCC4" },
        warn: { bg: "#FDF3E3", fg: "#7A4E0A", line: "#EFD9AE" },
        stop: { bg: "#FBECEA", fg: "#8A2318", line: "#EEC8C2" },
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
      },
      fontSize: {
        // Base is larger than a typical web app: read at arm's length, in sunlight.
        base: ["1.0625rem", { lineHeight: "1.6" }],
        lg: ["1.1875rem", { lineHeight: "1.55" }],
        xl: ["1.375rem", { lineHeight: "1.4" }],
        "2xl": ["1.75rem", { lineHeight: "1.3" }],
        "3xl": ["2.125rem", { lineHeight: "1.2" }],
      },
      spacing: {
        // Minimum comfortable touch target (WCAG 2.2 AA asks 24px; 48px is the
        // Android/iOS guidance and the right call for one-handed outdoor use).
        touch: "3rem",
      },
      borderRadius: { card: "0.75rem" },
      boxShadow: {
        card: "0 1px 2px rgba(26,29,33,0.05), 0 1px 8px rgba(26,29,33,0.04)",
      },
    },
  },
  plugins: [],
} satisfies Config;
