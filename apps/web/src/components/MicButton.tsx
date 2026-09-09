"use client";

import { Mic, Square } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { SPEECH_TAGS, type Locale } from "@/i18n/config";

/**
 * Voice input via the Web Speech API, with typing always available beside it.
 *
 * Speech recognition is not present on every browser and is unreliable on a cheap
 * Android phone, so it is treated as an enhancement: if it is missing the button says
 * so plainly and the typed field carries the whole flow. It is never the only way in.
 */

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

function getRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export function MicButton({
  locale,
  disabled,
  onTranscript,
  variant = "full",
}: {
  locale: Locale;
  disabled?: boolean;
  onTranscript: (text: string) => void;
  /**
   * `full` is the wide labelled control on the anonymous intake, where speaking is the
   * primary way in and the button has the screen to say so. `icon` is the round one that
   * sits beside a chat composer, where the text field is the primary control and a
   * full-width bar would crush it.
   */
  variant?: "full" | "icon";
}) {
  const t = useTranslations("assist");
  const a11y = useTranslations("a11y");
  const [supported, setSupported] = useState<boolean | null>(null);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    setSupported(getRecognition() !== null);
    return () => recognitionRef.current?.stop();
  }, []);

  const start = useCallback(() => {
    const recognition = getRecognition();
    if (!recognition) return;
    recognitionRef.current = recognition;
    recognition.lang = SPEECH_TAGS[locale];
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const text = event.results?.[0]?.[0]?.transcript ?? "";
      if (text) onTranscript(text);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    setListening(true);
    recognition.start();
  }, [locale, onTranscript]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  if (supported === false) {
    // Beside a composer there is nothing to explain — the text field is right there, and
    // a sentence about a missing microphone would push it off the row.
    if (variant === "icon") return null;
    return (
      <p className="rounded-card bg-accent-50 px-4 py-3 text-base text-ink-muted">
        {t("micUnavailable")}
      </p>
    );
  }

  return (
    <button
      type="button"
      onClick={listening ? stop : start}
      disabled={disabled || supported === null}
      aria-pressed={listening}
      aria-label={listening ? a11y("micButtonStop") : a11y("micButton")}
      className={`btn disabled:opacity-50 ${
        variant === "icon"
          ? "w-touch shrink-0 rounded-full px-0 text-xl"
          : "w-full text-xl"
      } ${
        listening
          ? "bg-stop-bg text-stop-fg ring-4 ring-stop-line"
          : variant === "icon"
            ? "border-2 border-line bg-surface text-ink hover:border-accent-600"
            : "bg-accent-700 text-white hover:bg-accent-800"
      }`}
    >
      {/* Lucide, not the 🎤 and ■ characters this used to draw. An emoji renders in the
          system's own font — a different shape, weight and colour on every phone, and on
          Android often a full-colour cartoon next to a page of flat navy icons. The rest
          of the app is lucide; so is this. */}
      {listening ? (
        <Square
          className={variant === "icon" ? "h-4 w-4 fill-current" : "h-5 w-5 fill-current"}
          aria-hidden="true"
        />
      ) : (
        <Mic
          className={variant === "icon" ? "h-4 w-4" : "h-5 w-5"}
          aria-hidden="true"
        />
      )}
      {variant === "full" && (listening ? t("listening") : t("speak"))}
    </button>
  );
}
