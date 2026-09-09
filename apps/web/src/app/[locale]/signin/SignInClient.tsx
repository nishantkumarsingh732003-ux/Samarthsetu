"use client";

/**
 * Sign in, or create an account. One screen, one toggle.
 *
 * Deliberately outside the `AccountProvider`: this page's only job is to obtain a token
 * and leave. Wiring it into the context would mean two provider trees for no gain, and
 * the provider on the destination page reads the token from storage on mount anyway.
 *
 * Three things worth noticing:
 *
 * - **Consent is a real checkbox with a real consequence.** The design drop's signup form
 *   has three fields and no consent control. It cannot be built that way: CLAUDE.md rule 4
 *   requires an explicit consent record before anything personal is stored, and the API
 *   refuses the signup with a 400 without one, so a form without the box would simply not
 *   work. It is unticked by default; a pre-ticked consent box is not consent.
 * - **The demo block names a citizen who is really there.** "Rahul Kumar — SC entrepreneur
 *   · Tailoring unit · Jaipur" is not invented copy: it is `DEMO_CITIZEN` / `DEMO_PROFILE`
 *   in `apps/api/app/services/citizen_accounts.py`, and `lib/demoAccount.test.ts` fails if
 *   the two drift apart. He is a set of answers chosen to sit inside the published
 *   ceilings, so a reviewer watches the engine separate the scheme families rather than
 *   agree with everything.
 * - **The demo credentials block is for a hackathon laptop and must not be deployed.**
 *   It is listed in docs/DEPLOYMENT.md beside /demo for the same reason.
 */

import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button, Field, TextInput } from "@/components/ui/controls";
import { toast } from "@/components/ui/sonner";
import { signIn, signUp } from "@/lib/citizenApi";
import { DEMO_ACCOUNT } from "@/lib/demoAccount";

import type { Locale } from "@/i18n/config";

// Seeded by scripts/seed/users.py. Same caveat as the /demo console: this puts a known
// password in the page source, which is fine on a laptop over synthetic data and
// nowhere else.
const DEMO_EMAIL = "citizen@setu.gov.in";
const DEMO_PASSWORD = "setu-demo-2026";

type Mode = "signin" | "signup";

export function SignInClient({ locale }: { locale: Locale }) {
  const t = useTranslations("auth");
  const tCommon = useTranslations("common");
  const tApp = useTranslations("app");
  const router = useRouter();

  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const go = (path: string) => router.push(`/${locale}${path}`);

  /** A finished profile goes to the dashboard; an empty one goes where it can be filled
   *  in. Landing an account with nothing in it on an empty dashboard is a dead end. */
  const land = (completed: boolean) =>
    go(completed ? "/dashboard" : "/onboarding");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (mode === "signup" && !consent) {
      setError(t("consentMissing"));
      return;
    }

    setBusy(true);
    const result =
      mode === "signin"
        ? await signIn(email.trim(), password)
        : await signUp({
            email: email.trim(),
            password,
            displayName: displayName.trim(),
            language: locale,
          });
    setBusy(false);

    if (result.ok) {
      toast.success(
        t(mode === "signin" ? "toastSignedIn" : "toastAccountCreated"),
      );
      land(result.data.profile.completed);
      return;
    }
    if (result.error === "conflict") setError(t("duplicate"));
    else if (result.error === "unauthorised") setError(t("failed"));
    else if (result.error === "offline") setError(tCommon("offline"));
    else setError(result.detail ?? tCommon("error"));
  }

  async function signInAsDemo() {
    setBusy(true);
    setError(null);
    const result = await signIn(DEMO_EMAIL, DEMO_PASSWORD);
    setBusy(false);
    // Was hardcoded to /dashboard, which is where the seeded demo account has nothing to
    // show — its profile is empty until someone fills it in.
    if (result.ok) {
      toast.success(t("toastDemoLoaded"));
      land(result.data.profile.completed);
    } else {
      setError(t("failed"));
    }
  }

  // The audiences the profile contract actually recognises and the rule pack actually
  // serves. The drop had "SC · SC/ST/OBC" here; every scheme in `packages/rules` is
  // Scheduled Caste only, so an OBC applicant reading that chip would have been told
  // they qualify for something they do not.
  const audiences = [t("chipSc"), t("chipSafai"), t("chipPwd"), t("chipWomen")];

  return (
    <div className="grid min-h-screen lg:h-screen lg:grid-cols-2 lg:overflow-hidden">
      <aside className="panel-dark relative hidden flex-col justify-between overflow-y-auto rounded-none p-10 lg:flex xl:p-12">
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className="grid h-10 w-10 place-items-center rounded-card bg-white/15 font-display text-lg font-bold"
          >
            स
          </span>
          <span className="leading-tight">
            <span className="block font-display text-base font-bold">
              {tApp("title")}
            </span>
            <span className="block text-xs text-white/60">
              {tApp("ministryShort")}
            </span>
          </span>
        </span>

        <div>
          <p className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-saffron">
            <Sparkles className="h-4 w-4 shrink-0" aria-hidden="true" />
            {t("brandEyebrow")}
          </p>
          <p className="mt-4 max-w-lg font-display text-3xl font-extrabold leading-[1.15] xl:text-4xl">
            {t("brandTitle")}
          </p>
          <p className="mt-4 max-w-md text-white/75">{t("brandSub")}</p>

          <ul className="mt-7 flex flex-wrap gap-2.5">
            {audiences.map((audience) => (
              <li
                key={audience}
                className="rounded-full border border-white/20 bg-white/10 px-3.5 py-1.5 text-sm"
              >
                {audience}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-sm text-white/55">{t("consentHint")}</p>
      </aside>

      <main className="overflow-y-auto bg-surface">
        <div className="flex min-h-full items-center justify-center px-5 py-4">
          <div className="w-full max-w-sm">
            <div className="flex items-center justify-between gap-3">
              <Link
                href={`/${locale}`}
                className="inline-flex min-h-touch items-center gap-1.5 rounded-card text-ink-muted
                         hover:text-accent-700"
              >
                <ArrowRight className="h-4 w-4 rotate-180" aria-hidden="true" />
                {tCommon("back")}
              </Link>
              <LanguageSwitcher locale={locale} />
            </div>

            <h1 className="mt-3 font-display text-2xl font-extrabold">
              {t(mode === "signin" ? "signInTitle" : "signUpTitle")}
            </h1>
            <p className="mt-1 text-ink-muted">
              {t(mode === "signin" ? "signInSub" : "signUpSub")}
            </p>

            <form onSubmit={submit} className="mt-4 space-y-2.5">
              {mode === "signup" && (
                <Field label={t("fullName")}>
                  {({ id }) => (
                    <TextInput
                      id={id}
                      required
                      autoComplete="name"
                      placeholder={t("fullNamePlaceholder")}
                      value={displayName}
                      onChange={(event) => setDisplayName(event.target.value)}
                    />
                  )}
                </Field>
              )}

              <Field label={t("email")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    required
                    type="email"
                    autoComplete="email"
                    inputMode="email"
                    placeholder={t("emailPlaceholder")}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                )}
              </Field>

              <Field label={t("password")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    required
                    type="password"
                    minLength={mode === "signup" ? 8 : undefined}
                    autoComplete={
                      mode === "signup" ? "new-password" : "current-password"
                    }
                    placeholder={
                      mode === "signup" ? t("passwordHint") : undefined
                    }
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                )}
              </Field>

              {mode === "signup" && (
                <label className="flex items-start gap-2.5 rounded-card border border-line bg-canvas p-2.5">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-5 w-5 shrink-0 accent-accent-700"
                    checked={consent}
                    onChange={(event) => setConsent(event.target.checked)}
                  />
                  <span className="text-sm">{t("consentLabel")}</span>
                </label>
              )}

              {error && (
                <p
                  role="alert"
                  className="rounded-card bg-stop-bg px-4 py-3 text-stop-fg"
                >
                  {error}
                </p>
              )}

              <Button type="submit" disabled={busy} className="w-full">
                {busy
                  ? t("working")
                  : t(mode === "signin" ? "submitSignIn" : "submitSignUp")}
                {busy ? null : (
                  <ArrowRight className="h-5 w-5" aria-hidden="true" />
                )}
              </Button>
            </form>

            <p className="mt-4 text-center text-ink-muted">
              {mode === "signin"
                ? t("newHerePrompt", { app: tApp("title") })
                : t("alreadyPrompt")}{" "}
              <button
                type="button"
                className="font-semibold text-accent-700 underline-offset-4 hover:underline"
                onClick={() => {
                  setMode(mode === "signin" ? "signup" : "signin");
                  setError(null);
                }}
              >
                {t(mode === "signin" ? "submitSignUp" : "submitSignIn")}
              </button>
            </p>

            <div className="mt-5 flex items-center gap-3">
              <span aria-hidden="true" className="h-px flex-1 bg-line" />
              <span className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                {t("quickDemo")}
              </span>
              <span aria-hidden="true" className="h-px flex-1 bg-line" />
            </div>

            <Button
              variant="secondary"
              disabled={busy}
              onClick={signInAsDemo}
              className="mt-3 w-full border-saffron-line bg-saffron-bg text-saffron-fg
                       hover:border-saffron"
            >
              <Sparkles className="h-5 w-5" aria-hidden="true" />
              {t("demoButton", { name: DEMO_ACCOUNT.name })}
            </Button>
            <p className="mt-1.5 text-center text-sm text-ink-faint">
              {t("demoHint", {
                category: DEMO_ACCOUNT.category,
                trade: t("demoTrade"),
                district: DEMO_ACCOUNT.district,
              })}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
