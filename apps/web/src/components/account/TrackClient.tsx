"use client";

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n/config";
import {
  getApplication,
  uploadDocument,
  type ApplicationResponse,
  type RequiredDocument,
} from "@/lib/api";
import { formatRupees } from "@/lib/format";

/**
 * The tracking screen, and the document upload that lives on it.
 *
 * Uploading here rather than during submission is deliberate. A citizen standing in a
 * queue with one bar of signal should already have their reference number; the photos
 * can follow whenever the connection allows. Making documents a precondition of
 * submitting would turn a bad connection into a lost application.
 *
 * Warnings never block. If we think the income certificate looks four years old we say
 * so and leave the button enabled — being wrong about a date must not stop someone
 * applying.
 */
const STAGES = [
  "SUBMITTED",
  "PARTNER_ACKNOWLEDGED",
  "DOCS_REQUESTED",
  "UNDER_APPRAISAL",
  "SANCTIONED",
  "DISBURSED",
] as const;

export function TrackClient({
  locale,
  reference,
}: {
  locale: Locale;
  reference: string;
}) {
  const t = useTranslations("track");
  const c = useTranslations("common");
  const d = useTranslations("docs");

  const [data, setData] = useState<ApplicationResponse | null>(null);
  const [error, setError] = useState<"notfound" | "other" | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [lastWarnings, setLastWarnings] = useState<Record<string, string[]>>({});
  const inputs = useRef<Record<string, HTMLInputElement | null>>({});

  const load = useCallback(async () => {
    const result = await getApplication(reference, locale);
    if (result.ok) {
      setData(result.data);
      setError(null);
    } else {
      setError(result.error === "notfound" ? "notfound" : "other");
    }
  }, [locale, reference]);

  useEffect(() => {
    void load();
  }, [load]);

  const onFile = useCallback(
    async (doc: RequiredDocument, file: File) => {
      setBusy(doc.id);
      const result = await uploadDocument(reference, doc.id, file, doc.validity_months);
      setBusy(null);

      if (!result.ok) {
        setLastWarnings((prev) => ({
          ...prev,
          [doc.id]: [result.error === "offline" ? c("offline") : c("error")],
        }));
        return;
      }
      setLastWarnings((prev) => ({
        ...prev,
        [doc.id]: result.data.document.warnings.map((warning) => warning.message),
      }));
      await load();
    },
    [c, load, reference],
  );

  if (error === "notfound") {
    return (
      <p role="alert" className="text-lg">
        {t("notFound")}
      </p>
    );
  }
  if (error) {
    return (
      <div className="panel p-5">
        <p role="alert" className="text-lg">
          {c("error")}
        </p>
        <button type="button" onClick={() => void load()} className="btn-primary mt-4 w-full">
          {c("retry")}
        </button>
      </div>
    );
  }
  if (!data) return <p className="text-lg">{c("loading")}</p>;

  const reached = new Set(data.timeline.map((entry) => entry.status));
  const outstanding = data.required_documents.filter((doc) => !doc.uploaded);

  return (
    <div className="space-y-6">
      <section className="panel p-4">
        <p className="text-base text-ink-muted">{t("reference")}</p>
        {/* Large and selectable: this gets read aloud down a phone line at a counter. */}
        <p className="mt-1 select-all font-mono font-display text-xl font-bold tracking-tight tracking-wide">
          {data.reference_no}
        </p>
        <p className="mt-3 text-lg">{data.scheme_name}</p>
        {data.partner ? (
          <p className="mt-1 text-base text-ink-muted">
            {data.partner.name}
            {data.partner.address ? `, ${data.partner.address}` : ""}
          </p>
        ) : null}
        {data.amount_requested ? (
          <p className="mt-1 text-base text-ink-muted">
            {c("rupees", { amount: formatRupees(data.amount_requested, locale) })}
          </p>
        ) : null}
      </section>

      <section aria-labelledby="timeline-heading">
        <h2 id="timeline-heading" className="mb-3 font-display text-lg font-bold">
          {t("heading")}
        </h2>
        <ol className="space-y-0">
          {STAGES.map((stage, index) => {
            const done = reached.has(stage);
            const current = data.status === stage;
            return (
              <li key={stage} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <span
                    aria-hidden="true"
                    className={`mt-1 h-4 w-4 shrink-0 rounded-full border-2 ${
                      done ? "border-accent-600 bg-accent-600" : "border-line bg-surface"
                    }`}
                  />
                  {index < STAGES.length - 1 ? (
                    <span
                      aria-hidden="true"
                      className={`w-0.5 flex-1 ${done ? "bg-accent-600" : "bg-line"}`}
                    />
                  ) : null}
                </div>
                <p
                  className={`pb-6 text-lg ${current ? "font-semibold" : ""} ${
                    done ? "" : "text-ink-faint"
                  }`}
                  aria-current={current ? "step" : undefined}
                >
                  {t(`status.${stage}` as "status.SUBMITTED")}
                </p>
              </li>
            );
          })}
        </ol>
      </section>

      <section aria-labelledby="docs-heading" className="panel p-4">
        <h2 id="docs-heading" className="font-display text-lg font-bold">
          {d("yourDocuments")}
        </h2>
        <p className="mt-1 text-base text-ink-muted">
          {outstanding.length === 0
            ? d("allUploaded")
            : d("outstanding", { count: outstanding.length })}
        </p>
        <p className="mt-2 text-sm text-ink-faint">{d("privacyNote")}</p>

        <ul className="mt-4 space-y-4">
          {data.required_documents.map((doc) => {
            const uploaded = data.documents.find((entry) => entry.doc_type === doc.id);
            const warnings = lastWarnings[doc.id] ?? uploaded?.warnings.map((w) => w.message) ?? [];
            return (
              <li key={doc.id} className="border-t border-line pt-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-medium">{doc.name}</p>
                    <p className="text-base text-ink-muted">{doc.why}</p>
                  </div>
                  {doc.uploaded ? (
                    <span className="shrink-0 rounded-full bg-accent-600 px-3 py-1 text-sm text-white">
                      {d("uploaded")}
                    </span>
                  ) : null}
                </div>

                {uploaded?.redaction_applied ? (
                  <p className="mt-2 text-sm text-accent-700">{d("idMaskedConfirmed")}</p>
                ) : null}

                {warnings.length > 0 ? (
                  <ul className="mt-2 space-y-1">
                    {warnings.map((message) => (
                      <li key={message} className="text-base text-warn-fg">
                        {message}
                      </li>
                    ))}
                  </ul>
                ) : null}

                <input
                  ref={(element) => {
                    inputs.current[doc.id] = element;
                  }}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,application/pdf"
                  capture="environment"
                  className="sr-only"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void onFile(doc, file);
                    event.target.value = "";
                  }}
                />
                <button
                  type="button"
                  onClick={() => inputs.current[doc.id]?.click()}
                  disabled={busy === doc.id}
                  className="btn-secondary mt-3 w-full disabled:opacity-50"
                >
                  {busy === doc.id
                    ? d("uploading")
                    : doc.uploaded
                      ? d("replacePhoto")
                      : d("takePhoto")}
                </button>
              </li>
            );
          })}
        </ul>

        {data.checklist_needs_verification ? (
          <p className="mt-4 text-sm text-ink-faint">{d("checklistUnverified")}</p>
        ) : null}
      </section>

      <p className="px-1 text-sm text-ink-faint">{t("indicativeOnly")}</p>
    </div>
  );
}
