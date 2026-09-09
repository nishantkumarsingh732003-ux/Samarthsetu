"use client";

/**
 * The app-facing control layer, now backed by shadcn/ui.
 *
 * This file used to *be* the primitives — hand-rolled on native elements, because the
 * design drop's 48 Radix components would have cost ~90KB gzipped against a 200KB budget
 * for the whole citizen route on 2G. That trade was reversed deliberately: 4G is the
 * realistic floor now, only the handful of Radix primitives actually used are installed,
 * and the route still measures inside the budget (see scripts/check-bundle.mjs, which
 * fails the build if it stops doing so).
 *
 * What did NOT change is the shape of this module. `Button`, `Chip`, `Field`,
 * `TextInput`, `SelectInput`, `RangeField` and `ProgressBar` keep the props they had, so
 * the fourteen screens importing them were not touched. Underneath, each is now the
 * shadcn component in the same directory.
 *
 * Two decisions survive the move intact, because they are accessibility decisions rather
 * than styling ones:
 *
 *   - Every control is at least 48px high (`min-h-touch`). shadcn ships 40px; that is not
 *     a thumb target on a Rs 6,000 phone held one-handed outdoors.
 *   - Every control takes its label as a prop rather than relying on a placeholder, which
 *     disappears the moment someone starts typing.
 */

import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button as ShadcnButton, type ButtonProps } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export { ShadcnButton as Button };
export type { ButtonProps };

type Tone = "neutral" | "good" | "warn" | "stop" | "accent" | "teal" | "saffron";

/** A semantic pill. Thin wrapper on `Badge` so `tone` keeps reading the way it did. */
export function Chip({
  tone = "neutral",
  className = "",
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Badge tone={tone} className={className}>
      {children}
    </Badge>
  );
}

/** Label, control, and an optional hint that is wired to the control by `aria-describedby`
 *  rather than merely sitting near it. */
export function Field({
  label,
  hint,
  children,
  className = "",
}: {
  label: string;
  hint?: string;
  children: (ids: { id: string; describedBy?: string }) => React.ReactNode;
  className?: string;
}) {
  const id = React.useId();
  const hintId = `${id}-hint`;
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={id}>{label}</Label>
      {children({ id, describedBy: hint ? hintId : undefined })}
      {hint && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </div>
  );
}

export function TextInput(props: React.ComponentProps<typeof Input>) {
  return <Input {...props} />;
}

export function TextArea(props: React.ComponentProps<typeof Textarea>) {
  return <Textarea {...props} />;
}

/**
 * Still a native `<select>`, and deliberately so.
 *
 * shadcn's Select is in `components/ui/select.tsx` and is properly accessible, but on
 * Android a native select opens the platform's own wheel: one tap, reachable by switch
 * control, familiar to every screen reader, and free of JavaScript. For the long option
 * lists in the onboarding wizard — states, districts, sectors — that is still the better
 * control on the device this product is built for. Use the shadcn one where the design
 * calls for a styled trigger.
 */
export function SelectInput({
  className = "",
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn("input", className)} {...props}>
      {children}
    </select>
  );
}

/**
 * A slider paired with a number box, because they fail in opposite directions: a slider
 * cannot express "Rs 8,50,000 exactly" on a small screen, and a number box gives no sense
 * of the range. Both write the same value.
 */
export function RangeField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  display,
  numberLabel,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  /** The value as the citizen should read it — already formatted and localised. */
  display: string;
  /** Accessible name for the paired number box, which has no visible label of its own. */
  numberLabel: string;
}) {
  const id = React.useId();
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <Label htmlFor={id}>{label}</Label>
        <output className="numeric text-lg font-semibold text-accent-700" htmlFor={id}>
          {display}
        </output>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <Slider
          id={id}
          aria-label={label}
          className="flex-1"
          min={min}
          max={max}
          step={step}
          value={[value]}
          onValueChange={([next]) => onChange(next)}
        />
        <Input
          type="number"
          aria-label={numberLabel}
          className="numeric w-32 text-base"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(event) => onChange(Number(event.target.value) || 0)}
        />
      </div>
    </div>
  );
}

/** A labelled progress bar. Radix announces it; a styled div does not. */
export function ProgressBar({
  value,
  label,
  tone = "accent",
}: {
  value: number;
  label: string;
  tone?: "accent" | "good" | "saffron";
}) {
  return <Progress value={value} label={label} tone={tone} />;
}
