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
 * - **The escape hatch is always visible.** "Check your eligibility without signing in"
 *   sits under the form, not buried. An account is a convenience here, and a sign-in
 *   wall in front of a scheme-eligibility check would be the exact barrier this project
 *   exists to remove.
 * - **Consent is a real checkbox with a real consequence.** Signup is refused without it,
 *   by the API, because the account stores personal data. It is unticked by default; a
 *   pre-ticked consent box is not consent.
 * - **The demo credentials block is for a hackathon laptop and must not be deployed.**
 *   It is listed in docs/DEPLOYMENT.md beside /demo for the same reason.
 */

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button, Field, TextInput } from "@/components/ui/controls";
import { signIn, signUp } from "@/lib/citizenApi";

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
        : await signUp({ email: email.trim(), password, displayName: displayName.trim(), language: locale });
    setBusy(false);

    if (result.ok) {
      // A finished profile goes to the dashboard; an empty one goes where it can be
      // filled in. Landing a new account on an empty dashboard is a dead end.
      go(result.data.profile.completed ? "/dashboard" : "/onboarding");
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
    if (result.ok) go("/dashboard");
    else setError(t("failed"));
  }

  return (
    <div className="ground-wash grid min-h-screen lg:grid-cols-2">
      <aside className="panel-dark hidden flex-col justify-between rounded-none p-12 lg:flex">
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className="grid h-10 w-10 place-items-center rounded-card bg-white/15 font-display text-lg font-bold"
          >
            से
          </span>
          <span className="font-display text-lg font-bold">{tApp("title")}</span>
        </span>
        <div>
          <p className="font-display text-3xl font-extrabold leading-tight">
            {t(mode === "signin" ? "signInTitle" : "signUpTitle")}
          </p>
          <p className="mt-4 max-w-md text-white/80">
            {t(mode === "signin" ? "signInSub" : "signUpSub")}
          </p>
        </div>
        <p className="text-sm text-white/60">{t("consentHint")}</p>
      </aside>

      <main className="flex items-center justify-center px-5 py-10">
        <div className="w-full max-w-sm">
          <Link href={`/${locale}`} className="btn-quiet -ml-3 text-sm">
            {tCommon("back")}
          </Link>

          <h1 className="mt-4 font-display text-2xl font-extrabold">
            {t(mode === "signin" ? "signInTitle" : "signUpTitle")}
          </h1>
          <p className="mt-1.5 text-ink-muted">
            {t(mode === "signin" ? "signInSub" : "signUpSub")}
          </p>

          <form onSubmit={submit} className="mt-7 space-y-4">
            {mode === "signup" && (
              <Field label={t("fullName")}>
                {({ id }) => (
                  <TextInput
                    id={id}
                    required
                    autoComplete="name"
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
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              )}
            </Field>

            <Field label={t("password")} hint={mode === "signup" ? t("passwordHint") : undefined}>
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  required
                  type="password"
                  minLength={mode === "signup" ? 8 : undefined}
                  autoComplete={mode === "signup" ? "new-password" : "current-password"}
                  aria-describedby={describedBy}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              )}
            </Field>

            {mode === "signup" && (
              <label className="flex items-start gap-3 rounded-card border border-line bg-surface p-3">
                <input
                  type="checkbox"
                  className="mt-1 h-5 w-5 shrink-0 accent-accent-700"
                  checked={consent}
                  onChange={(event) => setConsent(event.target.checked)}
                />
                <span className="text-base">
                  {t("consentLabel")}
                  <span className="mt-1 block field-hint">{t("consentHint")}</span>
                </span>
              </label>
            )}

            {error && (
              <p role="alert" className="rounded-card bg-stop-bg px-4 py-3 text-stop-fg">
                {error}
              </p>
            )}

            <Button type="submit" disabled={busy} className="w-full">
              {busy ? t("working") : t(mode === "signin" ? "submitSignIn" : "submitSignUp")}
            </Button>
          </form>

          <Button
            variant="quiet"
            className="mt-3 w-full"
            onClick={() => {
              setMode(mode === "signin" ? "signup" : "signin");
              setError(null);
            }}
          >
            {t(mode === "signin" ? "toSignUp" : "toSignIn")}
          </Button>

          <p className="mt-6 border-t border-line pt-6 text-center">
            <Link href={`/${locale}/assist`} className="text-accent-700 underline">
              {t("orAnonymous")}
            </Link>
          </p>

          <div className="mt-6 rounded-card border border-saffron-line bg-saffron-bg p-4">
            <p className="text-sm font-semibold text-saffron-fg">{t("demoTitle")}</p>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={signInAsDemo}
              className="mt-2 w-full text-base"
            >
              {t("demoButton")}
            </Button>
            <p className="mt-2 text-sm text-saffron-fg">{t("demoHint")}</p>
          </div>
        </div>
      </main>
    </div>
  );
}
