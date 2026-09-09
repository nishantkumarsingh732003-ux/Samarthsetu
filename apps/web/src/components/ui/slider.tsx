"use client";

/**
 * shadcn/ui Slider, on @radix-ui/react-slider.
 *
 * The thumb is 28px rather than shadcn's 20px, and the track sits inside a 48px-tall row,
 * so the whole control is a thumb target on a phone. Radix gives it arrow-key and
 * Page-Up/Down stepping, Home/End, and the right ARIA — which a styled `<input
 * type="range">` also gives, but this one can be dragged from anywhere on the track.
 */

import * as SliderPrimitive from "@radix-ui/react-slider";
import * as React from "react";

import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn("relative flex h-touch w-full touch-none select-none items-center", className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-line">
      <SliderPrimitive.Range className="absolute h-full bg-accent-700" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb
      className="block h-7 w-7 rounded-full border-2 border-accent-700 bg-surface shadow-card
                 transition-colors focus-visible:outline-none focus-visible:ring-4
                 focus-visible:ring-accent-600/40 focus-visible:ring-offset-2
                 focus-visible:ring-offset-canvas disabled:pointer-events-none disabled:opacity-50"
    />
  </SliderPrimitive.Root>
));
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };
