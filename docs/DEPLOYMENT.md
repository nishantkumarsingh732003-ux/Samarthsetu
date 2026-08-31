# Deploying SETU

The repository carries working configuration for Vercel (web) and Render (API +
Postgres). **Nothing here has been deployed** — pushing a public URL requires accounts and
credentials that belong to the repository owner, so the configs are checked in ready to
run and the deploy is one deliberate action rather than something that happened quietly.

The demo does not need any of this. `docker compose up -d && make demo` gives the full
system on a laptop, offline, in about forty seconds, and that is what the run sheet in
[DEMO_SCRIPT.md](DEMO_SCRIPT.md) assumes.

---

## Before deploying anything

- [ ] `SECRET_KEY` set to a long random value. The default is literally `change-me`, and the JWT signing key is derived from it.
- [ ] `ID_HASH_SALT` set to its own long random value. It defaults to `SECRET_KEY`, which is fine for a dev clone and not for anything holding real citizen data. **Rotating it later invalidates every existing government-ID hash** — deliberately, because the old ones stop being meaningful.
- [ ] `SEED_PASSWORD` set. The users seeder **refuses to run** with the published demo password unless `ENVIRONMENT=development`, but set it explicitly rather than relying on that guard.
- [ ] `ENVIRONMENT=production`.
- [ ] `ALLOWED_ORIGINS` set to the real web origin. `*` would let any site call the API with a citizen's session.
- [ ] The demo-credentials block removed from `apps/web/src/app/console/login/page.tsx`.
- [ ] A decision taken on `LLM_PROVIDER`. `none` is fully supported and costs nothing; the service works without it (`make chaos` proves this).
- [ ] Partner data replaced, or the synthetic-data disclaimer left visibly in place.

Storage note: the API writes redacted document bytes to `STORAGE_DIR`, a local directory.
On a platform with an ephemeral filesystem those files vanish on redeploy. For anything
beyond a demo, mount a persistent disk or swap `app/services/storage.py` for object
storage — it is a four-function module behind exactly that seam.

---

## Web → Vercel

`apps/web/vercel.json` is checked in. From the repo root:

```bash
npx vercel --cwd apps/web
```

Set one environment variable in the Vercel project:

```
NEXT_PUBLIC_API_BASE_URL = https://<your-api-host>/api/v1
```

It must be reachable from the citizen's browser, not from Vercel's build container — the
citizen app calls the API directly from the device.

---

## API + Postgres → Render

`render.yaml` at the repo root declares the web service, a Postgres instance and a Redis
instance. In the Render dashboard: **New → Blueprint**, point it at the repository.

Two things Render will not do for you:

**PostGIS and pgvector.** Render's managed Postgres supports both, but the extensions must
be created once:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```

Without them `alembic upgrade head` fails on the first geometry column, which is the
correct failure — a partner registry with no spatial index would not route.

**Seeding.** Migrations run automatically from `entrypoint.sh`; data does not. Once:

```bash
render exec <service> -- python /scripts/seed/run.py
```

Run `demo.py` only if you want the synthetic personas on a public URL. It truncates
citizen data, so never point it at anything real.

---

## Verifying a deployment

```bash
curl https://<api-host>/health     # {"status":"ok"}
curl https://<api-host>/readyz     # database / redis / llm, each stated
```

Then, from a phone on mobile data rather than office wifi — this project's whole premise
is a Rs 6,000 handset on a bad connection, and a deployment verified only on a laptop has
not been verified:

1. Open the web URL, pick a language, complete Sunita's journey.
2. Confirm the offline banner appears in aeroplane mode and the saved results still render.
3. Open `/console/login` and sign in.
4. Check `X-Request-ID` comes back on a response, so an incident is traceable.

---

## Railway, as an alternative

Railway works with the same `apps/api/Dockerfile`. Add Postgres and Redis plugins, create
the two extensions as above, and set the same environment variables. There is no
`railway.json` in the repo because Railway infers the Dockerfile; adding one would be a
file nobody maintains.
