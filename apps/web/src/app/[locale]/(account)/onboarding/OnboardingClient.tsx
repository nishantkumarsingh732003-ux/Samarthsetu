"use client";

/**
 * Four steps to a complete profile.
 *
 * The one structural decision worth stating: **each step saves as you leave it.** The
 * design drop held all six steps in memory and posted once at the end, which on a 2G
 * connection means a citizen who loses signal on step five retypes everything. Saving
 * per step costs four small requests instead of one and loses at most one screen.
 *
 * The visual separation between step 1 and step 2 is not cosmetic either. Step 1 is the
 * engine's contract — those answers decide verdicts. Step 2 is the enterprise
 * description, which a partner officer reads and the rules never see. The hint on each
 * step says so, and the profile page proves it by printing the exact dictionary handed
 * to the engine.
 */

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import {
  Button,
  Field,
  ProgressBar,
  SelectInput,
  TextArea,
  TextInput,
} from "@/components/ui/controls";

import type { CitizenProfile } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

const STEPS = ["step1", "step2", "step3", "step4"] as const;

const CATEGORIES = ["SC", "ST", "OBC", "GENERAL"] as const;
const GENDERS = ["FEMALE", "MALE", "OTHER", "UNDISCLOSED"] as const;
// Mirrors `setu_rules.profile.PROJECT_SECTORS`. Anything outside it is rejected by the
// engine's own validation, so the control offers exactly that vocabulary and no more.
const SECTORS = [
  "AGRICULTURE",
  "MANUFACTURING",
  "SERVICES",
  "TRADE",
  "TRANSPORT",
  "ARTISAN",
  "EDUCATION",
  "OTHER",
] as const;

/** Fields the wizard can edit. `completed` is excluded because it is not an answer —
 *  it is set by the save call when the last step is left, and letting it into the draft
 *  would widen its type to `unknown` at the call boundary. */
type Editable = Exclude<keyof CitizenProfile, "completed" | "completion_pct" | "engine_profile">;
type Draft = Partial<Record<Editable, unknown>>;

/** "" from an empty control means "not answered", which is null — not zero. */
function numberOrNull(value: string): number | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : Number(trimmed);
}

function textOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export function OnboardingClient({ locale }: { locale: Locale }) {
  const t = useTranslations("onboarding");
  const tCommon = useTranslations("common");
  const { account, updateProfile } = useAccount();
  const router = useRouter();

  const profile = account?.profile;
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft>({});

  // The stored value unless this session has typed over it.
  const value = <K extends Editable>(key: K): CitizenProfile[K] | null =>
    (key in draft ? (draft[key] as CitizenProfile[K]) : (profile?.[key] ?? null)) ?? null;

  const asText = (key: Editable): string => {
    const current = value(key);
    return current === null || current === undefined ? "" : String(current);
  };

  const set = (key: Editable, next: unknown) =>
    setDraft((previous) => ({ ...previous, [key]: next }));

  async function commit(finished: boolean) {
    if (Object.keys(draft).length === 0 && !finished) return true;
    setBusy(true);
    setError(null);
    const result = await updateProfile(finished ? { ...draft, completed: true } : draft);
    setBusy(false);
    if (!result.ok) {
      setError(result.error === "offline" ? tCommon("offline") : t("saveFailed"));
      return false;
    }
    setDraft({});
    return true;
  }

  async function next() {
    const last = step === STEPS.length - 1;
    if (!(await commit(last))) return;
    if (last) router.push(`/${locale}/matches`);
    else setStep((current) => current + 1);
  }

  const yesNo = (key: Editable, label: string) => (
    <Field label={label}>
      {({ id }) => (
        <SelectInput
          id={id}
          value={value(key) === null ? "" : value(key) ? "yes" : "no"}
          onChange={(event) =>
            set(key, event.target.value === "" ? null : event.target.value === "yes")
          }
        >
          <option value="">{t("notSure")}</option>
          <option value="yes">{t("yes")}</option>
          <option value="no">{t("no")}</option>
        </SelectInput>
      )}
    </Field>
  );

  return (
    <div className="mx-auto max-w-2xl">
      <header>
        <h1 className="font-display text-2xl font-extrabold">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">
          {t("step", { current: step + 1, total: STEPS.length })} · {t(STEPS[step])}
        </p>
        <div className="mt-3">
          <ProgressBar
            value={((step + 1) / STEPS.length) * 100}
            label={t("step", { current: step + 1, total: STEPS.length })}
          />
        </div>
      </header>

      <div className="panel mt-6 p-5 lg:p-7">
        <h2 className="font-display text-xl font-bold">{t(STEPS[step])}</h2>
        <p className="mt-1 text-ink-muted">{t(`${STEPS[step]}Hint`)}</p>

        <div className="mt-6 space-y-5">
          {step === 0 && (
            <>
              <Field label={t("fullName")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    autoComplete="name"
                    value={asText("display_name")}
                    onChange={(event) => set("display_name", textOrNull(event.target.value))}
                  />
                )}
              </Field>

              <Field label={t("category")}>
                {({ id }) => (
                  <SelectInput
                    id={id}
                    value={asText("category")}
                    onChange={(event) => set("category", textOrNull(event.target.value))}
                  >
                    <option value="">{t("choose")}</option>
                    {CATEGORIES.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </SelectInput>
                )}
              </Field>

              <Field label={t("income")} hint={t("incomeHint")}>
                {({ id, describedBy }) => (
                  <TextInput
                    id={id}
                    type="number"
                    inputMode="numeric"
                    min={0}
                    aria-describedby={describedBy}
                    value={asText("annual_family_income")}
                    onChange={(event) =>
                      set("annual_family_income", numberOrNull(event.target.value))
                    }
                  />
                )}
              </Field>

              <div className="grid gap-5 sm:grid-cols-2">
                <Field label={t("age")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      type="number"
                      inputMode="numeric"
                      min={0}
                      max={120}
                      value={asText("age")}
                      onChange={(event) => set("age", numberOrNull(event.target.value))}
                    />
                  )}
                </Field>

                <Field label={t("gender")}>
                  {({ id }) => (
                    <SelectInput
                      id={id}
                      value={asText("gender")}
                      onChange={(event) => set("gender", textOrNull(event.target.value))}
                    >
                      <option value="">{t("choose")}</option>
                      {GENDERS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </SelectInput>
                  )}
                </Field>
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                <Field label={t("education")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      value={asText("education_level")}
                      onChange={(event) =>
                        set("education_level", textOrNull(event.target.value))
                      }
                    />
                  )}
                </Field>
                <Field label={t("occupation")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      value={asText("occupation_type")}
                      onChange={(event) =>
                        set("occupation_type", textOrNull(event.target.value))
                      }
                    />
                  )}
                </Field>
              </div>

              {yesNo("has_caste_certificate", t("casteCertificate"))}
              {yesNo("is_pwd", t("pwd"))}
              {yesNo("is_safai_karamchari", t("safai"))}
            </>
          )}

          {step === 1 && (
            <>
              <Field label={t("sector")}>
                {({ id }) => (
                  <SelectInput
                    id={id}
                    value={asText("project_sector")}
                    onChange={(event) => set("project_sector", textOrNull(event.target.value))}
                  >
                    <option value="">{t("choose")}</option>
                    {SECTORS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </SelectInput>
                )}
              </Field>

              <Field label={t("businessName")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    value={asText("business_name")}
                    onChange={(event) => set("business_name", textOrNull(event.target.value))}
                  />
                )}
              </Field>

              <Field label={t("businessStatus")}>
                {({ id }) => (
                  <SelectInput
                    id={id}
                    value={asText("business_status")}
                    onChange={(event) => set("business_status", textOrNull(event.target.value))}
                  >
                    <option value="">{t("choose")}</option>
                    <option value="NEW">{t("statusNew")}</option>
                    <option value="EXISTING">{t("statusExisting")}</option>
                  </SelectInput>
                )}
              </Field>

              <Field label={t("description")} hint={t("descriptionHint")}>
                {({ id, describedBy }) => (
                  <TextArea
                    id={id}
                    maxLength={2000}
                    aria-describedby={describedBy}
                    value={asText("business_description")}
                    onChange={(event) =>
                      set("business_description", textOrNull(event.target.value))
                    }
                  />
                )}
              </Field>
            </>
          )}

          {step === 2 && (
            <>
              <Field label={t("projectCost")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="number"
                    inputMode="numeric"
                    min={0}
                    value={asText("project_cost")}
                    onChange={(event) => set("project_cost", numberOrNull(event.target.value))}
                  />
                )}
              </Field>
              <Field label={t("ownContribution")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="number"
                    inputMode="numeric"
                    min={0}
                    value={asText("own_contribution")}
                    onChange={(event) =>
                      set("own_contribution", numberOrNull(event.target.value))
                    }
                  />
                )}
              </Field>
              <Field label={t("loanRequired")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="number"
                    inputMode="numeric"
                    min={0}
                    value={asText("loan_required")}
                    onChange={(event) => set("loan_required", numberOrNull(event.target.value))}
                  />
                )}
              </Field>
            </>
          )}

          {step === 3 && (
            <>
              <div className="grid gap-5 sm:grid-cols-2">
                <Field label={t("state")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      autoComplete="address-level1"
                      value={asText("state")}
                      onChange={(event) => set("state", textOrNull(event.target.value))}
                    />
                  )}
                </Field>
                <Field label={t("district")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      autoComplete="address-level2"
                      value={asText("district")}
                      onChange={(event) => set("district", textOrNull(event.target.value))}
                    />
                  )}
                </Field>
              </div>
              <div className="grid gap-5 sm:grid-cols-2">
                <Field label={t("city")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      value={asText("city")}
                      onChange={(event) => set("city", textOrNull(event.target.value))}
                    />
                  )}
                </Field>
                <Field label={t("pincode")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      inputMode="numeric"
                      pattern="[1-9][0-9]{5}"
                      maxLength={6}
                      autoComplete="postal-code"
                      value={asText("pincode")}
                      onChange={(event) => set("pincode", textOrNull(event.target.value))}
                    />
                  )}
                </Field>
              </div>
            </>
          )}
        </div>

        {error && (
          <p role="alert" className="mt-5 rounded-card bg-stop-bg px-4 py-3 text-stop-fg">
            {error}
          </p>
        )}

        <p className="mt-6 rounded-card bg-accent-50 px-4 py-3 text-accent-800">
          {t("engineNote")}
        </p>

        <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5">
          <Button
            variant="secondary"
            disabled={step === 0 || busy}
            onClick={() => setStep((current) => Math.max(0, current - 1))}
          >
            {t("back")}
          </Button>
          <Button onClick={next} disabled={busy}>
            {busy ? t("saving") : step === STEPS.length - 1 ? t("finish") : t("next")}
          </Button>
        </div>
      </div>
    </div>
  );
}
