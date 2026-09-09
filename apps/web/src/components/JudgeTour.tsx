"use client";

/**
 * Mounts the walkthrough on every localised page, and costs almost nothing until it runs.
 *
 * This wrapper is all that ships in the shared bundle: a `sessionStorage` read and a
 * subscription. The card, its icons and its copy live behind `next/dynamic`, so the
 * anonymous journey — the one under the 200KB budget in scripts/check-bundle.mjs, walked
 * by a citizen on 2G who will never press the judge button — never downloads them.
 *
 * The step is read in an effect rather than in the `useState` initialiser: storage does
 * not exist during the server render, and an initialiser that read it would render a
 * different tree on the server than on the client. See scripts/check-hydration.mjs.
 */

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { onTourChange, readTourStep } from "@/lib/judgeTour";

const JudgeTourCard = dynamic(
  () => import("@/components/JudgeTourCard").then((m) => m.JudgeTourCard),
  { ssr: false },
);

export function JudgeTour() {
  const [step, setStep] = useState<number | null>(null);

  useEffect(() => {
    setStep(readTourStep());
    return onTourChange(() => setStep(readTourStep()));
  }, []);

  if (step === null) return null;
  return <JudgeTourCard step={step} />;
}
