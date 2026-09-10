"use client";

/**
 * The e-KYC row on the profile, and what it is careful not to claim.
 *
 * It reports one thing: whether a liveness capture was completed on this device, and
 * when. It does not report an identity as verified, because nothing in this product
 * verifies one — there is no UIDAI Aadhaar Face Auth integration behind it. The badge
 * therefore reads "capture complete", never "verified", and the caveat sits on the card
 * rather than only on the page behind it, so a citizen scanning their profile cannot come
 * away believing a government check has passed.
 *
 * Same posture as `DbtCheckDialog` one card above: explain, do not assert.
 */

import { ScanFace, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { onEkycChanged, readEkyc, type EkycRecord } from "@/lib/ekyc";

import type { Locale } from "@/i18n/config";

export function EkycCard({ locale }: { locale: Locale }) {
  const t = useTranslations("ekyc");
  const [record, setRecord] = useState<EkycRecord | null>(null);

  // Read in an effect and re-read on change: the capture page writes the record, and
  // coming back here with a stale "not done yet" would look like the capture was lost.
  useEffect(() => {
    const load = () => setRecord(readEkyc());
    load();
    return onEkycChanged(load);
  }, []);

  const readable = record
    ? new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
        dateStyle: "medium",
      }).format(new Date(record.capturedAt))
    : null;

  return (
    <Card interactive>
      <CardContent className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-prose">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal-700">
            <ScanFace className="h-4 w-4" aria-hidden="true" />
            {t("eyebrow")}
          </p>
          <h2 className="mt-1.5 font-display text-lg font-bold">{t("cardTitle")}</h2>
          <p className="mt-1 text-ink-muted">{t("cardBody")}</p>

          {record ? (
            <p className="mt-3 flex flex-wrap items-center gap-2">
              <Chip tone="good">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                {t("captureComplete")}
              </Chip>
              <span className="numeric text-sm text-ink-faint">
                {readable} · {record.reference}
              </span>
            </p>
          ) : (
            <Chip tone="warn" className="mt-3">
              {t("notDone")}
            </Chip>
          )}
        </div>

        <Button variant="secondary" asChild>
          <Link href="/ekyc">
            <ScanFace className="h-4 w-4" aria-hidden="true" />
            {record ? t("again") : t("start")}
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
