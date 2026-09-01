"use client";

import { useEffect, useRef, useState } from "react";

import { apiBase } from "@/lib/apiBase";

/**
 * A text-only client for the SETU conversation, shaped like a chat thread.
 *
 * This exists to prove one architectural claim without needing a Meta account: the
 * conversation is not a property of the web app. Every message here goes to
 * `POST /api/v1/webhook/whatsapp`, which runs the same `handle_turn` the citizen app
 * calls — same rule engine, same six languages, same verdict.
 *
 * The segment counter is not decoration. Every Indic script forces UCS-2 encoding, where
 * an SMS segment is 70 characters against 160 for Latin, and the sender pays per segment.
 * Showing it here makes the cost of serving people in their own language visible at the
 * point where the messages are written, rather than on an invoice later.
 *
 * Under `/demo` and outside `[locale]`: this is a pitch tool, not a citizen surface.
 */
interface Turn {
  from: "citizen" | "setu";
  text: string;
  segments?: number;
  stage?: string;
}

const LANGUAGES = [
  { code: "hi", label: "हिन्दी" },
  { code: "en", label: "English" },
  { code: "mr", label: "मराठी" },
  { code: "bn", label: "বাংলা" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
] as const;

const OPENERS: Record<string, string> = {
  hi: "mujhe sabzi ka thela lagana hai",
  en: "i want to start a vegetable cart",
  mr: "mala bhaji cha thela lavaycha aahe",
  bn: "ami sobji bikri korte chai",
  ta: "enakku kaikari vandi vaikanum",
  te: "naaku kooragaya bandi pettali",
};

const API = () => apiBase();

/** A throwaway sender number. Generated on the client only — see below. */
function randomSender(): string {
  return "9198765" + Math.floor(10000 + Math.random() * 89999);
}

export default function WhatsAppSimulator() {
  const [language, setLanguage] = useState<string>("hi");
  // Empty until mounted, then filled in `useEffect`. A `useState` initialiser runs
  // during server rendering *and* again on the client, so seeding it with Math.random()
  // gives the two passes different numbers and React fails hydration on the mismatch.
  // Anything non-deterministic — random, Date.now, crypto — has to wait for the client.
  const [sender, setSender] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSender(randomSender());
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send(text: string) {
    // No sender before mount, and the API keys the conversation session off it.
    if (!text.trim() || busy || !sender) return;
    setTurns((prior) => [...prior, { from: "citizen", text }]);
    setDraft("");
    setBusy(true);
    setError(null);

    try {
      const response = await fetch(`${API()}/webhook/whatsapp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ simulate: true, sender, text, language }),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { detail?: string };
        setError(body.detail ?? `Request failed (${response.status})`);
        return;
      }
      const reply = (await response.json()) as {
        text: string;
        sms_segments: number;
        stage: string;
        language: string;
      };
      setLanguage(reply.language);
      setTurns((prior) => [
        ...prior,
        { from: "setu", text: reply.text, segments: reply.sms_segments, stage: reply.stage },
      ]);
    } catch {
      setError("Could not reach the SETU API. Is `docker compose up` running?");
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setTurns([]);
    setError(null);
    // A new sender means a new session; the old one is keyed by a hash of this string.
    setSender(randomSender());
  }

  const totalSegments = turns.reduce((sum, turn) => sum + (turn.segments ?? 0), 0);

  return (
    <main className="mx-auto max-w-lg px-4 py-6">
      <header>
        <h1 className="text-2xl font-semibold">SETU on a feature phone</h1>
        <p className="mt-1 text-base text-ink-muted">
          Every message below goes to the same <code>handle_turn</code> the citizen app
          uses. Same rule engine, same six languages, no smartphone.
        </p>
      </header>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <label className="text-base">
          <span className="sr-only">Language</span>
          <select
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            className="rounded-card border-2 border-line bg-surface px-3 py-2 text-base"
          >
            {LANGUAGES.map((entry) => (
              <option key={entry.code} value={entry.code}>
                {entry.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!sender}
          onClick={() => void send(OPENERS[language])}
          className="btn-secondary text-base disabled:opacity-50"
        >
          Start the demo
        </button>
        <button type="button" onClick={reset} className="btn-secondary text-base">
          New sender
        </button>
      </div>

      <div className="card mt-4 flex h-[26rem] flex-col overflow-y-auto p-4">
        {turns.length === 0 ? (
          <p className="m-auto max-w-xs text-center text-base text-ink-muted">
            Press &ldquo;Start the demo&rdquo;, or type anything a citizen might say.
          </p>
        ) : (
          <ul className="space-y-3">
            {turns.map((turn, index) => (
              <li
                key={index}
                className={turn.from === "citizen" ? "flex justify-end" : "flex justify-start"}
              >
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-card px-3 py-2 text-base ${
                    turn.from === "citizen"
                      ? "bg-accent-700 text-white"
                      : "border border-line bg-canvas"
                  }`}
                >
                  {turn.text}
                  {turn.segments !== undefined ? (
                    <span className="mt-1 block text-xs opacity-70">
                      {turn.stage} · {turn.segments} SMS segment
                      {turn.segments === 1 ? "" : "s"}
                    </span>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        <div ref={endRef} />
      </div>

      {error ? (
        <p role="alert" className="mt-3 rounded-card bg-stop-bg px-4 py-3 text-base text-stop-fg">
          {error}
        </p>
      ) : null}

      <form
        className="mt-3 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void send(draft);
        }}
      >
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Type a message"
          aria-label="Message"
          className="min-w-0 flex-1 rounded-card border-2 border-line bg-surface px-4 py-3 text-base"
        />
        <button type="submit" disabled={busy || !sender} className="btn-primary disabled:opacity-50">
          {busy ? "…" : "Send"}
        </button>
      </form>

      <p className="mt-3 text-sm text-ink-faint">
        Sender {sender || "…"} · {totalSegments} segment{totalSegments === 1 ? "" : "s"} billed so
        far. Indic scripts encode as UCS-2, where a segment is 70 characters rather than
        160 — the cost of answering someone in their own language, made visible.
      </p>
    </main>
  );
}
