"use client";

/**
 * Set a scheme aside, or take it off the list again.
 *
 * The shadcn `Button` underneath, so this control inherits the 48px target, the focus
 * ring, the composited hover lift and the one-pixel press from the same place every
 * other button in the app gets them — rather than growing its own copy that drifts.
 *
 * A toggle button and not a checkbox: `aria-pressed` is what a screen reader announces
 * as "Save, not pressed" / "Save, pressed", which is the state a bookmark actually has.
 * The label changes with the state too, because a control whose only feedback is a
 * filled-in icon says nothing to someone who cannot see it and nothing to someone
 * reading it in high contrast.
 *
 * Nothing is saved to the server. See `lib/shortlist.ts` for why.
 */

import { Bookmark, BookmarkCheck } from "lucide-react";
import { useTranslations } from "next-intl";

import { useShortlist } from "@/components/account/useShortlist";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ShortlistButton({
  code,
  className = "",
  /** `icon` for a corner of a card, `full` where there is room for the word. */
  variant = "icon",
}: {
  code: string;
  className?: string;
  variant?: "icon" | "full";
}) {
  const t = useTranslations("shortlist");
  const { has, toggle, ready, isFull } = useShortlist();
  const saved = has(code);

  // Full, and this one is not on it: pressing would silently drop the oldest entry, so
  // say so instead of doing it.
  const blocked = !saved && isFull;

  const label = saved ? t("remove") : blocked ? t("full") : t("save");

  return (
    <Button
      variant="secondary"
      size={variant === "icon" ? "icon" : "default"}
      onClick={() => toggle(code)}
      disabled={!ready || blocked}
      aria-pressed={saved}
      aria-label={variant === "icon" ? label : undefined}
      title={variant === "icon" ? label : undefined}
      className={cn(
        "text-base",
        saved && "border-accent-700 bg-accent-50 text-accent-800 hover:border-accent-800",
        className,
      )}
    >
      {saved ? (
        <BookmarkCheck aria-hidden="true" />
      ) : (
        <Bookmark aria-hidden="true" />
      )}
      {variant === "full" && <span>{label}</span>}
    </Button>
  );
}
