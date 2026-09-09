"use client";

/**
 * shadcn/ui Badge, carrying this project's semantic tones rather than shadcn's
 * default/secondary/destructive/outline four.
 *
 * The tones are the verdict language the whole app speaks: `good` is eligible, `stop` is
 * blocked, `warn` is a caution, `teal` is an explanation, `saffron` is a highlight. Every
 * pair here is asserted by scripts/check-contrast.mjs.
 */

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium transition-colors",
  {
    variants: {
      tone: {
        neutral: "bg-canvas text-ink-muted",
        good: "bg-good-bg text-good-fg",
        warn: "bg-warn-bg text-warn-fg",
        stop: "bg-stop-bg text-stop-fg",
        accent: "bg-accent-50 text-accent-800",
        teal: "bg-teal-50 text-teal-700",
        saffron: "bg-saffron-bg text-saffron-fg",
        outline: "border border-line text-ink-muted",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

export { Badge, badgeVariants };
