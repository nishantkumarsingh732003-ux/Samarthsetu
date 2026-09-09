"use client";

/**
 * shadcn/ui Accordion on Radix.
 *
 * Used for the document list and the FAQ on the scheme page, both of which are a row you
 * can open. `type="multiple"` where several can be open at once; the caller decides.
 *
 * This is the one place the project trades away a no-JavaScript fallback: `<details>`
 * works without it and this does not. That trade is fine *here* and nowhere else — the
 * scheme page is behind a login and behind two fetches, so it is not part of the core
 * flow CLAUDE.md rule 5 protects (`/`, `/assist`, `/results`, `/apply`, `/track`). Keep
 * `Disclosure` in ui/Panel.tsx for those.
 */

import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>
>(({ className, ...props }, ref) => (
  <AccordionPrimitive.Item ref={ref} className={cn("card", className)} {...props} />
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      ref={ref}
      className={cn(
        `group flex min-h-touch flex-1 items-center gap-3 px-4 text-left text-base
         font-medium transition-colors hover:text-accent-700`,
        className,
      )}
      {...props}
    >
      {children}
      <ChevronDown
        className="ml-auto h-4 w-4 shrink-0 text-ink-faint transition-transform duration-200 group-data-[state=open]:rotate-180"
        aria-hidden="true"
      />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className="overflow-hidden data-[state=closed]:animate-none"
    {...props}
  >
    <div className={cn("border-t border-line px-4 py-3", className)}>{children}</div>
  </AccordionPrimitive.Content>
));
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
