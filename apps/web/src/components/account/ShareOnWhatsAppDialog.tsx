"use client";

/**
 * Hand the application summary to WhatsApp.
 *
 * Real, and cheap: `wa.me/<number>?text=<encoded>` is WhatsApp's own click-to-chat link.
 * No Business API, no template approval, no server — the citizen's installed WhatsApp
 * opens with the message already typed, and they choose who receives it. On the phone
 * this product is built for, that is the sharing mechanism people actually use.
 *
 * The number is optional on purpose. Leaving it blank opens WhatsApp's own contact
 * picker, which is what someone standing at a counter wants: they are handing the phone
 * to the officer in front of them, not typing that officer's number.
 *
 * WHAT THE MESSAGE MAY CONTAIN. WhatsApp is an external service and this text leaves the
 * app the moment the citizen taps through, so the summary carries what a partner needs at
 * a counter and nothing more: name, category, enterprise, location, the figures, and the
 * scheme. No Aadhaar, no bank details, no document images — CLAUDE.md rule 4 is about
 * what gets stored, and this is the same question asked about what gets sent. The
 * textarea is editable, so the citizen can cut anything else before it goes.
 */

import { Check, Copy, MessageCircle } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";

export function ShareOnWhatsAppDialog({
  open,
  onOpenChange,
  summary,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The prefilled text. Editable — the citizen owns what they send. */
  summary: string;
}) {
  const t = useTranslations("shareWhatsApp");
  const tCommon = useTranslations("common");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState(summary);
  const [copied, setCopied] = useState(false);

  // Keep only digits, then drop a leading 91 or 0 the citizen may have typed on top of
  // the fixed +91 prefix. `wa.me` wants the number in full international form.
  const digits = phone.replace(/\D/g, "").replace(/^(91|0)/, "").slice(0, 10);
  const href = `https://wa.me/${digits ? `91${digits}` : ""}?text=${encodeURIComponent(
    message,
  )}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard is blocked in some embedded browsers. The textarea is selectable, so
      // the citizen can still copy by hand; a thrown error here would close nothing.
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent closeLabel={tCommon("close")}>
        <DialogHeader>
          <Chip tone="good" className="w-fit">
            <MessageCircle className="h-3.5 w-3.5" aria-hidden="true" />
            {t("chip")}
          </Chip>
          <DialogTitle className="mt-2.5">{t("title")}</DialogTitle>
          <DialogDescription>{t("body")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-1.5">
          <Label htmlFor="wa-phone">{t("phoneLabel")}</Label>
          <div className="flex items-stretch gap-2">
            <span className="numeric grid min-h-touch place-items-center rounded-card border-2 border-line px-3 text-ink-muted">
              +91
            </span>
            <Input
              id="wa-phone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel-national"
              placeholder="9876543210"
              value={phone}
              onChange={(event) => setPhone(event.currentTarget.value)}
              className="numeric flex-1"
            />
          </div>
          <p className="field-hint">{t("phoneHint")}</p>
        </div>

        <div className="mt-4 space-y-1.5">
          <div className="flex items-center justify-between gap-3">
            <Label htmlFor="wa-message">{t("messageLabel")}</Label>
            <Button
              variant="quiet"
              onClick={copy}
              className="min-h-0 px-2 py-1 text-sm"
            >
              {copied ? (
                <Check className="h-4 w-4" aria-hidden="true" />
              ) : (
                <Copy className="h-4 w-4" aria-hidden="true" />
              )}
              {copied ? t("copied") : t("copy")}
            </Button>
          </div>
          <Textarea
            id="wa-message"
            rows={8}
            value={message}
            onChange={(event) => setMessage(event.currentTarget.value)}
            className="numeric text-base"
          />
        </div>

        <DialogFooter className="flex-col">
          <Button asChild className="w-full bg-[#128C7E] text-white hover:brightness-110">
            <a href={href} target="_blank" rel="noreferrer noopener">
              <MessageCircle className="h-4 w-4" aria-hidden="true" />
              {t("open")}
            </a>
          </Button>
          {/* WhatsApp's click-to-chat link carries text only — it cannot attach a file.
              Saying so here is cheaper than a citizen wondering where the PDF went. */}
          <p className="w-full text-center text-sm text-ink-faint">{t("attachHint")}</p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
