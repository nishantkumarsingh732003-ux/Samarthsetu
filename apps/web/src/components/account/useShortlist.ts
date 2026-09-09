"use client";

/**
 * The shortlist, as React sees it.
 *
 * Starts empty and fills in an effect, never from a `useState` initialiser. A client
 * component is still rendered on the server, where there is no `localStorage`, so
 * reading the store during the first pass makes the server HTML and the first client
 * HTML disagree — which is the exact class of bug `scripts/check-hydration.mjs` exists
 * to catch. `ready` distinguishes "we have not looked yet" from "we looked and it is
 * empty", so a bookmark button does not flash the wrong state on every navigation.
 *
 * Every mounted copy subscribes to the same change event, so the button on a scheme card
 * and the count in the sidebar move together without either owning the other.
 */

import { useCallback, useEffect, useState } from "react";

import {
  SHORTLIST_MAX,
  onShortlistChange,
  readShortlist,
  removeFromShortlist,
  toggleShortlist,
} from "@/lib/shortlist";

export interface Shortlist {
  codes: string[];
  /** False until the store has been read once on the client. */
  ready: boolean;
  has: (code: string) => boolean;
  toggle: (code: string) => void;
  remove: (code: string) => void;
  isFull: boolean;
}

export function useShortlist(): Shortlist {
  const [codes, setCodes] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setCodes(readShortlist());
    setReady(true);
    return onShortlistChange(() => setCodes(readShortlist()));
  }, []);

  const has = useCallback((code: string) => codes.includes(code), [codes]);

  // The store is the source of truth and it broadcasts, so these do not `setCodes`
  // themselves — the subscription above does, once, for every copy on the page.
  const toggle = useCallback((code: string) => void toggleShortlist(code), []);
  const remove = useCallback((code: string) => void removeFromShortlist(code), []);

  return { codes, ready, has, toggle, remove, isFull: codes.length >= SHORTLIST_MAX };
}
