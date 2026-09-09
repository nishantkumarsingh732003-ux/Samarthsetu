"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  actOnApplication,
  getCapacity,
  getQueue,
  getUser,
  setCapacity,
  signOut,
  type CapacityResponse,
  type QueueItem,
  type QueueResponse,
} from "@/lib/console";

/**
 * The branch officer's queue.
 *
 * Ordered so the officer can answer "what should I pick up next?" without opening
 * anything: readiness and SLA are on the row, and the reason the router sent this
 * application here is one click away with the rule IDs attached. An officer who can see
 * *why* a case landed on their desk can push back when it should not have.
 */
const SLA_TONE: Record<string, string> = {
  ON_TRACK: "bg-good-bg text-good-fg",
  DUE: "bg-warn-bg text-warn-fg",
  BREACHED: "bg-stop-bg text-stop-fg",
  UNKNOWN: "bg-line/40 text-ink-muted",
};

const ACTIONS: { key: string; label: string; needsReason: boolean }[] = [
  { key: "ACKNOWLEDGE", label: "Accept", needsReason: false },
  { key: "REQUEST_DOCS", label: "Request documents", needsReason: true },
  { key: "APPRAISE", label: "Start appraisal", needsReason: false },
  { key: "SANCTION", label: "Sanction", needsReason: false },
  { key: "DISBURSE", label: "Mark disbursed", needsReason: false },
  { key: "REJECT", label: "Reject", needsReason: true },
];

function rupees(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
}

export default function PartnerConsole() {
  const router = useRouter();
  const [queue, setQueue] = useState<QueueResponse | null>(null);
  const [capacity, setCapacityState] = useState<CapacityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  const load = useCallback(async () => {
    const [q, c] = await Promise.all([getQueue(filter || undefined), getCapacity()]);
    if (!q.ok) {
      if (q.status === 401) {
        router.push("/console/login");
        return;
      }
      setError(q.error);
      return;
    }
    setQueue(q.data);
    if (c.ok) setCapacityState(c.data);
    setError(null);
  }, [filter, router]);

  useEffect(() => {
    if (!getUser()) {
      router.push("/console/login");
      return;
    }
    void load();
  }, [load, router]);

  async function act(item: QueueItem, action: string, needsReason: boolean) {
    if (needsReason && !reason.trim()) {
      setError("Requesting documents or rejecting needs a reason the citizen can act on.");
      return;
    }
    setBusy(item.reference_no);
    const result = await actOnApplication(item.reference_no, action, reason.trim() || undefined);
    setBusy(null);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setReason("");
    setError(null);
    await load();
  }

  async function toggleScheme(schemeCode: string, accepting: boolean) {
    setBusy(schemeCode);
    const result = await setCapacity({
      scheme_code: schemeCode,
      is_currently_accepting: accepting,
    });
    setBusy(null);
    if (result.ok) setCapacityState(result.data);
    else setError(result.error);
  }

  if (!queue) {
    return (
      <main className="mx-auto max-w-console px-5 py-10">
        <p role="status" className="text-lg">
          {error ?? "Loading…"}
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-console px-5 py-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight">{queue.partner_name}</h1>
          <p className="mt-1 text-base text-ink-muted">
            {queue.total} application{queue.total === 1 ? "" : "s"} routed here
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            signOut();
            router.push("/console/login");
          }}
          className="btn-secondary"
        >
          Sign out
        </button>
      </header>

      {error ? (
        <p role="alert" className="mt-4 rounded-card bg-stop-bg px-4 py-3 text-base text-stop-fg">
          {error}
        </p>
      ) : null}

      {/* Capacity. Writes to the same table the routing engine filters on, so pausing
          here removes this branch from citizen routing on the next call. */}
      {capacity ? (
        <section aria-labelledby="capacity-heading" className="panel mt-6 p-5">
          <h2 id="capacity-heading" className="font-display text-lg font-bold">
            Intake capacity
          </h2>
          <p className="mt-1 text-base text-ink-muted">
            Pausing a scheme removes this branch from citizen routing immediately, and
            tells anyone nearby exactly why.
          </p>
          <ul className="mt-4 space-y-3">
            {capacity.rows.map((row) => (
              <li
                key={row.scheme_code}
                className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3"
              >
                <div>
                  <p className="text-base font-medium">{row.scheme_name}</p>
                  <p className="text-sm text-ink-faint">
                    Up to Rs {rupees(row.max_ticket)} · {row.avg_turnaround_days ?? "—"} day
                    turnaround · {row.active_load ?? 0}% busy
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busy === row.scheme_code}
                  onClick={() => toggleScheme(row.scheme_code, !row.is_currently_accepting)}
                  aria-pressed={row.is_currently_accepting}
                  className={
                    row.is_currently_accepting
                      ? "btn-secondary border-good-line text-good-fg"
                      : "btn-secondary border-stop-line text-stop-fg"
                  }
                >
                  {row.is_currently_accepting ? "Accepting" : "Paused"}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section aria-labelledby="queue-heading" className="mt-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="queue-heading" className="font-display text-lg font-bold">
            Queue
          </h2>
          <label className="text-base">
            <span className="sr-only">Filter by status</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="rounded-card border-2 border-line bg-surface px-3 py-2 text-base"
            >
              <option value="">All statuses</option>
              {Object.keys(queue.counts_by_status).map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ").toLowerCase()} ({queue.counts_by_status[status]})
                </option>
              ))}
            </select>
          </label>
        </div>

        {queue.items.length === 0 ? (
          <p className="panel mt-4 p-5 text-lg">Nothing in this view.</p>
        ) : (
          <ul className="mt-4 space-y-4">
            {queue.items.map((item) => (
              <li key={item.reference_no}>
                <article className="panel p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-mono text-base font-semibold">{item.reference_no}</p>
                      <p className="mt-1 text-lg">{item.scheme_name}</p>
                      <p className="text-base text-ink-muted">
                        {item.applicant.display_name ?? "Name withheld"} ·{" "}
                        {item.applicant.district ?? "—"} · Rs {rupees(item.amount_requested)}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-block rounded-full px-3 py-1 text-sm ${SLA_TONE[item.sla_state]}`}
                      >
                        {item.days_open}d open
                        {item.sla_days ? ` of ${item.sla_days}` : ""}
                      </span>
                      <p className="mt-1 text-sm text-ink-faint">
                        {item.status.replaceAll("_", " ").toLowerCase()}
                      </p>
                    </div>
                  </div>

                  {/* The privacy posture, visible at the counter: SamarthSetu never held the
                      full number, so the branch does KYC with the document in hand. */}
                  <p className="mt-3 text-sm text-ink-faint">
                    {item.applicant.gov_id_type ?? "ID"} ····{" "}
                    {item.applicant.gov_id_last4 ?? "????"} · phone ····{" "}
                    {item.applicant.phone_last4 ?? "????"} · verify in person
                  </p>

                  <div className="mt-4">
                    <div className="flex items-center justify-between text-base">
                      <span>Documents</span>
                      <span className="text-ink-muted">
                        {item.readiness.uploaded} of {item.readiness.required}
                      </span>
                    </div>
                    <div
                      role="meter"
                      aria-valuenow={Math.round(item.readiness.score * 100)}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Document readiness"
                      className="mt-1 h-2 w-full rounded-full bg-line"
                    >
                      <div
                        className="h-2 rounded-full bg-accent-600"
                        style={{ width: `${Math.round(item.readiness.score * 100)}%` }}
                      />
                    </div>
                    {item.readiness.missing.length > 0 ? (
                      <p className="mt-2 text-sm text-ink-muted">
                        Missing: {item.readiness.missing.join(", ")}
                      </p>
                    ) : null}
                    {item.readiness.unmasked_documents > 0 ? (
                      <p className="mt-1 text-sm text-warn-fg">
                        {item.readiness.unmasked_documents} ID document could not be masked
                        automatically — check it yourself.
                      </p>
                    ) : null}
                  </div>

                  <button
                    type="button"
                    onClick={() => setOpen(open === item.reference_no ? null : item.reference_no)}
                    aria-expanded={open === item.reference_no}
                    className="btn-secondary mt-4 w-full text-base"
                  >
                    Why was this routed here?
                  </button>

                  {open === item.reference_no ? (
                    <div className="mt-3 rounded-card bg-canvas p-4">
                      <p className="text-base">
                        Rule engine {item.engine_version} returned{" "}
                        <strong>{item.verdict ?? "no recorded verdict"}</strong>
                      </p>
                      <ul className="mt-2 space-y-1">
                        {item.matched_because.map((r) => (
                          <li key={r.rule_id} className="text-base">
                            <code className="rounded bg-line/60 px-1.5 py-0.5 text-xs">
                              {r.rule_id}
                            </code>{" "}
                            {r.message}
                          </li>
                        ))}
                      </ul>

                      <label className="mt-4 block">
                        <span className="text-base">Reason (needed to reject or ask for documents)</span>
                        <textarea
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                          rows={2}
                          className="mt-1 w-full rounded-card border-2 border-line bg-surface px-3 py-2 text-base"
                        />
                      </label>

                      <div className="mt-3 flex flex-wrap gap-2">
                        {ACTIONS.map((action) => (
                          <button
                            key={action.key}
                            type="button"
                            disabled={busy === item.reference_no}
                            onClick={() => act(item, action.key, action.needsReason)}
                            className="btn-secondary text-base disabled:opacity-50"
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </article>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
