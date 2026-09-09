"use client";

/**
 * shadcn/ui ToggleGroup on Radix, for the scheme pills on /compare.
 *
 * A group of related toggles is one tab stop with arrow-key movement between the items,
 * not eight tab stops in a row. With six or more schemes to page through that is the
 * difference between a control someone can use from the keyboard and a control they have
 * to endure, and Radix implements it for free.
 *
 * The shape is this project's, not stock shadcn's: a 48px pill (`min-h-touch`), navy when
 * pressed, and a `disabled` state that still reads — a scheme locked out because three are
 * already chosen is greyed but not invisible, because "you have picked enough" and "this
 * one does not exist" must not look the same.
 */

import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import * as React from "react";

import { cn } from "@/lib/utils";

const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    className={cn("flex flex-wrap items-center gap-2", className)}
    {...props}
  />
));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(
      `inline-flex min-h-touch items-center gap-2 rounded-full border-2 border-line px-4
       text-base font-medium text-ink-muted transition-colors
       hover:border-accent-600 hover:text-accent-700
       focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-600/40
       disabled:pointer-events-none disabled:opacity-50
       data-[state=on]:border-accent-700 data-[state=on]:bg-accent-700 data-[state=on]:text-white`,
      className,
    )}
    {...props}
  />
));
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { ToggleGroup, ToggleGroupItem };
