"use client";

/**
 * shadcn/ui Sheet — a Dialog that arrives from the edge instead of the middle.
 *
 * Same Radix primitive as `ui/dialog.tsx`, so the focus trap, Escape handling, inert
 * background and backdrop click are all the ones already reviewed there. The difference
 * is where it sits and how it moves, and that difference earns its keep: the eligibility
 * explanation is read *against* the card that opened it, and a centred modal covers the
 * card while a side panel leaves it visible.
 *
 * On a phone it is not a side panel at all — it is full width and comes up from nowhere
 * useful, so `side="right"` still spans the viewport below `sm`. A 24rem drawer on a
 * 360px screen is a modal with a sliver of wasted gutter.
 */

import * as SheetPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const Sheet = SheetPrimitive.Root;
const SheetTrigger = SheetPrimitive.Trigger;
const SheetClose = SheetPrimitive.Close;
const SheetPortal = SheetPrimitive.Portal;

const SheetOverlay = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-[#0B1729]/60 backdrop-blur-sm",
      "data-[state=open]:animate-in data-[state=closed]:animate-out",
      "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
  />
));
SheetOverlay.displayName = SheetPrimitive.Overlay.displayName;

const SheetContent = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Content> & {
    /** Accessible name for the ✕ button. Required — an icon alone announces nothing. */
    closeLabel: string;
  }
>(({ className, children, closeLabel, ...props }, ref) => (
  <SheetPortal>
    <SheetOverlay />
    <SheetPrimitive.Content
      ref={ref}
      className={cn(
        "fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l border-line bg-surface",
        "shadow-lift sm:max-w-[34rem]",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right",
        "data-[state=closed]:duration-200 data-[state=open]:duration-300",
        className,
      )}
      {...props}
    >
      {children}
      <SheetPrimitive.Close
        className="absolute right-4 top-4 grid h-touch w-touch place-items-center rounded-full
                   text-ink-faint transition-colors hover:bg-accent-50 hover:text-accent-700
                   focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-600/40"
      >
        <span className="sr-only">{closeLabel}</span>
        <X className="h-5 w-5" aria-hidden="true" />
      </SheetPrimitive.Close>
    </SheetPrimitive.Content>
  </SheetPortal>
));
SheetContent.displayName = SheetPrimitive.Content.displayName;

function SheetHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("shrink-0 border-b border-line px-5 py-5 pr-16 lg:px-6", className)}
      {...props}
    />
  );
}

/** The scrolling middle. Header and footer stay put; only this moves. */
function SheetBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("min-h-0 flex-1 overflow-y-auto px-5 py-5 lg:px-6", className)}
      {...props}
    />
  );
}

function SheetFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "shrink-0 border-t border-line px-5 py-4 lg:px-6",
        "flex flex-col gap-2.5 sm:flex-row",
        className,
      )}
      {...props}
    />
  );
}

const SheetTitle = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Title>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Title
    ref={ref}
    className={cn("font-display text-2xl font-extrabold tracking-tight", className)}
    {...props}
  />
));
SheetTitle.displayName = SheetPrimitive.Title.displayName;

const SheetDescription = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Description>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Description
    ref={ref}
    className={cn("text-ink-muted", className)}
    {...props}
  />
));
SheetDescription.displayName = SheetPrimitive.Description.displayName;

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetBody,
  SheetFooter,
  SheetTitle,
  SheetDescription,
};
