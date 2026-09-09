"use client";

/**
 * shadcn/ui Progress, on @radix-ui/react-progress.
 *
 * `label` is required rather than optional. A progress bar with no accessible name
 * announces "progress bar, 62 percent" and nothing about *what* is 62 percent, which on
 * a screen showing a fit score, a document count and an SLA clock is useless.
 */

import * as ProgressPrimitive from "@radix-ui/react-progress";
import * as React from "react";

import { cn } from "@/lib/utils";

const TONE = {
  accent: "bg-accent-700",
  good: "bg-good-fg",
  saffron: "bg-saffron",
  teal: "bg-teal-600",
} as const;

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  Omit<React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>, "value"> & {
    value: number;
    label: string;
    tone?: keyof typeof TONE;
  }
>(({ className, value, label, tone = "accent", ...props }, ref) => {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <ProgressPrimitive.Root
      ref={ref}
      value={clamped}
      aria-label={label}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-line", className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn("h-full w-full flex-1 rounded-full transition-transform", TONE[tone])}
        style={{ transform: `translateX(-${100 - clamped}%)` }}
      />
    </ProgressPrimitive.Root>
  );
});
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
