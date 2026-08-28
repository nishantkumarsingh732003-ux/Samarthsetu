const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const API_ORIGIN = API_BASE.replace(/\/api\/v1\/?$/, "");

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <header className="space-y-3">
        <p className="text-sm font-medium uppercase tracking-widest text-slate-500">
          Ministry of Social Justice &amp; Empowerment
        </p>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900">SETU</h1>
        <p className="text-lg text-slate-700">Scheme Eligibility &amp; Transparent Uptake</p>
      </header>

      <p className="text-base leading-relaxed text-slate-700">
        Find the government credit scheme that fits you, and the nearest Channel Partner
        authorised to process it. Eligibility is decided by a versioned, auditable rule
        engine — never by a language model.
      </p>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Build status
        </h2>
        <p className="mt-2 text-slate-700">
          Phase 0 — foundation and data model. The citizen journey lands in Phase 4.
        </p>
        <ul className="mt-4 space-y-1 text-sm">
          <li>
            <a className="text-sky-800 underline underline-offset-4" href={`${API_ORIGIN}/docs`}>
              API documentation
            </a>
          </li>
          <li>
            <a className="text-sky-800 underline underline-offset-4" href={`${API_ORIGIN}/health`}>
              API health check
            </a>
          </li>
        </ul>
      </section>
    </main>
  );
}
