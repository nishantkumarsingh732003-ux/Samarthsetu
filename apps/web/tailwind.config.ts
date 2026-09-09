import type { Config } from "tailwindcss";

/**
 * Visual direction: calm, institutional, warm. Something a ministry would ship.
 *
 * The palette is the SamarthSetu brand direction — a deep government navy, a teal second
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
          // shadcn's flat `accent` / `accent-foreground`, added to the scale rather than
          // replacing it, so both `bg-accent-50` and `bg-accent` resolve.
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        // The shadcn contract, resolved from the CSS variables in globals.css. These are
        // aliases of the scale above — `primary` IS `accent-700` — and exist so that
        // stock shadcn source (`bg-primary`, `text-muted-foreground`, `border-input`)
        // compiles without being rewritten, and so `npx shadcn@latest add <name>` keeps
        // working. `accent.DEFAULT` and `accent.foreground` extend the accent scale
        // rather than replacing it: `bg-accent-50` and `bg-accent` both resolve.
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

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
        // The three faces the design drop asked for are loaded through `next/font/google`
        // and self-served from this origin (see src/styles/fonts.ts) — no third-party
        // connection, no render-blocking stylesheet. Each `--font-*` variable is first in
        // its stack and Noto Sans is directly behind it, which is what actually matters:
        // Inter, Plus Jakarta Sans and JetBrains Mono carry no Devanagari, Bengali, Tamil
        // or Telugu, so four of the six languages fall through to Noto by design.
        sans: [
          "var(--font-body)",
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
          "var(--font-display)",
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
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      fontSize: {
        // 16px base. That is the browser default and the accessible floor, not a step
        // below it — the previous 17px/19px ramp read as oversized at desk distance and
        // pushed every heading up with it. Everything above scales from here.
        //
        // What did NOT come down with it: `spacing.touch` below. Type can shrink; a 48px
        // tap target cannot, and the two are independent — a 16px label centred in a 48px
        // control is still a 48px control.
        base: ["1rem", { lineHeight: "1.6" }], // 16px
        lg: ["1.125rem", { lineHeight: "1.55" }], // 18px
        xl: ["1.25rem", { lineHeight: "1.4" }], // 20px
        "2xl": ["1.5rem", { lineHeight: "1.3" }], // 24px
        "3xl": ["1.875rem", { lineHeight: "1.2" }], // 30px
        "4xl": ["2.25rem", { lineHeight: "1.15" }], // 36px
      },
      spacing: {
        // Minimum comfortable touch target (WCAG 2.2 AA asks 24px; 48px is the
        // Android/iOS guidance and the right call for one-handed outdoor use).
        touch: "3rem",
      },
      maxWidth: {
        /**
         * Page widths, density-compensated.
         *
         * The root font size is 80% on a desktop pointer — see the `html` rule in
         * globals.css — which is what gives the app the density the design was drawn at.
         * Every `rem` length compacts with it, and for type, spacing and radii that is
         * exactly the point. For the **measure** it is not: a page container that shrinks
         * by a fifth leaves a fifth of a wide monitor empty and makes the content column
         * look stranded rather than compact.
         *
         * So the five container widths in the app are named here and divided by that
         * 0.8, which leaves the rendered width where it has always been on a desktop and
         * — because the same rule restores 100% on a phone — harmlessly wider than the
         * viewport on a small screen, where the container is capped by the screen anyway.
         *
         * Change the 80% and these four move with it. That is the whole reason they are
         * named rather than sprinkled as `max-w-6xl` across six files.
         */
        shell: "90rem", // the signed-in surface   (was max-w-6xl,  72rem)
        console: "80rem", // the two staff consoles  (was max-w-5xl,  64rem)
        form: "52.5rem", // the onboarding wizard   (was max-w-2xl,  42rem)
        column: "35rem", // the anonymous journey   (was max-w-md,   28rem)
        landing: "103.125rem", // the landing page   (was max-w-[1320px], 82.5rem)
      },
      borderRadius: {
        card: "0.75rem",
        panel: "1.125rem",
        // shadcn's three, derived from --radius so a component that says `rounded-md`
        // lands on the same corner as one that says `rounded-card`.
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        card: "0 1px 2px rgba(23,32,51,0.05), 0 1px 8px rgba(23,32,51,0.04)",
        lift: "0 12px 28px -12px rgba(23,59,108,0.18), 0 4px 8px rgba(23,32,51,0.04)",
      },
      keyframes: {
        rise: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        // Radix drives these through data-state on the popper content.
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        // Used once per screen at most, and switched off entirely under
        // prefers-reduced-motion by the global rule in globals.css.
        rise: "rise 0.45s cubic-bezier(0.22,1,0.36,1) both",
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  // Supplies the `animate-in` / `fade-in-0` / `zoom-in-95` utilities every shadcn
  // overlay uses for its enter and exit states. The base layer's prefers-reduced-motion
  // rule switches all of them off, so nothing here animates for someone who asked it not to.
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
