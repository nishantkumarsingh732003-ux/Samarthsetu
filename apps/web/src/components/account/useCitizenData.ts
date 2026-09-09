"use client";

/**
 * Fetch-once hooks for the signed-in pages.
 *
 * Deliberately small and deliberately not React Query. The account surface makes at most
 * three read calls per screen against an API that already caches the expensive one
 * (`/citizen/matches` is memoised server-side on a fingerprint of the profile plus the
 * engine version), so a client cache would be a second cache solving a problem the first
 * one already solved.
 *
 * Every hook returns the same triple — `data`, `loading`, `error` — because every page
 * has to render all three states, and a hook that returns only the happy path pushes
 * that decision into the JSX where it gets forgotten.
 */

import { useCallback, useEffect, useState } from "react";

import {
  getCatalogue,
  getMatches,
  getMyApplications,
  getMyNotifications,
} from "@/lib/citizenApi";

import type {
  AuthedResult,
  CitizenApplication,
  CitizenMatches,
  CitizenNotification,
  SchemeCatalogue,
} from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export type LoadError = "offline" | "server" | "notfound" | "unauthorised" | "conflict";

export interface LoadState<T> {
  data: T | null;
  loading: boolean;
  /** The typed failure, so a page can say "offline" differently from "server error". */
  error: LoadError | null;
  reload: () => void;
}

function useAsync<T>(fetcher: () => Promise<AuthedResult<T>>, deps: unknown[]): LoadState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<LoadError | null>(null);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((value) => value + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void fetcher().then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setData(result.data);
        setError(null);
      } else {
        // The last good data is kept on a failure. A citizen who loses signal mid-scroll
        // should keep reading what they already had rather than watch it vanish.
        setError(result.error);
      }
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
    // `fetcher` is a fresh closure every render by design; the caller's deps are the
    // contract for when a refetch is actually warranted.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { data, loading, error, reload };
}

export function useMatches(locale: Locale): LoadState<CitizenMatches> {
  return useAsync(() => getMatches(locale), [locale]);
}

export function useCatalogue(locale: Locale): LoadState<SchemeCatalogue> {
  return useAsync(() => getCatalogue(locale), [locale]);
}

export function useMyApplications(): LoadState<CitizenApplication[]> {
  return useAsync(() => getMyApplications(), []);
}

/** What the service has told this citizen. Read once per shell mount, which is once per
 *  full page load — the bell is not a poller, because a message that arrives while
 *  someone is reading is not urgent enough to spend their data plan on. */
export function useMyNotifications(): LoadState<CitizenNotification[]> {
  return useAsync(() => getMyNotifications(), []);
}
