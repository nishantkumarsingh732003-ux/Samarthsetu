"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { signIn } from "@/lib/console";

/**
 * One sign-in form for both consoles; the role in the response decides where you land.
 *
 * The demo credentials are printed on the page. That is a deliberate choice for a
 * hackathon build with synthetic data and no real citizen in the database — a judge
 * should be signed in within ten seconds. It is also exactly the thing to delete first
 * in anything resembling a deployment, which is why it is one obviously-labelled block
 * rather than something woven through the form.
 */
const DEMO = [
  { role: "Ministry analyst", email: "admin@setu.gov.in", lands: "/console/admin" },
  { role: "Branch officer", email: "partner@setu.gov.in", lands: "/console/partner" },
];

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    const result = await signIn(email.trim().toLowerCase(), password);
    if (!result.ok) {
      setBusy(false);
      setError(result.error);
      return;
    }
    if (result.data.role === "ADMIN") router.push("/console/admin");
    else if (result.data.role === "PARTNER") router.push("/console/partner");
    else setError("This account has no console. The citizen service needs no sign-in.");
    setBusy(false);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
      <h1 className="font-display text-2xl font-extrabold tracking-tight">SamarthSetu console</h1>
      <p className="mt-1 text-base text-ink-muted">
        For Channel Partners and the Ministry. Citizens do not need an account.
      </p>

      <form onSubmit={submit} className="panel mt-6 space-y-4 p-5">
        <label className="block">
          <span className="text-base">Email</span>
          <input
            type="email"
            required
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-lg"
          />
        </label>

        <label className="block">
          <span className="text-base">Password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-card border-2 border-line bg-surface px-4 py-3 text-lg"
          />
        </label>

        {error ? (
          <p role="alert" className="text-base text-warn-fg">
            {error}
          </p>
        ) : null}

        <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-50">
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <section className="mt-6 rounded-card border-2 border-dashed border-line p-4">
        <h2 className="text-base font-semibold">Demo accounts</h2>
        <p className="mt-1 text-sm text-ink-faint">
          Synthetic data only. Remove this block before any real deployment.
        </p>
        <ul className="mt-3 space-y-2 text-sm">
          {DEMO.map((account) => (
            <li key={account.email}>
              <button
                type="button"
                onClick={() => {
                  setEmail(account.email);
                  setPassword("setu-demo-2026");
                }}
                className="text-left text-accent-700 underline"
              >
                {account.role} — {account.email}
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-sm text-ink-faint">Password: setu-demo-2026</p>
      </section>
    </main>
  );
}
