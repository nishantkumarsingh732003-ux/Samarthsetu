"use client";

/**
 * The primitive controls, hand-rolled.
 *
 * The design drop shipped 48 Radix-backed shadcn components. Installing them would have
 * added roughly 90KB gzipped for the handful actually used, against a 200KB budget for
 * the whole citizen route on a 2G connection. So the ones we need are written here in
 * about 200 lines, on native elements: a `<select>`, an `<input type="range">` and a
 * `<dialog>` are already accessible, already keyboard-navigable and already familiar to
 * a screen reader, and reimplementing them in divs is how that gets lost.
 *
 * Every control is at least 48px high (`min-h-touch`) and every one of them takes its
 * label as a prop rather than relying on a placeholder, because a placeholder disappears
 * the moment someone starts typing.
 */

import { useId } from "react";

type ButtonVariant = "primary" | "secondary" | "inverse" | "quiet";

const VARIANT: Record<ButtonVariant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  inverse: "btn-inverse",
  quiet: "btn-quiet",
};

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button type={type} className={`${VARIANT[variant]} ${className}`} {...props} />;
}

type Tone = "neutral" | "good" | "warn" | "stop" | "accent" | "teal" | "saffron";

const TONE: Record<Tone, string> = {
  neutral: "bg-canvas text-ink-muted",
  good: "bg-good-bg text-good-fg",
  warn: "bg-warn-bg text-warn-fg",
  stop: "bg-stop-bg text-stop-fg",
  accent: "bg-accent-50 text-accent-800",
  teal: "bg-teal-50 text-teal-700",
  saffron: "bg-saffron-bg text-saffron-fg",
};

export function Chip({
  tone = "neutral",
  className = "",
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  return <span className={`chip ${TONE[tone]} ${className}`}>{children}</span>;
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
  const id = useId();
  const hintId = `${id}-hint`;
  return (
    <div className={`space-y-1.5 ${className}`}>
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      {children({ id, describedBy: hint ? hintId : undefined })}
      {hint && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </div>
  );
}

export function TextInput({
  className = "",
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`input ${className}`} {...props} />;
}

export function TextArea({
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`input py-3 ${className}`} rows={3} {...props} />;
}

export function SelectInput({
  className = "",
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`input ${className}`} {...props}>
      {children}
    </select>
  );
}

/**
 * A slider paired with a number box, because they fail in opposite directions: a slider
 * cannot express "₹8,50,000 exactly" on a small screen, and a number box gives no sense
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
  const id = useId();
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
        <output className="numeric text-lg font-semibold text-accent-700" htmlFor={id}>
          {display}
        </output>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <input
          id={id}
          type="range"
          className="h-touch flex-1 accent-accent-700"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        <input
          type="number"
          aria-label={numberLabel}
          className="input numeric w-32 text-base"
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

/** A labelled progress bar. `<progress>` announces itself; a styled div does not. */
export function ProgressBar({
  value,
  label,
  tone = "accent",
}: {
  value: number;
  label: string;
  tone?: "accent" | "good" | "saffron";
}) {
  const bar = { accent: "bg-accent-700", good: "bg-good-fg", saffron: "bg-saffron" }[tone];
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-2 overflow-hidden rounded-full bg-line"
    >
      <div className={`h-full rounded-full ${bar}`} style={{ width: `${clamped}%` }} />
    </div>
  );
}
