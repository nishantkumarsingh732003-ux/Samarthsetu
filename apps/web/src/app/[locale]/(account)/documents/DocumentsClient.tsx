"use client";

/**
 * What to bring, per scheme, and why each thing is asked for.
 *
 * The design drop had a five-tile document vault with an upload button that cycled a
 * status label between "Not Uploaded", "Pending" and "Verified" in local state and
 * touched nothing. That is not ported. CLAUDE.md rule 6 puts invented data off limits on
 * the demo path, and a fake "Verified" badge against a caste certificate is the worst
 * possible thing to invent.
 *
 * What is real, and what this page shows instead: the checklist comes from the rule
 * pack, carries a digest so a partner and a citizen can confirm they are reading the same
 * version, and marks which documents contain a government ID — those get masked to the
 * last four digits at ingestion and never stored in full.
 *
 * Uploading belongs to an application, not to an account, and the page says so rather
 * than offering a button that would attach a file to nothing.
 */

import { FileText, ShieldAlert } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useCatalogue } from "@/components/account/useCitizenData";
import { Chip, Field, SelectInput } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { getScheme } from "@/lib/citizenApi";

import type { SchemeDetail } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export function DocumentsClient({ locale }: { locale: Locale }) {
  const t = useTranslations("myDocuments");
  const tCommon = useTranslations("common");
  const catalogue = useCatalogue(locale);

  const [code, setCode] = useState("");
  const [scheme, setScheme] = useState<SchemeDetail | null>(null);

  const schemes = catalogue.data?.schemes ?? [];
  const chosen = code || schemes[0]?.code || "";

  useEffect(() => {
    if (!chosen) return;
    let cancelled = false;
    void getScheme(chosen, locale).then((result) => {
      if (!cancelled && result.ok) setScheme(result.data);
    });
    return () => {
      cancelled = true;
    };
  }, [chosen, locale]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      <section className="panel p-4">
        <Field label={t("pickScheme")}>
          {({ id }) => (
            <SelectInput id={id} value={chosen} onChange={(event) => setCode(event.target.value)}>
              {schemes.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.official_name}
                </option>
              ))}
            </SelectInput>
          )}
        </Field>
      </section>

      {!scheme ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : (
        <>
          <p className="text-ink-muted">{t("forScheme", { scheme: scheme.official_name })}</p>

          <ul className="grid gap-3 lg:grid-cols-2">
            {scheme.required_documents.map((document) => (
              <li key={document.id} className="panel p-5">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-card bg-accent-50 text-accent-700">
                    <FileText className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <h2 className="font-display font-bold">{document.name}</h2>
                    <p className="mt-1 text-sm font-medium text-ink-faint">{t("why")}</p>
                    <p className="mt-0.5 text-ink-muted">{document.why}</p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {document.issued_by && (
                        <Chip tone="neutral">
                          {t("issuedBy", { authority: document.issued_by })}
                        </Chip>
                      )}
                      {document.validity_months !== null && (
                        <Chip tone={document.validity_is_practice_not_rule ? "warn" : "neutral"}>
                          {t("validity", { months: document.validity_months })}
                        </Chip>
                      )}
                    </div>

                    {document.validity_is_practice_not_rule && (
                      <p className="mt-2 text-sm text-warn-fg">{t("validityPractice")}</p>
                    )}
                    {document.contains_government_id && (
                      <p className="mt-3 flex items-start gap-2 rounded-card bg-accent-50 px-3 py-2 text-sm text-accent-800">
                        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                        {t("masked")}
                      </p>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <section className="panel p-5">
            <p className="text-ink-muted">{t("uploadNote")}</p>
            <Link href="/matches" className="btn-secondary mt-4 text-base">
              {t("pickScheme")}
            </Link>
            <p className="numeric mt-4 text-sm text-ink-faint">
              {t("digest", { digest: scheme.checklist_digest })}
            </p>
          </section>
        </>
      )}
    </div>
  );
}
