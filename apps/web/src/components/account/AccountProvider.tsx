"use client";

/**
 * Who is signed in, for the pages that care.
 *
 * The account is optional throughout. `status` distinguishes the three states a page
 * actually has to render differently — `loading` (we have a token and are checking it),
 * `anonymous` (no token, or one the API rejected), `signed-in` — and a page that treats
 * `loading` as `anonymous` will flash the sign-in screen at a returning citizen on every
 * navigation, which on a slow connection is most of them.
 *
 * There is no route-level auth guard anywhere in this app, and that is deliberate. The
 * API decides; the client only decides what to draw. A citizen who *arrives* at
 * /dashboard without a token is shown the sign-in prompt rather than redirected, because
 * a redirect loses where they were going and, on this audience's connection, costs
 * another round trip to find out.
 *
 * SIGNING OUT IS THE ONE CASE THAT DOES NAVIGATE, and for the opposite reason. Clearing
 * the token in place left the citizen on /dashboard or /profile reading "Sign in to see
 * this" — the URL still naming a page they had just chosen to leave, and the Back button
 * walking them into more of the same. There is nothing to preserve about where they were:
 * leaving was the request. So it goes to the landing page, which is also the honest
 * answer to "what can I still do?" — the whole eligibility journey works from there with
 * no account at all. `replace`, not `push`, so Back does not return to the wall.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { useRouter } from "@/i18n/navigation";
import {
  getAccount,
  loadDemoProfile,
  readToken,
  saveProfile,
  signIn as apiSignIn,
  signOut as apiSignOut,
  signUp as apiSignUp,
} from "@/lib/citizenApi";

import { writeTourStep } from "@/lib/judgeTour";

import type { AuthedResult, CitizenAccount, CitizenProfile } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

type Status = "loading" | "anonymous" | "signed-in";

interface AccountContext {
  status: Status;
  account: CitizenAccount | null;
  signIn: (email: string, password: string) => Promise<AuthedResult<CitizenAccount>>;
  signUp: (input: {
    email: string;
    password: string;
    displayName: string;
    language: Locale;
  }) => Promise<AuthedResult<CitizenAccount>>;
  signOut: () => void;
  updateProfile: (
    patch: Partial<Record<keyof CitizenProfile, unknown>> & { completed?: boolean },
  ) => Promise<AuthedResult<CitizenAccount>>;
  loadDemo: () => Promise<AuthedResult<CitizenAccount>>;
}

const Context = createContext<AccountContext | null>(null);

export function AccountProvider({ children }: { children: React.ReactNode }) {
  const [account, setAccount] = useState<CitizenAccount | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const router = useRouter();

  useEffect(() => {
    // Reading localStorage during render would differ between the server pass and the
    // first client pass and produce a hydration mismatch, so it happens in an effect.
    if (!readToken()) {
      setStatus("anonymous");
      return;
    }
    let cancelled = false;
    void getAccount().then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setAccount(result.data);
        setStatus("signed-in");
        return;
      }
      // A rejected token is cleared; a network failure is not. Signing someone out
      // because their bus went through a tunnel is the wrong response.
      if (result.error === "unauthorised") apiSignOut();
      setStatus("anonymous");
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const adopt = useCallback((result: AuthedResult<CitizenAccount>) => {
    if (result.ok) {
      setAccount(result.data);
      setStatus("signed-in");
    }
    return result;
  }, []);

  const value = useMemo<AccountContext>(
    () => ({
      status,
      account,
      signIn: (email, password) => apiSignIn(email, password).then(adopt),
      signUp: (input) => apiSignUp(input).then(adopt),
      signOut: () => {
        apiSignOut();
        setAccount(null);
        setStatus("anonymous");
        // A walkthrough halfway through the signed-in screens has nothing left to show.
        writeTourStep(null);
        router.replace("/");
      },
      updateProfile: (patch) => saveProfile(patch).then(adopt),
      loadDemo: () => loadDemoProfile().then(adopt),
    }),
    [account, adopt, router, status],
  );

  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useAccount(): AccountContext {
  const context = useContext(Context);
  if (context === null) {
    throw new Error("useAccount must be used inside an <AccountProvider>.");
  }
  return context;
}
