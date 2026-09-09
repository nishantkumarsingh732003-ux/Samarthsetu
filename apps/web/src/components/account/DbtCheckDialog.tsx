"use client";

/**
 * "Is your bank account Aadhaar-DBT linked?" — the question, answered honestly.
 *
 * WHAT THIS DOES NOT DO. It does not check. There is no NPCI mapper integration behind
 * this product and no way to look up whether a given account is seeded, so a dialog that
 * returned "Linked ✓" would be inventing a government record. That is not a demo
 * shortcut: a citizen told their account is DBT-linked when it is not will have a subsidy
 * silently fail to arrive, and will find out months later. The design drop's version
 * takes an Aadhaar number and returns a status; this one takes no Aadhaar at all and
 * sends the citizen to the official checker.
 *
 * WHAT IT DOES DO, and it is worth something:
 *
 *   - Explains what DBT seeding is and why it decides whether money reaches them, which
 *     is the part nobody at a counter explains.
 *   - Reads the bank off the IFSC. The first four characters of an IFSC are the bank's
 *     own code — SBIN, PUNB, HDFC — so naming the bank back to the citizen is a real
 *     check done entirely on the device, and a typo shows up immediately.
 *   - Hands them the official NPCI status page, which is the only thing that can actually
 *     answer the question.
 *
 * No Aadhaar field. CLAUDE.md rule 4 permits storing last four digits *when they are
 * needed*; these are not needed for anything here, and asking for an identifier you have
 * no use for is the data-minimisation failure the rule exists to prevent.
 */

import { ExternalLink, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/controls";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/** The official checker. NPCI publishes Aadhaar seeding status here and nowhere this app
 *  can reach programmatically. */
const NPCI_STATUS = "https://www.npci.org.in/what-we-do/nach/dbt";

/**
 * IFSC: four letters of bank code, a zero, then six of branch. Validated on the device —
 * this confirms the citizen typed a well-formed code, and nothing more. It does not and
 * cannot confirm the branch exists.
 */
const IFSC = /^([A-Z]{4})0[A-Z0-9]{6}$/;

export function DbtCheckDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("dbtCheck");
  const tCommon = useTranslations("common");
  const [ifsc, setIfsc] = useState("");

  const typed = ifsc.trim().toUpperCase();
  const match = IFSC.exec(typed);
  const bankCode = match?.[1] ?? null;
  const malformed = typed.length >= 11 && !match;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent closeLabel={tCommon("close")}>
        <DialogHeader>
          <Chip tone="good" className="w-fit">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            {t("chip")}
          </Chip>
          <DialogTitle className="mt-2.5">{t("title")}</DialogTitle>
          <DialogDescription>{t("body")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-1.5">
          <Label htmlFor="dbt-ifsc">{t("ifscLabel")}</Label>
          <Input
            id="dbt-ifsc"
            value={ifsc}
            onChange={(event) => setIfsc(event.currentTarget.value)}
            placeholder="SBIN0001234"
            autoComplete="off"
            spellCheck={false}
            maxLength={11}
            aria-invalid={malformed || undefined}
            aria-describedby="dbt-ifsc-hint"
            className="numeric uppercase"
          />
          <p id="dbt-ifsc-hint" className="field-hint">
            {bankCode
              ? t("ifscBank", { code: bankCode })
              : malformed
                ? t("ifscMalformed")
                : t("ifscHint")}
          </p>
        </div>

        {/* The honest part, said before the button rather than after it. */}
        <p className="mt-4 rounded-card bg-accent-50 px-4 py-3 text-accent-800">
          {t("cannotCheck")}
        </p>

        <DialogFooter className="flex-col">
          <Button asChild className="w-full">
            <a href={NPCI_STATUS} target="_blank" rel="noreferrer noopener">
              {t("openOfficial")}
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
            </a>
          </Button>
          <p className="w-full text-center text-sm text-ink-faint">{t("noAadhaar")}</p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
