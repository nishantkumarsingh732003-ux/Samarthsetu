"use client";

/**
 * The government-ID row on the profile: the masked reference, and the way to set it.
 *
 * It shows four digits or it shows nothing. There is no state in which this card can
 * display a full number, because no full number is ever stored — see `lib/govId.ts`.
 */

import { IdCard } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { GovIdDialog } from "@/components/account/GovIdDialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { maskedDisplay, onGovIdChanged, readGovId, type GovIdRef } from "@/lib/govId";

export function GovIdCard() {
  const t = useTranslations("govId");
  const [open, setOpen] = useState(false);
  const [record, setRecord] = useState<GovIdRef | null>(null);

  // Read in an effect and re-read on change: `localStorage` does not exist during the
  // server render, and the dialog writes to it while this card is mounted.
  useEffect(() => {
    const load = () => setRecord(readGovId());
    load();
    return onGovIdChanged(load);
  }, []);

  return (
    <>
      <Card interactive>
        <CardContent className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-prose">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal-700">
              <IdCard className="h-4 w-4" aria-hidden="true" />
              {t("eyebrow")}
            </p>
            <h2 className="mt-1.5 font-display text-lg font-bold">{t("cardTitle")}</h2>
            <p className="mt-1 text-ink-muted">{t("cardBody")}</p>

            {record ? (
              <p className="mt-3 flex flex-wrap items-center gap-2">
                <Chip tone="good">{t(`type.${record.idType}`)}</Chip>
                <span className="numeric font-semibold">
                  {maskedDisplay(record.last4, record.idType)}
                </span>
              </p>
            ) : (
              <Chip tone="warn" className="mt-3">
                {t("notSet")}
              </Chip>
            )}
          </div>

          <Button variant="secondary" onClick={() => setOpen(true)}>
            <IdCard className="h-4 w-4" aria-hidden="true" />
            {record ? t("change") : t("add")}
          </Button>
        </CardContent>
      </Card>

      <GovIdDialog open={open} onOpenChange={setOpen} />
    </>
  );
}
