"use client";

/**
 * "Which Aadhaar did you register?" — answered with four digits and no more.
 *
 * WHY FOUR AND NOT TWELVE. A Channel Partner matching a file needs to recognise the
 * record, not to re-read the card; four digits do that. CLAUDE.md rule 4 names the last
 * four as the part that may be kept, and `redaction.py` exists to strip the rest at
 * ingestion on the server. The cheapest way to honour that rule is to never let the whole
 * number into the browser, so this field takes four digits and refuses more.
 *
 * A PASTE OF A FULL AADHAAR IS REFUSED, not trimmed. Trimming would be the worse
 * behaviour: it looks like it worked, and the citizen never learns that all twelve digits
 * were in the page. So the field turns red, says what happened, and the save button stays
 * disabled until the value is four digits.
 *
 * NOTHING IS SENT. The reference is kept on this device to pre-fill the application form.
 * The server's own masked record (`gov_id_last4` plus a salted `gov_id_hash`) is written
 * by the application route when an application is actually raised — that is the record of
 * consequence, and this is a convenience in front of it.
 *
 * Sibling of `DbtCheckDialog`, which asks for an IFSC and deliberately asks for no
 * Aadhaar at all. The difference is purpose: that dialog has no use for an id, and this
 * one does.
 */

import { IdCard, ShieldCheck, Trash2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

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
import {
  ID_TYPES,
  clearGovId,
  maskedDisplay,
  parseLast4,
  readGovId,
  writeGovId,
  type IdType,
} from "@/lib/govId";

export function GovIdDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("govId");
  const tCommon = useTranslations("common");

  const [idType, setIdType] = useState<IdType>("AADHAAR");
  const [typed, setTyped] = useState("");
  const [saved, setSaved] = useState<string | null>(null);

  // Load whatever is already stored each time the dialog opens, so re-opening shows the
  // current reference rather than a blank field that looks like nothing was saved.
  useEffect(() => {
    if (!open) return;
    const record = readGovId();
    setIdType(record?.idType ?? "AADHAAR");
    setTyped(record?.last4 ?? "");
    setSaved(record ? maskedDisplay(record.last4, record.idType) : null);
  }, [open]);

  const parsed = parseLast4(typed);
  // Nothing is wrong until they have typed something; an empty field is not an error.
  const problem = typed.trim() === "" ? null : parsed.problem;

  const hint =
    problem === "tooLong"
      ? t("errTooLong")
      : problem === "notDigits"
        ? t("errNotDigits")
        : problem === "tooShort"
          ? t("errTooShort")
          : t("hint");

  const save = () => {
    if (!parsed.ok || !parsed.value) return;
    if (writeGovId(idType, parsed.value)) {
      setSaved(maskedDisplay(parsed.value, idType));
      onOpenChange(false);
    }
  };

  const forget = () => {
    clearGovId();
    setSaved(null);
    setTyped("");
  };

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
          <Label htmlFor="gov-id-type">{t("typeLabel")}</Label>
          <select
            id="gov-id-type"
            value={idType}
            onChange={(event) => setIdType(event.currentTarget.value as IdType)}
            className="input"
          >
            {ID_TYPES.map((value) => (
              <option key={value} value={value}>
                {t(`type.${value}`)}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-4 space-y-1.5">
          <Label htmlFor="gov-id-last4">{t("last4Label")}</Label>
          <Input
            id="gov-id-last4"
            value={typed}
            onChange={(event) => setTyped(event.currentTarget.value)}
            placeholder="1234"
            // `inputMode` brings up the numeric keypad without `type="number"`, which
            // would strip leading zeros — and "0007" is a valid last four.
            inputMode="numeric"
            autoComplete="off"
            spellCheck={false}
            // Deliberately NOT maxLength={4}. A maxLength would silently swallow a pasted
            // twelve-digit Aadhaar down to four and look like it worked. The whole point
            // is that the citizen sees it refused.
            aria-invalid={problem !== null || undefined}
            aria-describedby="gov-id-hint"
            className={`numeric ${problem ? "border-stop-fg" : ""}`}
          />
          <p
            id="gov-id-hint"
            className={problem ? "text-sm text-stop-fg" : "field-hint"}
            role={problem ? "alert" : undefined}
          >
            {hint}
          </p>
        </div>

        {saved && (
          <p className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-card bg-good-bg px-4 py-3 text-good-fg">
            <span className="numeric font-semibold">{saved}</span>
            <button type="button" onClick={forget} className="inline-flex items-center gap-1.5 text-sm underline">
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              {t("forget")}
            </button>
          </p>
        )}

        {/* Said before the button, like the DBT dialog: what this is not. */}
        <p className="mt-4 rounded-card bg-accent-50 px-4 py-3 text-accent-800">
          {t("neverFull")}
        </p>

        <DialogFooter className="flex-col">
          <Button onClick={save} disabled={!parsed.ok} className="w-full">
            <IdCard className="h-4 w-4" aria-hidden="true" />
            {t("save")}
          </Button>
          <p className="w-full text-center text-sm text-ink-faint">{t("storedOnDevice")}</p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
