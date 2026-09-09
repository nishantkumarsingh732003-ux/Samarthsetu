"use client";

/**
 * Overlays and disclosure.
 *
 * `Modal` keeps the props it always had — `open`, `onClose`, `title`, `closeLabel`,
 * `wide` — so the screens that use it did not change. Underneath it is now the shadcn
 * Dialog on Radix, which replaces a native `<dialog>` plus a hand-wired backdrop click.
 *
 * What that buys, over and above what `<dialog>` already gave us for free: the overlay
 * animates in and out instead of appearing, the backdrop click needs no "did this land on
 * the dialog's own box?" check, and scroll is locked on the body rather than only inside
 * the panel — which on a phone is the difference between a modal and a modal you can
 * scroll the page behind.
 *
 * `Disclosure` below is still `<details>`, and deliberately: it works with JavaScript
 * switched off, which is the state the core flow has to survive in. Where that does not
 * apply — the scheme page, behind a login and two fetches — use the shadcn Accordion.
 *
 * `TabLinks`/`TabPanel` used to live here too. They wired `role="tab"` onto plain buttons,
 * which makes every tab its own tab stop and gives a screen-reader user none of the
 * arrow-key movement the pattern promises. Their one consumer now uses `ui/tabs.tsx`,
 * which is Radix and implements WAI-ARIA properly, so they are gone rather than left
 * around as a second way to do the same thing.
 */

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function Modal({
  open,
  onClose,
  title,
  closeLabel,
  wide = false,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  /** Accessible name for the close button. Required — an icon alone announces nothing. */
  closeLabel: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Dialog open={open} onOpenChange={(next) => (next ? undefined : onClose())}>
      <DialogContent closeLabel={closeLabel} wide={wide} className="p-0">
        <DialogHeader className="mb-0 border-b border-line px-5 py-4">
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-5">{children}</div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Progressive disclosure for the long tail — a rule expression, a provenance block, the
 * exact profile the engine was given. `<details>` works with JavaScript switched off,
 * which is the state the core flow has to survive in.
 */
export function Disclosure({
  summary,
  children,
  className = "",
}: {
  summary: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <details className={`group ${className}`}>
      <summary
        className="flex min-h-touch cursor-pointer list-none items-center gap-2 rounded-card
                   px-1 text-base font-medium text-accent-700 hover:underline"
      >
        <span
          aria-hidden="true"
          className="inline-block transition-transform group-open:rotate-90"
        >
          ▸
        </span>
        {summary}
      </summary>
      <div className="pl-5 pt-2">{children}</div>
    </details>
  );
}
