/**
 * The fit score as a ring, the way the design drop drew it.
 *
 * Inline SVG rather than a charting library or an animated `<canvas>`: it is ~30 lines,
 * it costs no JavaScript at all, and it renders on the server — which matters because
 * this sits at the top of the matches page and is the first thing painted.
 *
 * Three things the ring is deliberately NOT allowed to imply:
 *
 *   - It is not the verdict. `fit.total` is the engine's *ranking* score, the answer to
 *     "why is this scheme above that one", and the verdict word sits beside it wherever
 *     this component is used.
 *   - It is not a probability of approval. Nothing in this product predicts what a
 *     Channel Partner will do.
 *   - It is not decorative. The number is announced to a screen reader through
 *     `role="img"` and an explicit label; the arc is `aria-hidden` because reading a
 *     circle to someone conveys nothing.
 */

// Palette values, not new colours: every stroke below is a token whose contrast against
// `surface` is already asserted by scripts/check-contrast.mjs. On the navy hero the arc
// becomes `good-bg`, which is what the dashboard hero already uses for this same number.
const BANDS = [
  { floor: 80, stroke: "#16803C" }, // good-fg
  { floor: 50, stroke: "#0B5D57" }, // teal-700
  { floor: 0, stroke: "#7A4E0A" }, // warn-fg
] as const;

export function ScoreRing({
  value,
  label,
  size = 128,
  onDark = false,
}: {
  /** 0–100. `fit.total` from the engine, already rounded by the caller. */
  value: number;
  /** What the number means, for a screen reader. Never rendered visually. */
  label: string;
  size?: number;
  /** On the navy hero the track has to be a white wash, not the page line colour. */
  onDark?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, value));
  // Geometry in a fixed 100-unit viewBox, so `size` only scales the rendered box and the
  // stroke never has to be recomputed.
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const stroke = BANDS.find((band) => pct >= band.floor)!.stroke;

  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className="shrink-0"
      role="img"
      aria-label={label}
    >
      <g aria-hidden="true">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          strokeWidth="8"
          stroke={onDark ? "rgba(255,255,255,0.18)" : "#E2E8F0"}
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          // `good-ring` on the navy hero — a mid green rather than the pale `good-bg`,
          // which washes out at this stroke width. Asserted against the panel's darkest
          // stop in scripts/check-contrast.mjs at the 3:1 floor for a non-text graphic.
          stroke={onDark ? "#34D399" : stroke}
          strokeDasharray={`${(pct / 100) * circumference} ${circumference}`}
          // Start the arc at twelve o'clock rather than three.
          transform="rotate(-90 50 50)"
        />
      </g>
      <text
        x="50"
        y="50"
        textAnchor="middle"
        dominantBaseline="central"
        className="font-display font-extrabold"
        fill={onDark ? "#FFFFFF" : "#172033"}
        fontSize="24"
      >
        {pct}%
      </text>
    </svg>
  );
}
