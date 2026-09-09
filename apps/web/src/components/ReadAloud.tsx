"use client";

import { Square, Volume2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { LOCALE_NAMES, SPEECH_TAGS, type Locale } from "@/i18n/config";

/**
 * Text-to-speech on every result card.
 *
 * The audience explicitly includes people who do not read fluently, so a written
 * explanation alone does not reach them. Uses the platform speech synthesiser — no
 * network, no bundle cost — and hides itself entirely where that is unavailable rather
 * than offering a button that does nothing.
 *
 * Two shapes, one implementation. `icon` is the square button that sits in a row of card
 * actions. `full` is the labelled pill the scheme page uses, and it names the language it
 * will speak in — "Listen (हिन्दी)" — because the synthesiser reads in the page's
 * language, not the device's, and someone who has switched language needs to know that
 * before they tap. The name is always in its own script (`LOCALE_NAMES`).
 */
export function ReadAloud({
  text,
  locale,
  variant = "icon",
}: {
  text: string;
  locale: Locale;
  variant?: "icon" | "full";
}) {
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

  if (variant === "full") {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-pressed={speaking}
        className="btn-secondary shrink-0 rounded-full text-base"
      >
        {speaking ? (
          <Square className="h-4 w-4 fill-current" aria-hidden="true" />
        ) : (
          <Volume2 className="h-4 w-4" aria-hidden="true" />
        )}
        {speaking
          ? t("stopReading")
          : t("listenIn", { language: LOCALE_NAMES[locale] })}
      </button>
    );
  }

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
