/**
 * shadcn/ui Card, carrying this project's surface tokens rather than shadcn's defaults.
 *
 * Two differences from stock, both deliberate:
 *
 *   - The radius, border and shadow come from `.panel` in globals.css, so a Card and the
 *     hand-written panels that predate it are the same object. There is one surface in
 *     this app, not a shadcn one and a legacy one.
 *   - `interactive` adds the shared hover: `.lift` paints the shadow once into a
 *     pseudo-element and animates only its opacity, and the card itself moves on
 *     `transform`. Both are compositor properties, which is why a long list of these
 *     holds its frame rate — see scripts/measure-frames.mjs, which fails the build if a
 *     surface ever animates `box-shadow` directly.
 */

import { Slot } from "@radix-ui/react-slot";
import * as React from "react";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    interactive?: boolean;
    /** Render the card's styling onto the child element instead of a wrapper `div` —
     *  the standard shadcn escape hatch, used here so a result card can be a real
     *  `<article>` without nesting a redundant box inside it. */
    asChild?: boolean;
  }
>(({ className, interactive = false, asChild = false, ...props }, ref) => {
  const Component = asChild ? Slot : "div";
  return (
  <Component
    ref={ref}
    className={cn(
      "panel",
      interactive &&
        "lift transition-transform duration-200 ease-out hover:-translate-y-0.5",
      className,
    )}
    {...props}
  />
  );
});
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-1.5", className)} {...props} />
  ),
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-display text-lg font-bold tracking-tight", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn("text-ink-muted", className)} {...props} />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-5 lg:p-6", className)} {...props} />
  ),
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center gap-2", className)} {...props} />
  ),
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
