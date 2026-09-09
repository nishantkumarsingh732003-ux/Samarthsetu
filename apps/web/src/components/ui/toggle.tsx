"use client";

/**
 * shadcn/ui Toggle on Radix — a single control that is either on or off.
 *
 * The difference from a `<button>` that flips a boolean is `aria-pressed`, which Radix
 * maintains and which is the only thing that tells a screen reader "high contrast, toggle
 * button, not pressed" instead of "high contrast, button". For a control whose entire job
 * is to report its own state to someone who may not be able to see it, that is the
 * feature, not a detail.
 *
 * The shape is this project's rather than stock shadcn's: a 48px target (`min-h-touch`),
 * navy when pressed, and a visible border in both states — an off toggle drawn as bare
 * text is a toggle nobody finds.
 */

import * as TogglePrimitive from "@radix-ui/react-toggle";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const toggleVariants = cva(
  `inline-flex min-h-touch items-center justify-center gap-2 rounded-card border-2
   border-line px-4 text-base font-medium text-ink-muted transition-colors
   hover:border-accent-600 hover:text-accent-700
   focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-600/40
   disabled:pointer-events-none disabled:opacity-50
   data-[state=on]:border-accent-700 data-[state=on]:bg-accent-700 data-[state=on]:text-white`,
  {
    variants: {
      size: {
        default: "",
        /** Square, for an icon with no label beside it. */
        icon: "w-touch px-0",
      },
    },
    defaultVariants: { size: "default" },
  },
);

const Toggle = React.forwardRef<
  React.ElementRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> &
    VariantProps<typeof toggleVariants>
>(({ className, size, ...props }, ref) => (
  <TogglePrimitive.Root
    ref={ref}
    className={cn(toggleVariants({ size }), className)}
    {...props}
  />
));
Toggle.displayName = TogglePrimitive.Root.displayName;

export { Toggle, toggleVariants };
