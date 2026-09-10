"use client";

/**
 * Samarth AI — the conversational front door, inside the signed-in shell.
 *
 * WHAT THE MODEL IS AND IS NOT ALLOWED TO DO, because this page is where it would be
 * easiest to get wrong. Every turn goes to `POST /conversation/ask` — not to
 * `/conversation/turn`, which is the anonymous intake behind `/assist` and advances a
 * profile one question at a time. This endpoint answers instead: the API assembles a
 * context pack from the published rule pack, this citizen's profile, the *deterministic*
 * engine's own verdicts with the rule ids that produced them, and their live
 * applications, and the model answers from that and nothing else. It never decides
 * eligibility (CLAUDE.md rule 1), and every verdict this thread shows carries the rule
 * ids it came from.
 *
 * That is the difference between this and a chatbot that sounds confident. A reply here
 * saying "you look eligible for the Term Loan" is the engine's verdict, wearing the
 * model's words; it is reproducible from the profile and the rules digest, and the
 * scheme cards under it link to the rule that decided.
 *
 * IT ALSO DOES THE WORK. Answers alone leave a citizen with a to-do list. When the engine
 * returns results the thread offers the scheme; when documents are outstanding on a live
 * application it offers the upload, inline, posting to the same endpoint the tracking
 * page uses; when a scheme is available it offers to start the application. Those
 * affordances are built from real state — matches, applications, the document checklist —
 * not from anything the model said.
 */

import { ArrowRight, Bot, Check, FileUp, Plus, Send, Sparkles, User } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { criterionKey } from "@/components/account/criteriaLabels";
import { useMyApplications } from "@/components/account/useCitizenData";
import { MicButton } from "@/components/MicButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Input } from "@/components/ui/input";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Link } from "@/i18n/navigation";
import {
  getApplication,
  uploadDocument,
  type ApplicationResponse,
  type RequiredDocument,
} from "@/lib/api";
import { clearThread, readThread, writeThread, type ChatEntry } from "@/lib/chatHistory";
import { askAssistant, type AssistantAction } from "@/lib/citizenApi";

import type { Locale } from "@/i18n/config";

/** One thing in the thread. `results` and `docs` are the acting parts. */
type Entry =
  | { kind: "said"; who: "citizen" | "assistant"; text: string; ruleIds?: string[] }
  | { kind: "action"; action: AssistantAction; schemeCode: string | null }
  | { kind: "docs" };

const PROMPTS = ["promptEligible", "promptBest", "promptWhy", "promptDocuments", "promptPartner"];

export function AssistantClient({ locale }: { locale: Locale }) {
  const t = useTranslations("assistant");
  const tAssist = useTranslations("assist");
  const tCommon = useTranslations("common");
  const tDocs = useTranslations("docs");
  // The criterion labels the match cards use, so a rule means the same thing wherever
  // the citizen meets it.
  const tMatches = useTranslations("matches");

  /**
   * Rule ids collapsed to the criteria a citizen reads, one chip each.
   *
   * Several rules can stand for the same criterion — a Term Loan checks project cost
   * against both a floor and a ceiling, and both map to "Project cost supported". Mapped
   * one-to-one that renders the same green chip twice, which reads as a mistake. So chips
   * are keyed by label, and every id behind a label rides along in its `title` so nothing
   * stops being checkable.
   */
  const criterionChips = useCallback(
    (ruleIds: string[]) => {
      const byLabel = new Map<string, string[]>();
      for (const id of ruleIds) {
        const key = criterionKey(id);
        const label = key ? tMatches(`criteria.${key}`) : id;
        byLabel.set(label, [...(byLabel.get(label) ?? []), id]);
      }
      return [...byLabel].map(([label, ids]) => ({ label, ids }));
    },
    [tMatches],
  );

  const applications = useMyApplications();
  const [thread, setThread] = useState<Entry[]>([]);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const inputs = useRef<Record<string, HTMLInputElement | null>>({});
  const foot = useRef<HTMLDivElement>(null);

  const reference = applications.data?.[0]?.reference_no ?? null;

  /** The live application, so the thread can offer the uploads it is actually missing. */
  const loadApplication = useCallback(async () => {
    if (!reference) return;
    const result = await getApplication(reference, locale);
    if (result.ok) setApplication(result.data);
  }, [reference, locale]);

  useEffect(() => {
    void loadApplication();
  }, [loadApplication]);

  /**
   * Restore the thread, or greet.
   *
   * Runs once, on mount, and never again — `restored` guards it rather than the
   * dependency array, because `t` changes identity when the citizen switches language
   * and the previous version of this effect listed it as a dependency. That meant
   * choosing Hindi wiped the conversation you were having. A thread is the citizen's own
   * record of what they were told; changing the language of the next reply is not a
   * reason to throw away the last one.
   *
   * The greeting is a message rather than a placeholder, so the thread is never empty
   * and a first-time citizen can see what this is for before typing. It seeds only when
   * there is nothing to restore.
   *
   * Deliberately in an effect and not in `useState`: `readThread()` reads
   * `localStorage`, which does not exist during the server render, so seeding initial
   * state from it would hydrate mismatched.
   */
  const restored = useRef(false);
  useEffect(() => {
    if (restored.current) return;
    restored.current = true;
    const saved = readThread();
    setThread(
      saved.length > 0 ? saved : [{ kind: "said", who: "assistant", text: t("greeting") }],
    );
  }, [t]);

  // Persist on every change. `docs` entries are dropped on the way out: that panel is
  // live application state, refetched on mount, and a cached copy would go stale and
  // start claiming documents are still outstanding after they have been uploaded.
  useEffect(() => {
    if (!restored.current || thread.length === 0) return;
    writeThread(thread.filter((entry): entry is ChatEntry => entry.kind !== "docs"));
  }, [thread]);

  /** Start again. The stored thread goes too, or reloading would bring it back. */
  const startNewChat = useCallback(() => {
    clearThread();
    setThread([{ kind: "said", who: "assistant", text: t("greeting") }]);
    setError(null);
  }, [t]);

  useEffect(() => {
    foot.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [thread, busy]);

  const submit = useCallback(
    async (utterance: string) => {
      const text = utterance.trim();
      if (!text || busy) return;

      setThread((current) => [...current, { kind: "said", who: "citizen", text }]);
      setTyped("");
      setBusy(true);
      setError(null);

      // Only what was actually said goes back as history — the action cards and the
      // document list are UI, not conversation, and would only crowd the context.
      const history = thread
        .filter((entry): entry is Extract<Entry, { kind: "said" }> => entry.kind === "said")
        .map((entry) => ({ role: entry.who, text: entry.text }));

      const result = await askAssistant(text, locale, history);
      setBusy(false);

      if (!result.ok) {
        setError(result.error === "offline" ? tCommon("offline") : tCommon("error"));
        return;
      }

      const next: Entry[] = [];
      /**
       * `grounded: false` means no model was reachable and the API answered
       * deterministically from the same pack — it still returns a real sentence naming
       * the scheme the engine matched, so it renders like any other reply. `noModel` is
       * the last guard, for a reply that somehow arrives empty; it should not be seen.
       */
      next.push({
        kind: "said",
        who: "assistant",
        text: result.data.answer || t("noModel"),
        ruleIds: result.data.rule_ids,
      });

      // The model proposes; the citizen presses. Nothing is submitted on its say-so.
      if (result.data.action === "upload_documents") {
        next.push({ kind: "docs" });
      } else if (result.data.action) {
        next.push({
          kind: "action",
          action: result.data.action,
          schemeCode: result.data.action_scheme_code,
        });
      }

      setThread((current) => [...current, ...next]);
    },
    [busy, locale, t, tCommon, thread],
  );

  const onFile = useCallback(
    async (document: RequiredDocument, file: File) => {
      if (!reference) return;
      setUploading(document.id);
      await uploadDocument(reference, document.id, file, document.validity_months);
      setUploading(null);
      await loadApplication();
      setThread((current) => [
        ...current,
        { kind: "said", who: "assistant", text: t("uploaded", { name: document.name }) },
      ]);
    },
    [reference, loadApplication, t],
  );

  const outstanding = (application?.required_documents ?? []).filter((doc) => !doc.uploaded);

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <Card className="flex min-h-[38rem] flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-4 lg:p-5">
          <span className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="grid h-11 w-11 place-items-center rounded-card bg-accent-700 text-white"
            >
              <Bot className="h-5 w-5" />
            </span>
            <span>
              <span className="block font-display text-lg font-bold">{t("name")}</span>
              <span className="block text-sm text-ink-faint">{t("tagline")}</span>
            </span>
          </span>
          <span className="flex items-center gap-2">
            {/* Says what the model does here, which is read and restate — not decide. */}
            <Chip tone="teal">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              {t("badge")}
            </Chip>
            {/* The thread now outlives the visit, so there has to be a way to end one.
                Shown only once there is something to clear. */}
            {thread.length > 1 && (
              <Button
                variant="secondary"
                onClick={startNewChat}
                disabled={busy}
                className="text-base"
              >
                <Plus className="h-4 w-4" aria-hidden="true" />
                {t("newChat")}
              </Button>
            )}
          </span>
        </div>

        <div
          className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 lg:p-5"
          aria-live="polite"
          aria-label={t("conversation")}
        >
          {thread.map((entry, index) => {
            if (entry.kind === "action") {
              return (
                <ProposedAction
                  key={index}
                  action={entry.action}
                  schemeCode={entry.schemeCode}
                />
              );
            }
            if (entry.kind === "docs") {
              return (
                <div key={index} className="ml-11 rounded-card border border-line p-4">
                  <p className="flex items-center gap-2 font-semibold">
                    <FileUp className="h-4 w-4 shrink-0 text-accent-700" aria-hidden="true" />
                    {t("docsHeading", { count: outstanding.length })}
                  </p>
                  <ul className="mt-3 space-y-2">
                    {outstanding.map((document) => (
                      <li
                        key={document.id}
                        className="flex flex-wrap items-center justify-between gap-2"
                      >
                        <span className="min-w-0">{document.name}</span>
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
                          disabled={uploading === document.id}
                          onClick={() => inputs.current[document.id]?.click()}
                          className="shrink-0 text-base"
                        >
                          {uploading === document.id
                            ? tDocs("uploading")
                            : tDocs("takePhoto")}
                        </Button>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-sm text-ink-faint">{tDocs("privacyNote")}</p>
                </div>
              );
            }

            const mine = entry.who === "citizen";
            return (
              <div
                key={index}
                className={`flex items-start gap-3 ${mine ? "flex-row-reverse" : ""}`}
              >
                <span
                  aria-hidden="true"
                  className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${
                    mine ? "bg-canvas text-ink-muted" : "bg-accent-700 text-white"
                  }`}
                >
                  {mine ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </span>
                <span
                  className={`max-w-[46rem] rounded-panel px-4 py-3 ${
                    mine
                      ? "bg-accent-700 text-white"
                      : "border border-line bg-surface text-ink"
                  }`}
                >
                  <span className="whitespace-pre-line">{entry.text}</span>
                  {/* What the answer leaned on.
                      Previously this printed the raw ids — TL_CATEGORY_SC,
                      TL_INCOME_CEILING — under every reply. That is the engine's
                      vocabulary, not a citizen's: it is unreadable to the person the
                      service is for, and on a low-literacy screen it reads as an error
                      code. So each id is shown as the criterion it stands for, using the
                      same mapping and the same words the match cards use, and the id
                      itself rides along in the `title` for anyone checking. Nothing that
                      was traceable stops being traceable — it stops being shouted. */}
                  {!mine && entry.ruleIds && entry.ruleIds.length > 0 && (
                    <span className="mt-2.5 flex flex-wrap gap-1.5">
                      {criterionChips(entry.ruleIds).map(({ label, ids }) => (
                        <Link
                          key={label}
                          href="/schemes"
                          // Every id behind this chip, for anyone checking. The label is
                          // what the citizen reads; the ids are what an auditor needs.
                          title={ids.join(" · ")}
                          className="inline-flex items-center gap-1 rounded-full bg-good-bg
                                     px-2.5 py-0.5 text-sm text-good-fg transition-colors
                                     hover:bg-good-line"
                        >
                          <Check className="h-3 w-3 shrink-0" aria-hidden="true" />
                          {label}
                        </Link>
                      ))}
                    </span>
                  )}
                </span>
              </div>
            );
          })}

          {busy && (
            <div className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-700 text-white"
              >
                <Bot className="h-4 w-4" />
              </span>
              <span className="rounded-panel border border-line px-4 py-3 text-ink-faint">
                {tAssist("thinking")}
              </span>
            </div>
          )}

          {error && (
            <p role="alert" className="rounded-card bg-stop-bg px-4 py-3 text-stop-fg">
              {error}
            </p>
          )}

          <div ref={foot} />
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit(typed);
          }}
          className="flex items-center gap-2 border-t border-line p-3 lg:p-4"
        >
          <MicButton locale={locale} disabled={busy} onTranscript={submit} variant="icon" />
          <Input
            value={typed}
            onChange={(event) => setTyped(event.currentTarget.value)}
            placeholder={t("placeholder")}
            aria-label={t("placeholder")}
            enterKeyHint="send"
            autoComplete="off"
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={busy || !typed.trim()}
            size="icon"
            aria-label={tAssist("send")}
            className="shrink-0 rounded-full"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </Button>
        </form>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardContent className="p-4 lg:p-5">
            <h2 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
              {t("suggested")}
            </h2>
            <ul className="mt-3 space-y-2">
              {PROMPTS.map((prompt) => (
                <li key={prompt}>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void submit(t(prompt))}
                    className="w-full rounded-card border border-line px-4 py-3 text-left
                               transition-colors hover:border-accent-600 hover:text-accent-700
                               disabled:opacity-50"
                  >
                    {t(prompt)}
                  </button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 lg:p-5">
            <h2 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
              {tCommon("language")}
            </h2>
            <div className="mt-2">
              <LanguageSwitcher locale={locale} />
            </div>
            {/* The sentence that keeps the badge above honest. */}
            <p className="mt-3 text-sm text-ink-faint">{t("disclaimer")}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * The one next step the assistant proposed, as a button.
 *
 * The model names an action; this maps it to a screen that already exists. It never
 * executes anything — an assistant that could file for government credit on its own
 * reading of a sentence is not a feature, and the API deliberately returns a proposal
 * rather than performing a write.
 */
function ProposedAction({
  action,
  schemeCode,
}: {
  action: AssistantAction;
  schemeCode: string | null;
}) {
  const t = useTranslations("assistant");

  const href =
    action === "open_scheme" && schemeCode
      ? `/schemes/${schemeCode}`
      : action === "find_partners"
        ? schemeCode
          ? `/results/${schemeCode}/partners`
          : "/partners"
        : action === "start_application" && schemeCode
          ? `/apply/${schemeCode}`
          : action === "plan_repayment"
            ? "/calculator"
            : null;

  if (!href) return null;

  return (
    <div className="ml-11">
      <Link href={href} className="btn-primary text-base">
        {t(`action.${action}`)}
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
    </div>
  );
}
