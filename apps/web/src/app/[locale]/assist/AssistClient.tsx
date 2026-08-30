"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { MicButton } from "@/components/MicButton";
import type { Locale } from "@/i18n/config";
import { sendTurn, type TurnResponse } from "@/lib/api";
import { saveResults } from "@/lib/storage";

/**
 * The conversational intake.
 *
 * Answers already given are shown as chips the citizen can tap to correct, because a
 * mis-heard income is the difference between eligible and not and they must be able to
 * see and fix what we think we heard.
 */
export function AssistClient({ locale }: { locale: Locale }) {
  const t = useTranslations("assist");
  const c = useTranslations("common");
  const a11y = useTranslations("a11y");
  const router = useRouter();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turn, setTurn] = useState<TurnResponse | null>(null);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const submit = useCallback(
    async (utterance: string) => {
      const text = utterance.trim();
      if (!text || busy) return;
      setBusy(true);
      setError(null);

      const result = await sendTurn(text, locale, sessionId);
      setBusy(false);

      if (!result.ok) {
        setError(result.error === "offline" ? c("offline") : c("error"));
        return;
      }

      setTyped("");
      setSessionId(result.data.session_id);
      setTurn(result.data);

      if (result.data.results) {
        // Written before navigating so the results page works with the network gone.
        saveResults({
          language: locale,
          profile: result.data.profile,
          results: result.data.results,
          explanations: result.data.explanations ?? [],
          sessionId: result.data.session_id,
          district: (result.data.context?.district as string | undefined) ?? null,
          matchRunId: result.data.match_run_id ?? null,
        });
        router.push(`/${locale}/results`);
      }
    },
    [busy, c, locale, router, sessionId],
  );

  useEffect(() => {
    inputRef.current?.focus();
  }, [turn?.question_field]);

  const answers = Object.entries(turn?.profile ?? {});

  return (
    <div className="space-y-6">
      {/* The question. aria-live so a screen reader announces each new one without
          the citizen having to hunt for it. */}
      <section
        aria-live="polite"
        aria-label={a11y("conversation")}
        className="card p-5"
      >
        {turn?.questions_asked ? (
          <p className="mb-2 text-sm font-medium text-ink-faint">
            {t("progress", {
              current: turn.questions_asked,
              max: turn.max_questions,
            })}
          </p>
        ) : null}
        <p className="text-xl font-medium">
          {busy ? t("thinking") : (turn?.question ?? t("heading"))}
        </p>

        {turn?.question_choices?.length ? (
          <ul className="mt-4 flex flex-wrap gap-2">
            {turn.question_choices.map((choice) => (
              <li key={choice}>
                <button
                  type="button"
                  onClick={() => submit(choice)}
                  disabled={busy}
                  className="btn-secondary px-4 text-base"
                >
                  {choice}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      {error ? (
        <p role="alert" className="rounded-card bg-stop-bg px-4 py-3 text-stop-fg">
          {error}
        </p>
      ) : null}

      <MicButton locale={locale} disabled={busy} onTranscript={submit} />

      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit(typed);
        }}
        className="space-y-3"
      >
        <label htmlFor="answer" className="block text-base font-medium">
          {t("typeInstead")}
        </label>
        <div className="flex gap-2">
          <input
            id="answer"
            ref={inputRef}
            value={typed}
            onChange={(event) => setTyped(event.target.value)}
            placeholder={t("placeholder")}
            enterKeyHint="send"
            autoComplete="off"
            className="min-h-touch flex-1 rounded-card border-2 border-line bg-surface px-4 text-lg"
          />
          <button type="submit" disabled={busy || !typed.trim()} className="btn-primary px-6">
            {t("send")}
          </button>
        </div>
      </form>

      {answers.length > 0 ? (
        <section aria-labelledby="answers-heading" className="card p-5">
          <h2 id="answers-heading" className="text-base font-medium">
            {t("yourAnswers")}
          </h2>
          <p className="mt-1 text-sm text-ink-faint">{t("tapToChange")}</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {answers.map(([field, value]) => (
              <li key={field}>
                <button
                  type="button"
                  onClick={() => {
                    setTyped("");
                    inputRef.current?.focus();
                  }}
                  className="min-h-touch rounded-card bg-accent-50 px-4 text-base text-accent-800"
                >
                  <span className="block text-xs text-ink-faint">
                    {field.replace(/_/g, " ")}
                  </span>
                  {String(value)}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
