"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiBase, apiOrigin } from "@/lib/apiBase";

/**
 * Mission control for a live demo.
 *
 * The problem this solves is not technical. It is that six minutes in front of a jury is
 * the worst possible time to be typing a profile into a form, remembering which income
 * figure triggers the redirect, or discovering that the screen you wanted is three clicks
 * away. Every scenario here is one click, runs against the local API, and carries the
 * sentence to say while it loads.
 *
 * Three rules it holds to:
 *
 *   - **Nothing external.** Every call goes to the local API. No model, no network, no
 *     third party is required for any scenario to complete.
 *   - **Nothing random.** The profiles are fixed constants, so the same numbers appear
 *     every rehearsal and on the day.
 *   - **Nothing destructive.** There is deliberately no "reset the database" button.
 *     Adding a destructive HTTP endpoint to a government-adjacent service to save one
 *     terminal command is the wrong trade, so the command is shown instead. The
 *     scenarios are independent and idempotent, so they do not need it: the read-only
 *     ones write nothing, and the conversational one starts a fresh session each time.
 *
 * **This route must not be deployed.** The analytics scenario signs in with the seeded
 * admin credentials from client-side code, which puts an admin password in the page
 * source. That is acceptable for a laptop demo over synthetic data and unacceptable
 * anywhere else, so `/demo` is on the removal checklist in docs/DEPLOYMENT.md — beside
 * the demo-credentials block on the sign-in page, which has the same problem.
 */
const API = () => apiBase();

interface Reason {
  rule_id: string;
  message: string;
}
interface FitComponent {
  key: string;
  score: number;
  detail: string;
}
interface SchemeResult {
  scheme_code: string;
  official_name: string;
  verdict: string;
  rank: number;
  indicative_amount: number | null;
  redirect_suggestion: string | null;
  matched_because: Reason[];
  blocked_because: Reason[];
  missing_fields: string[];
  fit: { total: number; components: FitComponent[] } | null;
}

type Line = { label: string; value: string; tone?: "good" | "warn" | "stop" | "plain" };
type Panel = { title: string; lines: Line[]; note?: string };

const PROFILES = {
  sunita: {
    category: "SC",
    project_sector: "TRADE",
    occupation_type: "Vegetable vendor",
    annual_family_income: 180000,
    project_cost: 80000,
  },
  ramesh: {
    category: "SC",
    project_sector: "MANUFACTURING",
    occupation_type: "Furniture workshop",
    annual_family_income: 420000,
    project_cost: 1200000,
  },
  // Income far above the Rs 5,00,000 ceiling: every scheme must refuse, with a reason.
  overCeiling: {
    category: "SC",
    project_sector: "TRADE",
    annual_family_income: 5000000,
    project_cost: 80000,
  },
  // Deliberately sparse, so the engine asks rather than guesses.
  sparse: { project_sector: "TRADE" },
} as const;

const LANGUAGES = [
  ["hi", "हिन्दी"],
  ["mr", "मराठी"],
  ["bn", "বাংলা"],
  ["ta", "தமிழ்"],
  ["te", "తెలుగు"],
  ["en", "English"],
] as const;

async function call<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API()}${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return (await response.json()) as T;
}

const rupees = (n: number) => new Intl.NumberFormat("en-IN").format(Math.round(n));

interface Scenario {
  id: string;
  title: string;
  proves: string;
  say: string;
  run?: () => Promise<Panel>;
  open?: { href: string; label: string };
  command?: string;
}

export default function DemoConsole() {
  const [ready, setReady] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");
  const [active, setActive] = useState<string | null>(null);
  const [panel, setPanel] = useState<Panel | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${apiOrigin()}/readyz`)
      .then((r) => r.json())
      .then((d) => {
        setReady(d.checks);
        setHealth("up");
      })
      .catch(() => setHealth("down"));
  }, []);

  const launch = useCallback(async (scenario: Scenario) => {
    if (!scenario.run) return;
    setActive(scenario.id);
    setPanel(null);
    setError(null);
    try {
      setPanel(await scenario.run());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reach the SETU API.");
    } finally {
      setActive(null);
    }
  }, []);

  const scenarios: Scenario[] = [
    {
      id: "eligible",
      title: "An eligible citizen",
      proves: "Every reason carries a rule ID, and the ranking explains itself.",
      say: "Sunita sells vegetables in Nagpur and needs eighty thousand rupees. Every line here traces to a rule in a YAML file with a source URL.",
      run: async () => {
        const d = await call<{ results: SchemeResult[]; engine_version: string }>("/match", {
          profile: PROFILES.sunita,
          language: "en",
        });
        const top = d.results[0];
        return {
          title: `${top.official_name} — ${top.verdict}`,
          lines: [
            { label: "Fit", value: `${top.fit?.total ?? "—"} / 100`, tone: "good" },
            {
              label: "Indicative",
              value: top.indicative_amount ? `Rs ${rupees(top.indicative_amount)}` : "—",
            },
            ...top.matched_because.map((r) => ({
              label: r.rule_id,
              value: r.message,
              tone: "good" as const,
            })),
            ...(top.fit?.components ?? []).map((c) => ({
              label: c.key.replace(/_/g, " "),
              value: `${Math.round(c.score)} — ${c.detail}`,
            })),
          ],
          note: `Engine ${d.engine_version}. No model was consulted for this verdict.`,
        };
      },
      open: { href: "/en/assist", label: "Open the citizen app" },
    },
    {
      id: "ineligible",
      title: "An ineligible citizen",
      proves: "A refusal always says why, and is never hidden.",
      say: "Income of fifty lakh, far above the five-lakh ceiling. We show the refusal rather than hiding it — a citizen told nothing assumes we never considered them.",
      run: async () => {
        const d = await call<{ results: SchemeResult[] }>("/match", {
          profile: PROFILES.overCeiling,
          language: "en",
        });
        return {
          title: "All three schemes refused",
          lines: d.results.map((r) => ({
            label: r.official_name,
            value: r.blocked_because[0]?.message ?? r.verdict,
            tone: "stop" as const,
          })),
          note: "Every refusal names the rule that produced it.",
        };
      },
    },
    {
      id: "need-more",
      title: "Not enough information yet",
      proves: "Unknown is not the same as no. The engine asks instead of refusing.",
      say: "We know almost nothing about this person. A naive system would reject them. Three-valued logic returns NEED MORE INFO and the single next question worth asking.",
      run: async () => {
        const d = await call<{
          results: SchemeResult[];
          next_question: { field: string; question_i18n: Record<string, string> } | null;
        }>("/match", { profile: PROFILES.sparse, language: "en" });
        return {
          title: d.results[0].verdict,
          lines: [
            {
              label: "Next question",
              value: d.next_question?.question_i18n.en ?? "—",
              tone: "warn",
            },
            { label: "Field", value: d.next_question?.field ?? "—" },
            {
              label: "Still missing",
              value: d.results[0].missing_fields.join(", ") || "—",
            },
          ],
          note: "A hard-block rule referencing an unknown field never becomes a refusal.",
        };
      },
    },
    {
      id: "redirect",
      title: "The wrong scheme, redirected",
      proves: "The anti-misrouting claim, in four seconds.",
      say: "Ramesh asked about the scheme everyone has heard of, with a twelve-lakh workshop. The engine tells him it does not fit and names the one that does — before he goes anywhere near a branch.",
      run: async () => {
        const d = await call<{ results: SchemeResult[] }>("/match", {
          profile: PROFILES.ramesh,
          language: "en",
        });
        const redirected = d.results.find((r) => r.redirect_suggestion);
        const top = d.results[0];
        return {
          title: `Asked about Micro Finance → sent to ${top.official_name}`,
          lines: [
            { label: "Matched", value: `${top.official_name} (${top.verdict})`, tone: "good" },
            {
              label: "Refused",
              value: redirected?.blocked_because[0]?.message ?? "—",
              tone: "stop",
            },
            { label: "Redirect", value: redirected?.redirect_suggestion ?? "—", tone: "warn" },
          ],
          note: "This is the problem statement's own words answered on screen.",
        };
      },
    },
    {
      id: "routing",
      title: "Partner routing, and why not",
      proves: "The screen no other entry will have.",
      say: "These branches are close to Sunita. Each one names the exact rule that excludes it. She would have walked into one of these.",
      run: async () => {
        const d = await call<{
          partners: { name: string; distance_km: number | null; score: number }[];
          why_not: { name: string; reason: string }[];
          candidates_considered: number;
          eligible_partner_count: number;
        }>("/partners/route", {
          scheme_code: "NSFDC_MICRO_FINANCE",
          amount: 72000,
          district: "Nagpur",
        });
        return {
          title: `${d.eligible_partner_count} of ${d.candidates_considered} branches can help`,
          lines: [
            ...d.partners.slice(0, 3).map((p) => ({
              label: `${p.distance_km ?? "—"} km`,
              value: p.name,
              tone: "good" as const,
            })),
            ...d.why_not.map((w) => ({
              label: "Cannot help",
              value: w.reason,
              tone: "stop" as const,
            })),
          ],
          note: "Hard-filtered on authorisation and ticket size before any ranking.",
        };
      },
      open: {
        href: "/en/results/NSFDC_MICRO_FINANCE/partners?amount=72000&district=Nagpur&family=MICRO_FINANCE",
        label: "Open the partner screen",
      },
    },
    {
      id: "multilingual",
      title: "The same decision, six languages",
      proves: "Not translated labels — the reasons themselves.",
      say: "One profile, one verdict, six languages. The rule IDs are identical; only the words change. Official scheme names are never translated.",
      run: async () => {
        const results = await Promise.all(
          LANGUAGES.map(async ([code, label]) => {
            const d = await call<{ results: SchemeResult[] }>("/match", {
              profile: PROFILES.sunita,
              language: code,
            });
            return { label, reason: d.results[0].matched_because[0] };
          }),
        );
        return {
          title: "MF_CATEGORY_SC, rendered in six languages",
          lines: results.map((r) => ({ label: r.label, value: r.reason?.message ?? "—" })),
          note: "Same rule ID, same verdict, every time.",
        };
      },
    },
    {
      id: "privacy",
      title: "The Aadhaar redaction proof",
      proves: "Not a policy statement — a test that reads the stored pixels.",
      say: "This renders an Aadhaar-like card, confirms OCR can read the number, runs the real upload pipeline, then OCRs the stored bytes to prove the digits are gone.",
      command: "docker compose exec api python -m pytest tests/test_redaction.py -v",
    },
    {
      id: "analytics",
      title: "The ministry dashboard",
      proves: "A procurement instrument, not a chart.",
      say: "Districts where citizens ran an eligibility check and no authorised partner can process what they matched. Demand measured from checks, not applications — the people who matter most never applied.",
      run: async () => {
        const login = await call<{ access_token: string }>("/auth/login", {
          email: "admin@setu.gov.in",
          password: "setu-demo-2026",
        });
        const response = await fetch(`${API()}/admin/analytics`, {
          headers: { Authorization: `Bearer ${login.access_token}` },
        });
        const d = (await response.json()) as {
          misrouting: { total_prevented: number; routing_calls: number };
          coverage: {
            underserved: { district: string; state: string; families_unserved: string[] }[];
          };
        };
        return {
          title: `${d.misrouting.total_prevented} wrong-counter outcomes prevented`,
          lines: [
            {
              label: "Across",
              value: `${d.misrouting.routing_calls} routing decisions`,
              tone: "good",
            },
            ...d.coverage.underserved.slice(0, 4).map((u) => ({
              label: `${u.district}, ${u.state}`,
              value: `no partner for ${u.families_unserved.join(", ").toLowerCase().replace(/_/g, " ")}`,
              tone: "warn" as const,
            })),
          ],
          note: "Every figure is a live query, not a fixture.",
        };
      },
      open: { href: "/console/admin", label: "Open the dashboard" },
    },
    {
      id: "whatsapp",
      title: "A feature phone",
      proves: "The same orchestrator, over text.",
      say: "The people furthest from a branch are the least likely to own a smartphone. Four keypad messages to a verdict, in Hindi, through the same handle_turn the web app calls.",
      run: async () => {
        const sender = `demo-console-${Date.now()}`;
        const reply = await call<{ text: string; stage: string; sms_segments: number }>(
          "/webhook/whatsapp",
          {
            simulate: true,
            sender,
            text: "mujhe sabzi ka thela lagana hai",
            language: "hi",
          },
        );
        return {
          title: `Reply in ${reply.sms_segments} SMS segment(s)`,
          lines: [
            { label: "Stage", value: reply.stage },
            { label: "SETU says", value: reply.text },
          ],
          note: "Indic scripts encode as UCS-2 — 70 characters a segment, not 160.",
        };
      },
      open: { href: "/demo/whatsapp", label: "Open the simulator" },
    },
    {
      id: "chaos",
      title: "Take the model away",
      proves: "The claim, proved rather than asserted.",
      say: "This points the running service at a model endpoint that does not exist and drives a full citizen journey. Same scheme, same verdict, same rules digest — byte-identical, because no model was ever involved in deciding.",
      command: "make chaos",
    },
  ];

  const toneClass = (tone: Line["tone"]) =>
    tone === "good"
      ? "text-good-fg"
      : tone === "warn"
        ? "text-warn-fg"
        : tone === "stop"
          ? "text-stop-fg"
          : "text-ink";

  return (
    <main className="mx-auto max-w-6xl px-5 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
        <div>
          <h1 className="text-2xl font-semibold">SETU demo console</h1>
          <p className="mt-1 text-base text-ink-muted">
            Every scenario runs against the local API. Nothing external, nothing random,
            nothing destructive.
          </p>
        </div>
        <div className="text-sm">
          <div className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                health === "up" ? "bg-good-fg" : health === "down" ? "bg-stop-fg" : "bg-line"
              }`}
            />
            <span>
              {health === "up"
                ? "API responding"
                : health === "down"
                  ? "API unreachable — run docker compose up -d"
                  : "checking…"}
            </span>
          </div>
          {ready ? (
            <p className="mt-1 text-ink-faint">
              database {String(ready.database)} · redis {String(ready.redis)} · model{" "}
              {String(ready.llm_provider_configured)}
            </p>
          ) : null}
        </div>
      </header>

      <p className="mt-4 rounded-card border border-line bg-canvas px-4 py-3 text-sm text-ink-muted">
        <strong>Local demo tool — not for deployment.</strong> The analytics scenario signs
        in with the seeded admin credentials from this page, so it must be removed before
        any deployment; see docs/DEPLOYMENT.md. If a screen looks wrong, rebuild the world
        in about two seconds:{" "}
        <code className="rounded bg-line/60 px-1.5 py-0.5">make demo</code>. There is no
        reset button here on purpose — a destructive HTTP endpoint is not worth saving one
        command.
      </p>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <ol className="space-y-4">
          {scenarios.map((scenario, index) => (
            <li key={scenario.id}>
              <article className="card p-5">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-sm text-ink-faint">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h2 className="text-lg font-semibold">{scenario.title}</h2>
                </div>
                <p className="mt-1 text-base text-ink-muted">{scenario.proves}</p>
                <blockquote className="mt-3 border-l-4 border-accent-600 pl-3 text-base">
                  {scenario.say}
                </blockquote>

                <div className="mt-4 flex flex-wrap gap-2">
                  {scenario.run ? (
                    <button
                      type="button"
                      onClick={() => void launch(scenario)}
                      disabled={active === scenario.id || health !== "up"}
                      className="btn-primary text-base disabled:opacity-50"
                    >
                      {active === scenario.id ? "Running…" : "Run it"}
                    </button>
                  ) : null}
                  {scenario.open ? (
                    <Link href={scenario.open.href} className="btn-secondary text-base">
                      {scenario.open.label}
                    </Link>
                  ) : null}
                </div>

                {scenario.command ? (
                  <pre className="mt-3 overflow-x-auto rounded-card bg-canvas px-3 py-2 text-sm">
                    <code>{scenario.command}</code>
                  </pre>
                ) : null}
              </article>
            </li>
          ))}
        </ol>

        <div className="lg:sticky lg:top-6 lg:h-fit">
          <div className="card p-5">
            <h2 className="text-lg font-semibold">Result</h2>
            {error ? (
              <p role="alert" className="mt-3 text-base text-stop-fg">
                {error}
              </p>
            ) : panel ? (
              <>
                <p className="mt-2 text-lg font-medium">{panel.title}</p>
                <dl className="mt-4 space-y-3">
                  {panel.lines.map((line, i) => (
                    <div key={i} className="border-t border-line pt-2">
                      <dt className="font-mono text-xs uppercase tracking-wide text-ink-faint">
                        {line.label}
                      </dt>
                      <dd className={`mt-0.5 text-base ${toneClass(line.tone)}`}>{line.value}</dd>
                    </div>
                  ))}
                </dl>
                {panel.note ? (
                  <p className="mt-4 border-t border-line pt-3 text-sm text-ink-faint">
                    {panel.note}
                  </p>
                ) : null}
              </>
            ) : (
              <p className="mt-3 text-base text-ink-muted">
                Press &ldquo;Run it&rdquo; on any scenario. The result appears here, live from
                the API.
              </p>
            )}
          </div>

          <p className="mt-4 px-1 text-sm text-ink-faint">
            Channel Partner records are synthetic, pending the official MoSJE partner master.
            Scheme figures are verified against nsfdc.nic.in but carry no circular number and
            are flagged accordingly.
          </p>
        </div>
      </div>
    </main>
  );
}
