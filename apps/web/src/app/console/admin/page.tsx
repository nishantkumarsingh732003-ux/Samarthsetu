"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { downloadCsv, getAnalytics, getUser, signOut, type Analytics } from "@/lib/console";

/**
 * The MoSJE dashboard.
 *
 * Every figure is computed from the database on load — no chart library, no fixture, no
 * cached snapshot. The bars are divs, which keeps the page dependency-free and means a
 * screen reader gets the number rather than a canvas it cannot describe.
 *
 * The section worth defending is **underserved districts**: places where citizens ran an
 * eligibility check and no authorised partner nearby can process what they matched. That
 * is a procurement decision, not a progress bar, and it is the one number here that
 * tells the ministry to do something rather than telling them how they are doing.
 */
function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function Bar({ share, tone = "bg-accent-600" }: { share: number; tone?: string }) {
  return (
    <div className="h-2 w-full rounded-full bg-line">
      <div className={`h-2 rounded-full ${tone}`} style={{ width: `${Math.round(share * 100)}%` }} />
    </div>
  );
}

export default function AdminConsole() {
  const router = useRouter();
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const result = await getAnalytics();
    if (!result.ok) {
      if (result.status === 401) {
        router.push("/console/login");
        return;
      }
      setError(result.error);
      return;
    }
    setData(result.data);
    setError(null);
  }, [router]);

  useEffect(() => {
    if (!getUser()) {
      router.push("/console/login");
      return;
    }
    void load();
  }, [load, router]);

  if (!data) {
    return (
      <main className="mx-auto max-w-console px-5 py-10">
        <p role="status" className="text-lg">
          {error ?? "Loading…"}
        </p>
      </main>
    );
  }

  const funnelMax = Math.max(...data.funnel.stages.map((s) => s.count), 1);
  const m = data.misrouting;

  return (
    <main className="mx-auto max-w-console px-5 py-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Scheme uptake</h1>
          <p className="mt-1 text-base text-ink-muted">
            Ministry of Social Justice &amp; Empowerment · rule engine{" "}
            {data.engine_version}
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void load()} className="btn-secondary">
            Refresh
          </button>
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
        </div>
      </header>

      {error ? (
        <p role="alert" className="mt-4 rounded-card bg-stop-bg px-4 py-3 text-base text-stop-fg">
          {error}
        </p>
      ) : null}

      {/* The primary KPI, stated first because it is the thing this service exists to
          change: applications that would have walked into the wrong counter. */}
      <section aria-labelledby="kpi-heading" className="panel mt-6 border-2 border-accent-600 p-5">
        <h2 id="kpi-heading" className="font-display text-lg font-bold">
          Misrouting prevented
        </h2>
        <p className="mt-2 text-4xl font-semibold text-accent-800">{m.total_prevented}</p>
        <p className="mt-1 text-base text-ink-muted">
          wrong-counter outcomes avoided across {m.routing_calls} routing decisions
        </p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
          {[
            ["Not authorised for the scheme, or paused", m.partners_filtered_for_authorisation],
            ["Beyond reach or outside service area", m.partners_filtered_for_distance],
            ["Wrong ticket size for that branch", m.partners_filtered_for_ticket_size],
            ["Sent to a better-fitting scheme", m.redirects_suggested],
          ].map(([label, value]) => (
            <div key={String(label)} className="border-t border-line pt-2">
              <dt className="text-base text-ink-muted">{label}</dt>
              <dd className="font-display text-xl font-bold tracking-tight">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="funnel-heading" className="panel mt-6 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="funnel-heading" className="font-display text-lg font-bold">
            From first question to sanction
          </h2>
          <button
            type="button"
            onClick={() => void downloadCsv("funnel")}
            className="btn-secondary text-base"
          >
            Export CSV
          </button>
        </div>
        {data.funnel.largest_drop_off ? (
          <p className="mt-2 rounded-card bg-warn-bg px-4 py-3 text-base text-warn-fg">
            Largest loss: {data.funnel.largest_drop_off} —{" "}
            {pct(data.funnel.largest_drop_off_pct)} of people did not continue.
          </p>
        ) : null}
        <ul className="mt-4 space-y-3">
          {data.funnel.stages.map((stage) => (
            <li key={stage.stage}>
              <div className="flex justify-between text-base">
                <span>{stage.label}</span>
                <span className="text-ink-muted">
                  {stage.count}
                  {stage.conversion_from_previous !== null
                    ? ` · ${pct(stage.conversion_from_previous)}`
                    : ""}
                </span>
              </div>
              <Bar share={stage.count / funnelMax} />
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="coverage-heading" className="panel mt-6 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="coverage-heading" className="font-display text-lg font-bold">
            Underserved districts
          </h2>
          <button
            type="button"
            onClick={() => void downloadCsv("underserved")}
            className="btn-secondary text-base"
          >
            Export CSV
          </button>
        </div>
        <p className="mt-1 text-base text-ink-muted">
          Districts where citizens checked eligibility but no authorised, accepting
          partner can process every scheme family. {data.coverage.districts_with_demand}{" "}
          district(s) show demand.
        </p>
        {data.coverage.underserved.length === 0 ? (
          <p className="mt-4 text-base">
            Every district with demand has an authorised partner for all three families.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-base">
              <thead className="text-sm text-ink-faint">
                <tr>
                  <th scope="col" className="py-2">District</th>
                  <th scope="col">Demand</th>
                  <th scope="col">Partners</th>
                  <th scope="col">Nearest (km)</th>
                  <th scope="col">Families unserved</th>
                </tr>
              </thead>
              <tbody>
                {data.coverage.underserved.map((row) => (
                  <tr key={`${row.district}-${row.state}`} className="border-t border-line">
                    <td className="py-2">
                      {row.district}
                      <span className="text-ink-faint">, {row.state}</span>
                    </td>
                    <td>{row.demand}</td>
                    <td>{row.partners_within_25km}</td>
                    <td>{row.nearest_authorised_km ?? "—"}</td>
                    <td className="text-ink-muted">
                      {row.families_unserved.join(", ").replaceAll("_", " ").toLowerCase() || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        {(
          [
            ["Scheme mix", data.scheme_mix, "scheme_mix"],
            ["Language of service", data.language_mix, "language_mix"],
            ["Application status", data.status_mix, "status_mix"],
          ] as const
        ).map(([title, rows, section]) => (
          <section key={section} className="panel p-5" aria-label={title}>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-lg font-bold">{title}</h2>
              <button
                type="button"
                onClick={() => void downloadCsv(section)}
                className="text-base text-accent-700 underline"
              >
                CSV
              </button>
            </div>
            {rows.length === 0 ? (
              <p className="mt-3 text-base text-ink-muted">Nothing recorded yet.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {rows.map((row) => (
                  <li key={row.key}>
                    <div className="flex justify-between text-base">
                      <span>{row.label}</span>
                      <span className="text-ink-muted">
                        {row.count} · {pct(row.share)}
                      </span>
                    </div>
                    <Bar share={row.share} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}

        <section className="panel p-5" aria-label="Turnaround by partner type">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-lg font-bold">Turnaround by partner type</h2>
            <button
              type="button"
              onClick={() => void downloadCsv("turnaround")}
              className="text-base text-accent-700 underline"
            >
              CSV
            </button>
          </div>
          {data.turnaround.length === 0 ? (
            <p className="mt-3 text-base text-ink-muted">
              No application has moved past submission yet.
            </p>
          ) : (
            <table className="mt-3 w-full text-left text-base">
              <thead className="text-sm text-ink-faint">
                <tr>
                  <th scope="col" className="py-1">Type</th>
                  <th scope="col">Cases</th>
                  <th scope="col">Median</th>
                  <th scope="col">p90</th>
                </tr>
              </thead>
              <tbody>
                {data.turnaround.map((row) => (
                  <tr key={row.partner_type} className="border-t border-line">
                    <td className="py-1">{row.partner_type}</td>
                    <td>{row.applications}</td>
                    <td>{row.median_days ?? "—"}d</td>
                    <td>{row.p90_days ?? "—"}d</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      <p className="mt-6 text-sm text-ink-faint">
        Computed live from the database at {new Date(data.generated_at).toLocaleString()}.
        Channel Partner records are synthetic pending the official MoSJE partner master.
      </p>
    </main>
  );
}
