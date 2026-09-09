"use client";

/**
 * shadcn/ui Button, with this project's sizes.
 *
 * Two deliberate departures from the stock recipe, both of them accessibility decisions
 * that predate shadcn here and are not shadcn's to overrule:
 *
 *   - `default` is `min-h-touch` (48px), not `h-10` (40px). 48px is the Android and iOS
 *     guidance and the right call for one-handed outdoor use on a cheap phone.
 *   - Type is `text-lg`, not `text-sm`. The whole scale in tailwind.config.ts is a step
 *     up from a typical web app because this is read at arm's length, in sunlight.
 *
 * Hover feedback comes from the `.lift` class in globals.css and not from a
 * `hover:shadow-*` utility. The shadow is painted once into a pseudo-element and only
 * its opacity animates, so the hover state is composited rather than repainted — see the
 * comment on `.lift` for the measurement behind that. `transition-colors` is widened to
 * include `transform` for the one-pixel press, which is also composited.
 *
 * The variant names map onto the `.btn-*` classes the app already used, so the fourteen
 * call sites through components/ui/controls.tsx did not have to change.
 */

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "lift inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-card font-medium " +
    "transition-[color,background-color,border-color,transform] duration-200 ease-out " +
    "active:translate-y-px focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-600/40 " +
    "focus-visible:ring-offset-2 focus-visible:ring-offset-canvas disabled:pointer-events-none " +
    "disabled:opacity-50 disabled:after:opacity-0 [&_svg]:pointer-events-none [&_svg]:size-5 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-accent-700 text-white hover:bg-accent-800 active:bg-accent-800",
        secondary: "border-2 border-line bg-surface text-ink hover:border-accent-600",
        /** Inside a dark panel, where the surface button would vanish. */
        inverse: "bg-white text-accent-700 hover:bg-accent-50",
        quiet: "text-ink-muted hover:bg-accent-50 hover:text-accent-700 after:hidden",
        outline: "border-2 border-accent-700 bg-transparent text-accent-700 hover:bg-accent-50",
        ghost: "hover:bg-accent-50 hover:text-accent-700 after:hidden",
        destructive: "bg-stop-fg text-white hover:brightness-110",
        link: "text-accent-700 underline-offset-4 hover:underline after:hidden active:translate-y-0",
      },
      size: {
        default: "min-h-touch px-5 text-base",
        sm: "min-h-touch px-3 text-base",
        lg: "min-h-touch px-8 text-lg",
        /** A square target for an icon with no visible label. Still 48px. */
        icon: "h-touch w-touch p-0",
      },
      /** The landing page's pill buttons. */
      shape: { default: "", pill: "rounded-full" },
    },
    defaultVariants: { variant: "primary", size: "default", shape: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Render the child element instead of a `<button>` — used to style a `<Link>`. */
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, shape, asChild = false, type, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        // A button inside a form defaults to `submit`, which has surprised someone on
        // every project. Only set it when we are actually rendering a button.
        type={asChild ? undefined : (type ?? "button")}
        className={cn(buttonVariants({ variant, size, shape }), className)}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
