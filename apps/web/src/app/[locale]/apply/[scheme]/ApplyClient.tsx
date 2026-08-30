"use client";

import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n/config";
import {
  getChecklist,
  submitApplication,
  type RequiredDocument,
} from "@/lib/api";
import { formatRupees } from "@/lib/format";
import { loadResults } from "@/lib/storage";

/**
 * The submission form.
 *
 * Three decisions worth naming.
 *
 * **Everything is optional except consent.** A citizen who will not type their Aadhaar
 * into a phone still gets a reference number and a branch to walk into. Withholding an
 * identifier costs them nothing here; the partner asks for it in person.
 *
 * **The checklist is shown before the submit button, not after.** The point of the
 * screen is that they leave knowing what to carry.
 *
 * **Consent is an unticked box with the consequence written next to it.** A pre-ticked
 * box is not consent under the DPDP Act, and it is not consent in any ordinary sense.
 */
export function ApplyClient({
  locale,
  schemeCode,
}: {
  locale: Locale;
  schemeCode: string;
}) {
  const t = useTranslations("apply");
  const c = useTranslations("common");
  const d = useTranslations("docs");
  const router = useRouter();
  const search = useSearchParams();

  const partnerId = search.get("partner") ?? undefined;
  const partnerName = search.get("partnerName") ?? undefined;
  const partnerType = search.get("partnerType") ?? undefined;
  const family = search.get("family") ?? "MICRO_FINANCE";
  const amount = Number(search.get("amount") ?? 0);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [govId, setGovId] = useState("");
  const [consent, setConsent] = useState(false);
  const [checklist, setChecklist] = useState<RequiredDocument[] | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getChecklist(family, locale, partnerType).then((result) => {
      if (result.ok) setChecklist(result.data.documents);
    });
  }, [family, locale, partnerType]);

  const submit = useCallback(async () => {
    if (!consent) return;
    setSubmitting(true);
    setError(null);

    const saved = loadResults();
    const result = await submitApplication({
      schemeCode,
      partnerId,
      amount: amount > 0 ? amount : undefined,
      // Pins the application to the eligibility run that led here, so a sanction can
      // be replayed against the rules that were live at the time.
      matchRunId: search.get("run"),
      language: locale,
      applicant: {
        ...(name.trim() ? { display_name: name.trim() } : {}),
        ...(phone.trim() ? { phone: phone.trim() } : {}),
        ...(govId.trim() ? { gov_id: govId.trim(), gov_id_type: "AADHAAR" as const } : {}),
        ...(saved?.district ? { district: saved.district } : {}),
      },
    });

    if (result.ok) {
      router.push(`/${locale}/track/${result.data.reference_no}`);
      return;
    }
    setSubmitting(false);
    setError(result.error === "offline" ? c("offline") : c("error"));
  }, [
    amount,
    c,
    consent,
    govId,
    locale,
    name,
    partnerId,
    phone,
    router,
    schemeCode,
    search,
  ]);

  return (
    <form
      className="space-y-6"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      {partnerName ? (
        <section className="card p-4">
          <h2 className="text-base text-ink-muted">{t("goingTo")}</h2>
          <p className="mt-1 text-lg font-medium">{partnerName}</p>
          {amount > 0 ? (
            <p className="mt-1 text-base text-ink-muted">
              {c("rupees", { amount: formatRupees(amount, locale) })}
            </p>
          ) : null}
        </section>
      ) : null}

      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold">{t("aboutYou")}</legend>
        <p className="text-base text-ink-muted">{t("allOptional")}</p>

        <label className="block">
          <span className="text-base">{t("yourName")}</span>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            autoComplete="name"
            className="mt-1 w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-lg"
          />
        </label>

        <label className="block">
          <span className="text-base">{t("yourPhone")}</span>
          <input
            type="tel"
            inputMode="numeric"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            autoComplete="tel"
            className="mt-1 w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-lg"
          />
          <span className="mt-1 block text-sm text-ink-faint">{t("phoneLast4")}</span>
        </label>

        <label className="block">
          <span className="text-base">{t("yourId")}</span>
          <input
            type="text"
            inputMode="numeric"
            value={govId}
            onChange={(event) => setGovId(event.target.value)}
            className="mt-1 w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-lg"
          />
          {/* The exact promise, in the place the citizen is deciding whether to type it. */}
          <span className="mt-1 block text-sm text-ink-faint">{t("idMasked")}</span>
        </label>
      </fieldset>

      {checklist && checklist.length > 0 ? (
        <section className="card p-4" aria-labelledby="bring-heading">
          <h2 id="bring-heading" className="text-lg font-semibold">
            {d("whatToBring")}
          </h2>
          <ul className="mt-3 space-y-3">
            {checklist.map((doc) => (
              <li key={doc.id} className="border-t border-line pt-3">
                <p className="text-base font-medium">{doc.name}</p>
                <p className="text-base text-ink-muted">{doc.why}</p>
                {doc.validity_months ? (
                  <p className="mt-1 text-sm text-ink-faint">
                    {doc.validity_is_practice_not_rule
                      ? d("validityPractice", { months: doc.validity_months })
                      : d("validityRule", { months: doc.validity_months })}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <label className="flex gap-3 rounded-card border-2 border-line p-4">
        <input
          type="checkbox"
          checked={consent}
          onChange={(event) => setConsent(event.target.checked)}
          className="mt-1 h-6 w-6 shrink-0"
        />
        <span className="text-base">{t("consentText")}</span>
      </label>

      {error ? (
        <p role="alert" className="text-lg text-warn-fg">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={!consent || submitting}
        className="btn-primary w-full disabled:opacity-50"
      >
        {submitting ? c("loading") : t("submit")}
      </button>

      <p className="text-sm text-ink-faint">{t("afterSubmit")}</p>
    </form>
  );
}
