"use client";

/**
 * Overlays and disclosure, on native elements.
 *
 * `<dialog>` gives focus trapping, Escape-to-close, inert background and a screen-reader
 * announcement for free, in every browser this project targets. The design drop used a
 * Radix Dialog and a Radix Sheet for exactly this and paid ~30KB for it.
 *
 * The one thing `<dialog>` does not do is close on a backdrop click, so that is wired up
 * — carefully, by checking the click landed on the dialog element itself rather than on
 * its contents, because the backdrop is part of the dialog's own box.
 */

import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/controls";

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
  /** Accessible name for the ✕ button. Required — an icon alone announces nothing. */
  closeLabel: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Two whole class strings rather than one interpolated width: Tailwind's scanner reads
  // source text, so a `w-[min(92vw,${expr})]` template produces no CSS at all.
  const width = wide ? "w-[min(92vw,48rem)]" : "w-[min(92vw,34rem)]";

  return (
    <dialog
      ref={ref}
      // Escape and the close button both route through the same handler, so the parent's
      // state cannot drift out of step with the element's own open/closed state.
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        // The backdrop is the dialog's own box; a click on a child has a different
        // target. Without this check, every click inside would close the modal.
        if (event.target === ref.current) onClose();
      }}
      className={`${width} rounded-panel border border-line bg-surface p-0 text-ink
                  shadow-lift backdrop:bg-ink/40`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
        <h2 className="text-xl font-semibold">{title}</h2>
        <Button
          variant="quiet"
          onClick={onClose}
          aria-label={closeLabel}
          className="min-h-0 shrink-0 px-2 py-1 text-2xl leading-none"
        >
          <span aria-hidden="true">✕</span>
        </Button>
      </div>
      <div className="max-h-[70vh] overflow-y-auto px-5 py-5">{children}</div>
    </dialog>
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

/**
 * A tab strip that is really a set of links, so each panel has a URL.
 *
 * Deep-linking matters here: a partner officer telling a citizen "look at the documents
 * tab" needs that to be a thing they can send. Client-side tab state cannot be shared.
 */
export function TabLinks({
  tabs,
  current,
  onSelect,
  label,
}: {
  tabs: { id: string; label: string }[];
  current: string;
  onSelect: (id: string) => void;
  label: string;
}) {
  return (
    <div role="tablist" aria-label={label} className="flex flex-wrap gap-1 rounded-card border border-line bg-surface p-1">
      {tabs.map((tab) => {
        const active = tab.id === current;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={active}
            aria-controls={`panel-${tab.id}`}
            onClick={() => onSelect(tab.id)}
            className={`min-h-touch grow rounded-card px-4 text-base font-medium transition-colors ${
              active
                ? "bg-accent-700 text-white"
                : "text-ink-muted hover:bg-accent-50 hover:text-accent-700"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({
  id,
  current,
  children,
}: {
  id: string;
  current: string;
  children: React.ReactNode;
}) {
  if (id !== current) return null;
  return (
    <div role="tabpanel" id={`panel-${id}`} aria-labelledby={`tab-${id}`} tabIndex={0} className="mt-4">
      {children}
    </div>
  );
}
