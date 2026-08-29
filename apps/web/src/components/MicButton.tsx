"use client";

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
}: {
  locale: Locale;
  disabled?: boolean;
  onTranscript: (text: string) => void;
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
      className={`btn w-full text-xl ${
        listening
          ? "bg-stop-bg text-stop-fg ring-4 ring-stop-line"
          : "bg-accent-700 text-white hover:bg-accent-800"
      } disabled:opacity-50`}
    >
      <span aria-hidden="true" className="text-2xl">
        {listening ? "■" : "🎤"}
      </span>
      {listening ? t("listening") : t("speak")}
    </button>
  );
}
