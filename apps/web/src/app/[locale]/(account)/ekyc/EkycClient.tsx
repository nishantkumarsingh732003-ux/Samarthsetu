"use client";

/**
 * e-KYC liveness capture — four seconds of selfie video, on the citizen's own device.
 *
 * WHAT IS REAL HERE, because a screen that says "Verified" has to be able to say what it
 * verified. The camera is real `getUserMedia`. The clip is a real `MediaRecorder`
 * recording. The three checks reported are the three this device can actually make:
 * a live video track produced frames, the recorder ran for the expected duration, and
 * the resulting clip carried bytes. Each is measured, not animated.
 *
 * WHAT IS NOT DONE, said plainly and repeatedly on the page: nothing here compares the
 * face to an Aadhaar photograph. There is no UIDAI Aadhaar Face Auth integration behind
 * this product. `DbtCheckDialog` sets the precedent — it refuses to return a DBT status
 * it cannot look up, because a citizen who believes a government check passed will
 * present that belief at a counter and be turned away. A confidence percentage against
 * an Aadhaar record would be exactly that failure, so this screen does not show one.
 * It reports a completed capture, and names the integration that would be required.
 *
 * WHAT LEAVES THE DEVICE: nothing. The stream is previewed, the clip is held in memory,
 * and the blob is dropped as soon as its size has been read. No frame, clip, template or
 * descriptor is uploaded, and `lib/ekyc.ts` stores only flags. That is the whole reason
 * the feature can exist at all under CLAUDE.md rule 4.
 */

import {
  ArrowLeft,
  Camera,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Video,
  XCircle,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import {
  allChecksPassed,
  newReference,
  readEkyc,
  writeEkyc,
  type EkycChecks,
  type EkycRecord,
} from "@/lib/ekyc";

import type { Locale } from "@/i18n/config";

/** How long the clip runs. Four seconds is long enough to hold a face steady and short
 *  enough that nobody on a slow phone gives up halfway. */
const CLIP_SECONDS = 4;

type Stage = "idle" | "starting" | "ready" | "recording" | "checking" | "done" | "denied";

/** The three checks, in the order the panel reveals them. */
const CHECK_KEYS = ["cameraLive", "clipRecorded", "clipHasData"] as const;

export function EkycClient({ locale }: { locale: Locale }) {
  const t = useTranslations("ekyc");
  const tCommon = useTranslations("common");

  const [stage, setStage] = useState<Stage>("idle");
  const [existing, setExisting] = useState<EkycRecord | null>(null);
  const [checks, setChecks] = useState<Partial<EkycChecks>>({});
  const [result, setResult] = useState<EkycRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(CLIP_SECONDS);

  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);

  // A previous capture, if one still stands. Read in an effect, not in `useState`:
  // `localStorage` does not exist during the server render.
  useEffect(() => {
    setExisting(readEkyc());
  }, []);

  /** Release the camera. Called on every exit path — a live camera light left on after
   *  the citizen has finished is both a privacy problem and a battery one. */
  const stopCamera = useCallback(() => {
    recorder.current?.state === "recording" && recorder.current.stop();
    recorder.current = null;
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
  }, []);

  useEffect(() => stopCamera, [stopCamera]);

  const startCamera = useCallback(async () => {
    setError(null);
    setStage("starting");
    try {
      const media = await navigator.mediaDevices.getUserMedia({
        // `user` is the selfie camera. Audio is not requested: nothing here needs it, and
        // asking for a microphone the feature does not use is the data-minimisation
        // failure CLAUDE.md rule 4 exists to prevent.
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      stream.current = media;
      if (video.current) {
        video.current.srcObject = media;
        await video.current.play().catch(() => {});
      }
      setStage("ready");
    } catch {
      // Permission refused, no camera, or a browser that blocks it on an insecure
      // origin. All three are the same thing to the citizen: they cannot do this here.
      setStage("denied");
    }
  }, []);

  const record = useCallback(async () => {
    const media = stream.current;
    if (!media) return;

    setStage("recording");
    setChecks({});
    setCountdown(CLIP_SECONDS);

    // Check one, measured rather than assumed: a video track exists and is live.
    const track = media.getVideoTracks()[0];
    const cameraLive = Boolean(track && track.readyState === "live");

    const chunks: Blob[] = [];
    let clipRecorded = false;
    let bytes = 0;

    try {
      const rec = new MediaRecorder(media);
      recorder.current = rec;
      rec.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };

      const started = Date.now();
      const finished = new Promise<void>((resolve) => {
        rec.onstop = () => resolve();
      });

      rec.start();
      for (let left = CLIP_SECONDS; left > 0; left -= 1) {
        await new Promise((r) => setTimeout(r, 1000));
        setCountdown(left - 1);
      }
      rec.stop();
      await finished;

      // Check two: the recorder actually ran for about the expected time.
      clipRecorded = Date.now() - started >= (CLIP_SECONDS - 1) * 1000;
      // Check three: the clip carried data. Reading `.size` is the last thing done with
      // the blob — it is never uploaded, never stored, and goes out of scope here.
      bytes = chunks.reduce((total, chunk) => total + chunk.size, 0);
    } catch {
      // MediaRecorder is unavailable or refused the stream. The capture simply did not
      // succeed; nothing is written.
    } finally {
      recorder.current = null;
    }

    const measured: EkycChecks = { cameraLive, clipRecorded, clipHasData: bytes > 0 };

    // Reveal the checks one at a time. The pause is presentation, not computation — the
    // values above are already decided, so nothing here can change an outcome.
    setStage("checking");
    for (const key of CHECK_KEYS) {
      await new Promise((r) => setTimeout(r, 420));
      setChecks((current) => ({ ...current, [key]: measured[key] }));
    }

    stopCamera();

    if (!allChecksPassed(measured)) {
      setError(t("failedBody"));
      setStage("idle");
      return;
    }

    const record: Omit<EkycRecord, "simulated"> = {
      capturedAt: Date.now(),
      reference: newReference(),
      seconds: CLIP_SECONDS,
      checks: measured,
    };
    writeEkyc(record);
    setResult({ ...record, simulated: true });
    setExisting({ ...record, simulated: true });
    setStage("done");
  }, [stopCamera, t]);

  const readable = (at: number) =>
    new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(at));

  const showResult = stage === "done" ? result : stage === "idle" ? existing : null;

  return (
    <div className="space-y-5">
      <Link href="/profile" className="btn-quiet -ml-3 text-base">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        {t("back")}
      </Link>

      <header>
        {/* The badge says what this is before the heading does, because "e-KYC" on a page
            carrying a ministry's name reads as a government check unless told otherwise. */}
        <Chip tone="accent">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          {t("badge")}
        </Chip>
        <h1 className="mt-3 font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-2 max-w-2xl text-lg text-ink-muted">{t("sub")}</p>
      </header>

      {showResult ? (
        <Card>
          <CardContent className="p-5 lg:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <span
                  aria-hidden="true"
                  className="grid h-14 w-14 shrink-0 place-items-center rounded-card bg-good-bg"
                >
                  <ShieldCheck className="h-6 w-6 text-good-fg" />
                </span>
                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-good-fg">
                    {t("captureComplete")}
                  </p>
                  <p className="mt-1 font-display text-xl font-bold">
                    {t("capturedOn", { when: readable(showResult.capturedAt) })}
                  </p>
                  <p className="numeric mt-1 text-sm text-ink-faint">
                    {t("refLabel")} · {showResult.reference}
                  </p>
                </div>
              </div>
              <Button variant="secondary" onClick={startCamera}>
                <Camera className="h-4 w-4" aria-hidden="true" />
                {t("again")}
              </Button>
            </div>

            <ul className="mt-5 grid gap-x-8 gap-y-2.5 sm:grid-cols-2">
              {CHECK_KEYS.map((key) => (
                <li key={key} className="flex items-start gap-2.5 text-ink-muted">
                  <CheckCircle2
                    className="mt-0.5 h-4 w-4 shrink-0 text-good-fg"
                    aria-hidden="true"
                  />
                  {t(`check.${key}`)}
                </li>
              ))}
            </ul>

            {/* The sentence that keeps the card above honest. Not a footnote — it is the
                difference between "a capture was completed" and "a person was verified". */}
            <p className="mt-5 rounded-card bg-warn-bg px-4 py-3 text-sm text-warn-fg">
              {t("notVerified")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <Card>
            <CardContent className="p-0">
              <div className="relative aspect-[4/3] w-full overflow-hidden rounded-t-panel bg-[#0f172a]">
                <video
                  ref={video}
                  playsInline
                  muted
                  // Mirrored: an unmirrored selfie preview makes people move the wrong way.
                  className={`h-full w-full -scale-x-100 object-cover ${
                    stage === "ready" || stage === "recording" ? "" : "invisible"
                  }`}
                />

                {(stage === "ready" || stage === "recording") && (
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute left-1/2 top-1/2 h-[70%] w-[52%]
                               -translate-x-1/2 -translate-y-1/2 rounded-[50%]
                               border-[3px] border-dashed border-good-ring"
                  />
                )}

                {stage === "recording" && (
                  <span className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full bg-stop-fg px-3 py-1 text-sm font-semibold text-white">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-white" />
                    {t("rec", { seconds: countdown })}
                  </span>
                )}

                {(stage === "idle" || stage === "starting" || stage === "denied") && (
                  <div className="absolute inset-0 grid place-items-center p-6 text-center">
                    <div>
                      {stage === "denied" ? (
                        <XCircle className="mx-auto h-10 w-10 text-white/70" aria-hidden="true" />
                      ) : (
                        <Video className="mx-auto h-10 w-10 text-white/70" aria-hidden="true" />
                      )}
                      <p className="mt-3 font-display text-lg font-bold text-white">
                        {stage === "denied" ? t("deniedTitle") : t("readyTitle")}
                      </p>
                      <p className="mx-auto mt-1.5 max-w-sm text-white/70">
                        {stage === "denied" ? t("deniedBody") : t("readyBody")}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 lg:p-5">
                {stage === "ready" || stage === "recording" ? (
                  <Button
                    onClick={record}
                    disabled={stage === "recording"}
                    className="w-full bg-teal-700 hover:bg-teal-800"
                  >
                    {stage === "recording" ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        {t("recording")}
                      </>
                    ) : (
                      <>
                        <Video className="h-4 w-4" aria-hidden="true" />
                        {t("record", { seconds: CLIP_SECONDS })}
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    onClick={startCamera}
                    disabled={stage === "starting" || stage === "checking"}
                    className="w-full"
                  >
                    {stage === "starting" ? (
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <Camera className="h-4 w-4" aria-hidden="true" />
                    )}
                    {stage === "denied" ? t("retry") : t("start")}
                  </Button>
                )}

                {error && (
                  <p role="alert" className="mt-3 rounded-card bg-stop-bg px-4 py-3 text-stop-fg">
                    {error}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 lg:p-5">
              <h2 className="font-display text-lg font-bold">{t("checksHeading")}</h2>
              <ul className="mt-3 space-y-2" aria-live="polite">
                {CHECK_KEYS.map((key, index) => {
                  const state = checks[key];
                  const pending = stage === "checking" && state === undefined;
                  return (
                    <li
                      key={key}
                      className={`flex items-center gap-3 rounded-card border px-4 py-3 transition-colors duration-300 ${
                        state === true
                          ? "border-good-line bg-good-bg text-good-fg"
                          : state === false
                            ? "border-stop-fg/30 bg-stop-bg text-stop-fg"
                            : "border-line text-ink-muted"
                      }`}
                    >
                      {state === true ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
                      ) : state === false ? (
                        <XCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                      ) : pending ? (
                        <Loader2 className="h-4 w-4 shrink-0 animate-spin" aria-hidden="true" />
                      ) : (
                        <span
                          aria-hidden="true"
                          className="grid h-5 w-5 shrink-0 place-items-center rounded-full border border-line text-xs font-semibold"
                        >
                          {index + 1}
                        </span>
                      )}
                      <span className="min-w-0">{t(`check.${key}`)}</span>
                    </li>
                  );
                })}
              </ul>

              <p className="mt-4 text-sm text-ink-faint">{t("privacyNote")}</p>
              <p className="mt-3 rounded-card bg-warn-bg px-3 py-2.5 text-sm text-warn-fg">
                {t("notVerified")}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <p className="text-sm text-ink-faint">{tCommon("notOfficialShort")}</p>
    </div>
  );
}
