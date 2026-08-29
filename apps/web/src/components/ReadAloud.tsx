"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { SPEECH_TAGS, type Locale } from "@/i18n/config";

/**
 * Text-to-speech on every result card.
 *
 * The audience explicitly includes people who do not read fluently, so a written
 * explanation alone does not reach them. Uses the platform speech synthesiser — no
 * network, no bundle cost — and hides itself entirely where that is unavailable rather
 * than offering a button that does nothing.
 */
export function ReadAloud({ text, locale }: { text: string; locale: Locale }) {
  const t = useTranslations("results");
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    setSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => window.speechSynthesis?.cancel();
  }, []);

  if (!supported) return null;

  const toggle = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = SPEECH_TAGS[locale];
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={speaking ? t("stopReading") : t("readAloud")}
      className="flex h-touch w-touch shrink-0 items-center justify-center rounded-card border-2 border-line text-xl"
    >
      <span aria-hidden="true">{speaking ? "■" : "🔊"}</span>
    </button>
  );
}
