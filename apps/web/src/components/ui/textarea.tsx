"use client";

/** shadcn/ui Textarea, matching Input's border weight and type size. */

import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<"textarea">>(
  ({ className, rows = 3, ...props }, ref) => (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(
        "flex min-h-touch w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-base",
        "text-ink placeholder:text-ink-faint focus:border-accent-600 focus-visible:outline-none",
        "focus-visible:ring-4 focus-visible:ring-accent-600/40 focus-visible:ring-offset-2",
        "focus-visible:ring-offset-canvas disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export { Textarea };
