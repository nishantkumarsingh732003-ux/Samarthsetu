"use client";

/**
 * shadcn/ui Toaster, on sonner.
 *
 * Bottom right, dismissed by itself after four and a half seconds, with a close button so
 * it can be dismissed sooner. Sonner puts them in an `aria-live` region and gives the
 * stack a keyboard shortcut, which is the part that would have been got wrong by hand.
 *
 * Two settings that are deliberate rather than default:
 *
 *   - **`duration` is 4500ms, not sonner's 4000.** Every toast in this app has to be
 *     readable in six scripts, and a Tamil or Telugu line is physically longer than the
 *     English one for the same sentence.
 *   - **`closeButton` is on.** WCAG 2.2.1 wants content that disappears on a timer to be
 *     dismissible; a toast that can only be waited out is the failure mode.
 *
 * **Colour is set through sonner's own CSS variables, not through Tailwind classes.**
 * The first attempt passed `classNames.success = "bg-good-bg …"` and the toast rendered
 * white anyway: sonner injects its stylesheet into `<head>` at runtime, *after* the
 * Tailwind sheet, so its `[data-sonner-toast] { background: var(--normal-bg) }` beats a
 * utility class of equal specificity. `richColors` plus these variables sets the value
 * sonner itself reads, so there is nothing to out-specify.
 *
 * The values are this project's palette — the same green the verdict chips use — and every
 * foreground/background pair below is one `scripts/check-contrast.mjs` already asserts.
 * They are literals here for the same reason `scripts/check-contrast.mjs` holds literals:
 * this has to be a plain CSS value at runtime, and importing the Tailwind config into the
 * client bundle to avoid six hexes would cost far more than it saves.
 */

import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

/** Mirrors `theme.extend.colors` in tailwind.config.ts. Keep the two in step. */
const PALETTE = {
  "--normal-bg": "#FFFFFF", // surface
  "--normal-text": "#172033", // ink
  "--normal-border": "#E2E8F0", // line
  "--success-bg": "#DCFCE7", // good-bg
  "--success-text": "#16803C", // good-fg   — 4.72:1 on good-bg
  "--success-border": "#A7E5BC", // good-line
  "--error-bg": "#FEE2E2", // stop-bg
  "--error-text": "#B3261E", // stop-fg    — 5.35:1 on stop-bg
  "--error-border": "#F2C3BE", // stop-line
  "--warning-bg": "#FEF3C7", // warn-bg
  "--warning-text": "#7A4E0A", // warn-fg   — 7.06:1 on warn-bg
  "--warning-border": "#EFD9AE", // warn-line
  "--info-bg": "#EFF4FA", // accent-50
  "--info-text": "#112A4F", // accent-800 — 14.6:1 on accent-50
  "--info-border": "#D6E4EF", // accent-100
} as React.CSSProperties;

export function Toaster(props: ToasterProps) {
  return (
    <Sonner
      position="bottom-right"
      duration={4500}
      closeButton
      richColors
      // Sonner defaults to a stack that expands on hover; keeping it expanded means the
      // second toast is readable without a pointer, which a touchscreen has none of.
      expand
      style={PALETTE}
      toastOptions={{
        classNames: {
          toast: "rounded-card font-sans text-base shadow-lift",
          title: "font-medium",
          description: "text-sm opacity-80",
        },
      }}
      {...props}
    />
  );
}

export { toast } from "sonner";
