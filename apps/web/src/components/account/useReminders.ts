"use client";

/**
 * The reminders, as React sees them. Mirrors `useShortlist` exactly.
 *
 * Starts empty and fills in an effect, never from a `useState` initialiser. A client
 * component is still rendered on the server, where there is no `localStorage`, so reading
 * the store during the first pass makes the server HTML and the first client HTML
 * disagree — the exact class of bug `scripts/check-hydration.mjs` exists to catch.
 */

import { useCallback, useEffect, useState } from "react";

import {
  clearReminder,
  onRemindersChange,
  readReminders,
  setReminder,
  type Reminders,
} from "@/lib/reminders";

export interface RemindersState {
  reminders: Reminders;
  /** False until the store has been read once on the client. */
  ready: boolean;
  get: (code: string) => string;
  set: (code: string, date: string) => void;
  clear: (code: string) => void;
}

export function useReminders(): RemindersState {
  const [reminders, setState] = useState<Reminders>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setState(readReminders());
    setReady(true);
    return onRemindersChange(() => setState(readReminders()));
  }, []);

  const get = useCallback((code: string) => reminders[code] ?? "", [reminders]);

  // The store is the source of truth and it broadcasts, so these do not `setState`
  // themselves — the subscription above does, once, for every copy on the page.
  const set = useCallback((code: string, date: string) => {
    setReminder(code, date);
  }, []);
  const clear = useCallback((code: string) => {
    clearReminder(code);
  }, []);

  return { reminders, ready, get, set, clear };
}
