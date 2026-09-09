"use client";

/**
 * shadcn/ui Input. Still a native `<input>` — shadcn's is too, which is the point.
 *
 * 48px tall and `text-lg`, for the same reasons as Button. The 2px border is this
 * project's, not shadcn's 1px: at arm's length in sunlight a hairline border on a white
 * field is not a visible edge.
 */

import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex min-h-touch w-full rounded-card border-2 border-line bg-surface px-4 text-base text-ink",
        "file:border-0 file:bg-transparent file:text-base file:font-medium",
        "placeholder:text-ink-faint focus:border-accent-600 focus-visible:outline-none",
        "focus-visible:ring-4 focus-visible:ring-accent-600/40 focus-visible:ring-offset-2",
        "focus-visible:ring-offset-canvas disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
