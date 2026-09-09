"use client";

/**
 * The document tiles, and the upload that makes them real.
 *
 * The design drop's version of this page was a five-tile vault whose button cycled a
 * label between "Not Uploaded", "Pending" and "Verified" in local state and touched
 * nothing. That is still not what this is. What changed is that the tiles now sit on top
 * of a real application: the checklist comes from the rule pack, the status comes from
 * `validation_status` on the stored document, and the button posts the file to the same
 * endpoint the tracking page uses.
 *
 * ON THE WORD "VERIFIED". It is not used here and must not be. What the API runs is an
 * automated check — it detects the document type and blacks out any ID number before
 * storing — and it reports `PENDING | PASSED | WARNING | FAILED`. Nobody has verified
 * that a caste certificate is genuine, and a green "Verified" badge against one is the
 * single worst thing this page could invent. "Checks passed" is what actually happened.
 *
 * Uploads attach to an application, not to an account, because that is what the API
 * models and what a partner receives. With no application yet the tiles still render —
 * the checklist is worth reading before you apply — and say so instead of offering a
 * button that would attach a file to nothing.
 */

import { FileText, ShieldAlert, Upload } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { useMyApplications } from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Link } from "@/i18n/navigation";
import {
  getApplication,
  uploadDocument,
  type ApplicationResponse,
  type RequiredDocument,
  type UploadedDocument,
} from "@/lib/api";

import type { Locale } from "@/i18n/config";

/** `validation_status` -> how the tile reads. Deliberately not "Verified": see above. */
const STATUS = {
  PASSED: { key: "statusPassed", tone: "good" },
  PENDING: { key: "statusPending", tone: "warn" },
  WARNING: { key: "statusWarning", tone: "warn" },
  FAILED: { key: "statusFailed", tone: "stop" },
} as const;

export function DocumentsClient({ locale }: { locale: Locale }) {
  const t = useTranslations("myDocuments");
  const tDocs = useTranslations("docs");
  const tCommon = useTranslations("common");

  const applications = useMyApplications();
  const [reference, setReference] = useState("");
  const [data, setData] = useState<ApplicationResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const inputs = useRef<Record<string, HTMLInputElement | null>>({});

  const rows = applications.data ?? [];
  const chosen = reference || rows[0]?.reference_no || "";

  const load = useCallback(async () => {
    if (!chosen) return;
    const result = await getApplication(chosen, locale);
    if (result.ok) setData(result.data);
  }, [chosen, locale]);

  useEffect(() => {
    void load();
  }, [load]);

  const onFile = useCallback(
    async (document: RequiredDocument, file: File) => {
      if (!chosen) return;
      setBusy(document.id);
      await uploadDocument(chosen, document.id, file, document.validity_months);
      setBusy(null);
      await load();
    },
    [chosen, load],
  );

  const uploadedFor = (id: string): UploadedDocument | undefined =>
    data?.documents.find((entry) => entry.doc_type === id);

  const required = data?.required_documents ?? [];

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      {rows.length > 1 && (
        <Card>
          <CardContent className="p-4 lg:p-5">
            <Select value={chosen} onValueChange={setReference}>
              <SelectTrigger aria-label={t("pickApplication")} className="max-w-md">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {rows.map((row) => (
                  <SelectItem key={row.reference_no} value={row.reference_no}>
                    {row.reference_no} · {row.scheme_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      )}

      {applications.loading && !applications.data ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : rows.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="mx-auto h-8 w-8 text-ink-faint" aria-hidden="true" />
            <h2 className="mt-3 font-display text-lg font-bold">{t("noApplication")}</h2>
            <p className="mx-auto mt-2 max-w-md text-ink-muted">{t("uploadNote")}</p>
            <Link href="/matches" className="btn-primary mt-5">
              {t("startFromMatches")}
            </Link>
          </CardContent>
        </Card>
      ) : !data ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : (
        <>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {required.map((document) => {
              const uploaded = uploadedFor(document.id);
              const state = uploaded ? STATUS[uploaded.validation_status] : null;
              const sending = busy === document.id;

              return (
                <li key={document.id}>
                  <Card interactive className="h-full">
                    <CardContent className="flex h-full flex-col p-5">
                      <span
                        aria-hidden="true"
                        className="grid h-11 w-11 place-items-center rounded-card bg-accent-50 text-accent-700"
                      >
                        <FileText className="h-5 w-5" />
                      </span>

                      <h2 className="mt-4 font-display text-lg font-bold">
                        {document.name}
                      </h2>

                      <div className="mt-2">
                        {state ? (
                          <Chip tone={state.tone}>{t(state.key)}</Chip>
                        ) : (
                          <Chip tone="neutral">{t("statusMissing")}</Chip>
                        )}
                      </div>

                      {/* The contents are never rendered. The file goes to the API, is
                          redacted there, and this page only ever learns its status. */}
                      <p className="mt-3 text-sm text-ink-faint">{t("notDisplayed")}</p>

                      {/* Whatever the automated check flagged, said plainly rather than
                          hidden behind a status word. */}
                      {uploaded && uploaded.warnings.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {uploaded.warnings.map((warning) => (
                            <li key={warning.code} className="text-sm text-warn-fg">
                              {warning.message}
                            </li>
                          ))}
                        </ul>
                      )}

                      {document.contains_government_id && (
                        <p className="mt-3 flex items-start gap-2 rounded-card bg-accent-50 px-3 py-2 text-sm text-accent-800">
                          <ShieldAlert
                            className="mt-0.5 h-4 w-4 shrink-0"
                            aria-hidden="true"
                          />
                          {t("masked")}
                        </p>
                      )}

                      <div className="mt-auto pt-4">
                        {/* A real file input, hidden behind the button, with `capture` so
                            a phone opens the camera rather than a file browser. */}
                        <input
                          ref={(element) => {
                            inputs.current[document.id] = element;
                          }}
                          type="file"
                          accept="image/*,application/pdf"
                          capture="environment"
                          className="sr-only"
                          onChange={(event) => {
                            const file = event.currentTarget.files?.[0];
                            if (file) void onFile(document, file);
                            event.currentTarget.value = "";
                          }}
                        />
                        <Button
                          variant="secondary"
                          disabled={sending}
                          onClick={() => inputs.current[document.id]?.click()}
                          className="w-full justify-center text-base"
                        >
                          <Upload className="h-4 w-4" aria-hidden="true" />
                          {sending
                            ? tDocs("uploading")
                            : uploaded
                              ? t("update")
                              : t("upload")}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </li>
              );
            })}
          </ul>

          <p className="text-sm text-ink-faint">{tDocs("privacyNote")}</p>
          <p className="text-sm text-ink-faint">{tDocs("checklistUnverified")}</p>
        </>
      )}
    </div>
  );
}
