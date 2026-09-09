"use client";

/**
 * shadcn/ui Tabs on Radix, replacing the hand-rolled `TabLinks`/`TabPanel`.
 *
 * What the hand-rolled pair got wrong was not styling: it wired `role="tab"` onto plain
 * buttons, which means every tab is its own tab stop and none of the arrow-key movement a
 * screen-reader user expects from a tab strip is there. Radix implements the WAI-ARIA
 * pattern properly — roving tabindex, Home/End, automatic activation — and that is worth
 * more on this page than the two kilobytes it costs.
 *
 * The trigger keeps this project's own shape rather than shadcn's: a full-height pill in
 * a bordered rail, at least 48px tall (`min-h-touch`), navy when selected. Stock shadcn
 * ships a 36px trigger, which is not a thumb target on the phone this is built for.
 */

import * as TabsPrimitive from "@radix-ui/react-tabs";
import * as React from "react";

import { cn } from "@/lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "flex flex-wrap gap-1 rounded-card border border-line bg-surface p-1",
      className,
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      `min-h-touch grow rounded-card px-4 text-base font-medium text-ink-muted
       transition-colors hover:bg-accent-50 hover:text-accent-700
       data-[state=active]:bg-accent-700 data-[state=active]:text-white`,
      className,
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content ref={ref} className={cn("mt-4", className)} {...props} />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
