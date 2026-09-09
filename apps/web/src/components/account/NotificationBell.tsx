"use client";

/**
 * What this service has told the citizen, and when.
 *
 * The rows come from `GET /citizen/notifications`, which reads the `notifications` table
 * — the same rows the partner console reads, minus the masked digits an officer needs
 * and a citizen does not. Every entry is a message that was actually sent, stored
 * rendered in the language it went out in. **Nothing here is composed on read.** A bell
 * that invents "your documents are due" from the state of a row would be a notification
 * the citizen was never sent, on a page carrying a ministry's name.
 *
 * That also means an empty bell is a true statement and is shown as one: "nothing yet"
 * rather than a fabricated welcome message.
 *
 * Built on the shadcn Popover (Radix underneath), for the same reason the language
 * switcher is built on the shadcn DropdownMenu: the behaviour a hand-rolled popup gets
 * wrong comes for free. Escape and outside-click to close, focus returned to the trigger
 * on close, `aria-expanded` and `aria-controls` wired up, a focus trap that does not trap
 * too hard, and collision-aware placement so the panel never opens off the bottom of a
 * short screen. The first draft of this file re-implemented three of those on `document`
 * listeners and got the fourth wrong.
 *
 * **The dot is device-local.** There is no read receipt in the schema and adding one
 * would mean writing a row every time someone glances at a bell. Instead the timestamp
 * of the newest message seen is kept in `localStorage`, the same place and for the same
 * reason as the shortlist: it is a convenience, not a record, and it must not widen the
 * DPDP surface. Signing in on a second device shows the dot again, which is the correct
 * failure — a message you have not seen *on this device* is one you may not have seen.
 */

import {
  BadgeIndianRupee,
  Bell,
  CheckCircle2,
  CircleAlert,
  Clock,
  FileText,
  Inbox,
  MessageSquare,
  Send,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useMyNotifications } from "@/components/account/useCitizenData";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";

import type { CitizenNotification } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

const SEEN_KEY = "setu.notifications.seen.v1";

function readSeen(): string {
  try {
    return window.localStorage.getItem(SEEN_KEY) ?? "";
  } catch {
    return "";
  }
}

function writeSeen(stamp: string): void {
  try {
    window.localStorage.setItem(SEEN_KEY, stamp);
  } catch {
    // Blocked site data: the dot comes back on the next load. Harmless.
  }
}

/**
 * The event name picks the icon.
 *
 * These are the seven events in `apps/api/app/templates/notifications.yaml`, and they are
 * named for the *status* the application moved to rather than with a common prefix —
 * `UNDER_APPRAISAL`, not `APPLICATION_UNDER_APPRAISAL`. An earlier prefix match on
 * `APPLICATION_*` therefore caught exactly one of them and dropped the other six onto the
 * generic speech bubble.
 *
 * An event with no entry here still renders, with the neutral icon. A template can be
 * added on the API side without this file being touched, and the worst outcome is a plain
 * icon rather than a missing row.
 */
const EVENT_ICON: Record<string, typeof MessageSquare> = {
  APPLICATION_SUBMITTED: Send,
  PARTNER_ACKNOWLEDGED: CheckCircle2,
  DOCS_REQUESTED: FileText,
  UNDER_APPRAISAL: Clock,
  SANCTIONED: CheckCircle2,
  DISBURSED: BadgeIndianRupee,
  REJECTED: CircleAlert,
};

const iconFor = (event: string) => EVENT_ICON[event] ?? MessageSquare;

export function NotificationBell({ locale }: { locale: Locale }) {
  const t = useTranslations("notifications");
  const tCommon = useTranslations("common");
  const { data, loading, error } = useMyNotifications();

  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState("");

  // In an effect, not a `useState` initialiser: this component is rendered on the
  // server too, where there is no localStorage, and the two passes must agree.
  useEffect(() => setSeen(readSeen()), []);

  const rows = data ?? [];
  // The API orders newest first, so the head is the watermark.
  const newest = rows[0]?.created_at ?? "";
  const unread = rows.filter((row) => row.created_at > seen).length;

  function onOpenChange(next: boolean) {
    setOpen(next);
    if (next && newest) {
      writeSeen(newest);
      setSeen(newest);
    }
  }

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger
        aria-label={unread > 0 ? t("labelUnread", { count: unread }) : t("label")}
        className="relative grid h-12 w-12 place-items-center rounded-full text-ink-muted
                   transition-[color,background-color,transform] duration-200 ease-out
                   hover:bg-accent-50 hover:text-accent-700 active:translate-y-px
                   focus-visible:outline-none focus-visible:ring-4
                   focus-visible:ring-accent-600/40 focus-visible:ring-offset-2
                   focus-visible:ring-offset-surface data-[state=open]:bg-accent-50
                   data-[state=open]:text-accent-700"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        {unread > 0 && (
          <span
            aria-hidden="true"
            className="absolute right-2.5 top-2.5 h-2.5 w-2.5 rounded-full bg-saffron
                       ring-2 ring-surface"
          />
        )}
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-panel border-line
                   bg-surface p-0 shadow-lift"
      >
        <div className="flex items-center justify-between gap-3 px-4 py-3">
          <h2 className="font-display text-base font-bold">{t("title")}</h2>
          {rows.length > 0 && (
            <span className="numeric text-sm text-ink-faint">
              {t("count", { count: rows.length })}
            </span>
          )}
        </div>
        <Separator className="bg-line" />

        <ul className="max-h-[26rem] divide-y divide-line overflow-y-auto">
          {loading && rows.length === 0 && (
            <li role="status" className="px-4 py-6 text-center text-ink-faint">
              {tCommon("loading")}
            </li>
          )}

          {!loading && error && rows.length === 0 && (
            <li className="px-4 py-6 text-center text-ink-faint">
              {error === "offline" ? tCommon("offline") : tCommon("error")}
            </li>
          )}

          {!loading && !error && rows.length === 0 && (
            <li className="px-4 py-8 text-center">
              <Inbox className="mx-auto h-8 w-8 text-ink-faint" aria-hidden="true" />
              <p className="mt-2 font-medium">{t("emptyTitle")}</p>
              <p className="mt-1 text-sm text-ink-faint">{t("emptyBody")}</p>
            </li>
          )}

          {rows.map((row) => (
            <NotificationRow key={row.id} row={row} locale={locale} />
          ))}
        </ul>

        <Separator className="bg-line" />
        <p className="bg-canvas px-4 py-2.5 text-sm text-ink-faint">{t("footnote")}</p>
      </PopoverContent>
    </Popover>
  );
}

function NotificationRow({
  row,
  locale,
}: {
  row: CitizenNotification;
  locale: Locale;
}) {
  const Icon = iconFor(row.event);
  // `sent_at` is null while queued or after a failed send. Falling back to `created_at`
  // shows when the message was raised rather than showing nothing.
  const stamp = row.sent_at ?? row.created_at;

  return (
    <li className="flex gap-3 px-4 py-3">
      <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-card bg-accent-50 text-accent-700">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </span>
      <div className="min-w-0">
        {/* The body is the record. It was rendered in the citizen's language at send
            time, so it carries its own `lang` rather than inheriting the page's — a
            message sent in Hindi to someone now reading in English is still Hindi.

            The timestamp below is formatted in the *reader's* timezone, which differs
            from the server's. That would be a hydration mismatch anywhere else; it is
            safe here because Radix renders the panel into a portal only once it is
            open, and it starts closed on both passes. Do not lift this row out. */}
        <p lang={row.language} className="text-ink">
          {row.body}
        </p>
        <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-ink-faint">
          <time dateTime={stamp} className="numeric">
            {new Intl.DateTimeFormat(locale, {
              dateStyle: "medium",
              timeStyle: "short",
            }).format(new Date(stamp))}
          </time>
          {row.application_reference && (
            <span className="numeric">· {row.application_reference}</span>
          )}
        </p>
      </div>
    </li>
  );
}
