"use client";

import { useEffect } from "react";

/**
 * Recover from a chunk that belongs to a build that no longer exists.
 *
 * THE FAILURE. Next splits the app into chunks whose names change every build. A tab that
 * was loaded from one build and then navigates client-side asks for a chunk by the name
 * that build gave it. If the server has since been rebuilt — a deploy in production, a
 * server restart in development — that name is gone, and the navigation dies with
 *
 *     ChunkLoadError: Loading chunk app/[locale]/(account)/schemes/page failed
 *
 * on a server that is serving correct files. Nothing is wrong with the app; the tab is
 * simply holding a map of a build that has been replaced.
 *
 * THE FIX, and why it is a reload rather than a retry. The page's whole module graph is
 * pinned to the old build id, so re-requesting one chunk cannot help — the document has
 * to be fetched again to pick up the new one. A single reload does exactly that, and the
 * citizen loses nothing: results, shortlist, the assistant thread and the e-KYC record all
 * live in `localStorage`, which survives it.
 *
 * WHY IT CANNOT LOOP. A reload that fails the same way would reload again forever, which
 * is worse than the error. So a marker is written to `sessionStorage` first, and a second
 * chunk error in the same tab is left alone to surface normally. The marker is cleared
 * once the page has loaded successfully, so a later deploy is still recovered from.
 *
 * `sessionStorage`, not `localStorage`: the guard is about this tab's current predicament,
 * and it should not persist into tomorrow's session.
 */

/** Set while a recovery reload is in flight. */
const GUARD = "setu.chunkReload.v1";

function isChunkError(value: unknown): boolean {
  const message =
    value instanceof Error
      ? `${value.name}: ${value.message}`
      : typeof value === "string"
        ? value
        : "";
  // Matches Next's own `ChunkLoadError`, and webpack's wording for a failed import.
  return /ChunkLoadError|Loading chunk .* failed|Loading CSS chunk .* failed/i.test(message);
}

export function ChunkReloader() {
  useEffect(() => {
    let guarded = false;
    try {
      guarded = window.sessionStorage.getItem(GUARD) === "1";
      // The page rendered, so whatever went wrong last time is behind us. Clearing here
      // rather than never means a deploy an hour from now is still recovered from.
      if (guarded) window.sessionStorage.removeItem(GUARD);
    } catch {
      // Blocked site data. Without a guard a reload could loop, so do not attempt one.
      return;
    }

    const recover = (reason: unknown) => {
      if (!isChunkError(reason)) return;
      try {
        if (window.sessionStorage.getItem(GUARD) === "1") return; // already tried
        window.sessionStorage.setItem(GUARD, "1");
      } catch {
        return;
      }
      window.location.reload();
    };

    const onError = (event: ErrorEvent) => recover(event.error ?? event.message);
    const onRejection = (event: PromiseRejectionEvent) => recover(event.reason);

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);

  return null;
}
