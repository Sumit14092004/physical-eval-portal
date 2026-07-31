# Physical Evaluation Portal

Training academy management system covering Training Records, BPET/PPT
Physical Evaluation (age-graded, auto-grading), and the Weekly →
Monthly → Quarterly → Final examination pipeline with merit ranking.

## Why this stack

- **FastAPI (async)** — handles high concurrency (many instructors entering
  marks simultaneously during exam windows) without blocking; native
  Python ecosystem makes future AI features (predictive fitness scoring,
  anomaly detection in marks, performance forecasting) straightforward
  to bolt on later without a rewrite.
- **PostgreSQL** — your data is deeply relational; window functions
  (`RANK() OVER (...)`) make batch-wide rank computation fast even at
  150k+ trainees, done in the DB rather than pulled into app memory.
- **Redis + Celery** — rank recomputation and report generation run as
  background jobs, not on the request path.
- **JWT + RBAC** — stateless auth scales horizontally across instances.

## Key design decision: standards are data, not code

The exact BPET/PPT thresholds (Excellent/Good/Satisfactory per age band)
live in the `physical_standards` table, seeded from the official tables
in `app/db/seed_physical_standards.py`. The grading engine
(`app/services/grading.py`) only encodes *comparison logic*
(lower-is-better vs higher-is-better). If standards are revised, you
update the table — no code deploy needed.

**⚠️ One value needs your verification:** in the source PPT table, the
40-45 age band row has a "Push up" column that appears to replace
"Chin up" for that band (per the image, Chin up shows Ex-20/Good-18/Sat-16
under a "Push up" sub-header). I've transcribed it as-is into
`seed_physical_standards.py` but flagged it with a comment — please
double check that row against the original document before relying on
it in production, since it's the one ambiguous cell in an otherwise
clean table.

## Demo data

Two seed scripts, run in order:

```bash
python -m app.db.seed_physical_standards   # BPET/PPT threshold reference tables
python -m app.db.seed_demo_data            # 5 staff accounts + 1 batch + 50 trainees
```

`seed_demo_data.py` creates:
- **5 staff logins**: 1 instructor (`trainer@academy.test`) + 4 admins,
  including one labeled for you (`sumit.admin@academy.test`) and three
  others. All share password `Academy@2026` — change it after first login.
- **1 batch**: "GD Constable Batch 2026-A"
- **50 trainees**, realistic Indian names, weighted mostly into the 18-30
  age band (typical fresh-recruit intake) with a handful spread across
  30-40 / 40-45 / 45-50 so every BPET/PPT threshold row actually gets
  exercised when grading results.

## Design system

Restyled to an institutional government-portal identity (in the spirit of
sites like indianarmy.gov.in — utility bar, navy header, tricolor accent
stripe, horizontal nav, breadcrumb) rather than a generic SaaS dashboard.
Uses a generic circular badge, not any official emblem/crest.

- **Palette**: navy `#0B3D65` (header), maroon `#7A1F2B` (active nav/accents),
  gold `#B08D2E` (rank/merit), gray-blue paper background, tricolor stripe
  (saffron/white/green) as a structural divider under the header.
- **Type**: Merriweather (serif, institutional headings), Inter (body),
  IBM Plex Mono (all numeric data — marks, ranks, dates).

## What's built so far

**Backend — 22 routes, fully wired, imports and compiles clean:**
```
backend/
  app/
    models/          # User, Trainee, Batch, PhysicalActivity/Standard/Result,
                      # TrainingRecord, Weekly/Monthly/Quarterly/Final exams
    services/
      grading.py      # BPET/PPT auto-grading engine
      ranking.py      # SQL window-function based rank computation
    routers/
      auth.py                  # JWT login
      org.py                   # batches, trainees, bulk CSV import
      physical_evaluation.py   # record + fetch BPET/PPT results, list activities
      training.py              # training record CRUD
      examinations.py          # weekly/monthly/quarterly/final + merit list
    db/
      base.py                     # async SQLAlchemy engine/session
      seed_physical_standards.py  # seeds official threshold tables
    core/
      config.py, security.py, deps.py   # settings, JWT, RBAC dependency
  alembic/            # initial migration creates all tables + enums
  requirements.txt
docker-compose.yml   # postgres + redis + backend for local dev
```

**Frontend — builds clean, type-checks clean:**
- Design system: institutional "service register" identity (olive/brass/paper,
  Barlow Condensed + Inter + IBM Plex Mono)
- Login, Dashboard, role-aware sidebar shell
- Physical Evaluation entry form — batch selector → trainee dropdown →
  activity dropdown (BPET/PPT grouped) → live auto-graded result
- Training Records — full entry form (subject, instructor, indoor/outdoor,
  attendance, drill/PT/weapon/firing/obstacle/tactical) + running list per trainee
- Examinations — tabbed entry forms for Weekly / Monthly / Quarterly / Final,
  each showing live computed percentage/aggregate/rank from the backend
- Merit List — batch-scoped, pulls real ranked data from the backend
- Administration (admin-only) — create batch, add a single trainee, bulk
  CSV import with per-row error reporting
- My Records (trainee-only, read-only) — physical evaluation, training
  records, weekly tests, and final exam standing; navigation is now
  role-split so trainees never see instructor entry forms

**Background jobs — Celery wired in:**
- Rank recomputation (monthly / quarterly / final) now dispatches as a
  Celery task instead of running inline on the request path, with retry
  on transient DB errors (`app/tasks/ranking_tasks.py`)
- A sync DB session (`app/db/sync_base.py`, psycopg2 driver) backs the
  Celery worker, separate from the async engine FastAPI uses
  — Trade-off: the API response right after submitting a mark reflects
  rank as of before that submission; the frontend shows "computing…"
  until a refetch picks up the settled rank (typically sub-second)
  - `docker-compose.yml` now includes a `celery_worker` service

## Not yet built (next steps — tell me which to prioritize)

- Deployment config (containers are ready; need a target: AWS/GCP/on-prem + CI/CD)
- Merit List page for trainees currently shows a batch selector rather than
  defaulting to their own batch — small UX polish item
- Celery Beat / periodic recompute as a safety net (currently recompute is
  purely event-driven off each mark submission)

## Scaling & AI roadmap (for when you're ready)

- **Now → thousands of trainees:** current setup (single Postgres,
  single backend instance) is plenty.
- **Tens of thousands:** add PgBouncer for connection pooling, read
  replicas for reporting/dashboards, and a CDN for the frontend.
- **150k+ / national scale:** partition large tables (e.g.
  `physical_test_results`) by batch or year, move report generation
  fully to Celery, consider horizontal backend scaling behind a load
  balancer.
- **AI integration (future):** the clean separation of raw performance
  data (`physical_test_results`) from grading logic means you can later
  add a model that predicts injury risk, flags anomalous performance
  drops, or recommends individualized training adjustments — it would
  read from the same tables without touching the core schema.

## Local development setup

```bash
docker compose up -d postgres redis
cd backend
pip install -r requirements.txt --break-system-packages
alembic upgrade head
python -m app.db.seed_physical_standards
python -m app.db.seed_demo_data
uvicorn app.main:app --reload
```

In a second terminal, for the Celery worker (needed for rank recomputation to actually run):
```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

In a third terminal, for the frontend:
```bash
cd frontend
npm install
npm run dev
```

API docs at `http://localhost:8000/docs`, app at `http://localhost:5173`.

## Deployment

**Want the free path (Render + Neon + GitHub Pages)?** See `DEPLOY_FREE.md` for exact steps. The rest of this section covers the real-VM path (`docker-compose.prod.yml`), for when you're ready to actually serve trainees.

**⚠️ Honest note:** the Dockerfiles, `docker-compose.prod.yml`, and Caddy
config below follow standard, well-established patterns, but there's no
Docker daemon available in the sandbox this was built in, so they're
reviewed carefully but not build-tested end-to-end. Run `docker compose
-f docker-compose.prod.yml up -d --build` yourself and check logs before
trusting this with real data.

### What's included

- `backend/Dockerfile` — Python 3.12, installs `requirements.txt`
- `frontend/Dockerfile` — multi-stage: Node builds the Vite app, nginx serves the static output
- `frontend/nginx.conf` — serves the SPA, proxies `/api/` to the backend container
- `docker-compose.prod.yml` — Postgres, Redis, backend (Gunicorn + Uvicorn workers), Celery worker, frontend (nginx), and Caddy as reverse proxy with **automatic HTTPS** (just point DNS at the VM and set `DOMAIN`)
- `.github/workflows/ci.yml` — on every push: backend import check, Celery task import check, frontend type-check + build, then both Docker images build. No deploy step yet (see below).

### Getting a single instance live (the right starting point at your current scale)

1. Provision a VM (any provider — a $10–20/mo box is plenty to start: DigitalOcean, AWS Lightsail, Azure, a college-provided server, etc.) with Docker + Docker Compose installed.
2. Point your domain's DNS A record at the VM's IP.
3. Copy the repo to the VM, then:
   ```bash
   cp .env.prod.example .env
   # edit .env: set real POSTGRES_PASSWORD, JWT_SECRET_KEY, CORS_ORIGINS, DOMAIN
   docker compose -f docker-compose.prod.yml up -d --build
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   docker compose -f docker-compose.prod.yml exec backend python -m app.db.seed_physical_standards
   ```
4. Caddy issues a Let's Encrypt certificate automatically on first request — no manual certbot step.
5. Skip `seed_demo_data.py` in production; use the Administration screens (or bulk CSV import) to add real batches/trainees instead.

### CI/CD — what exists vs. what's a deliberate decision point

CI (build/type-check verification) is wired and will run on every push once this is a GitHub repo. **Continuous deployment isn't wired up** — that's a deliberate stopping point rather than an oversight, because it needs you to have already chosen a hosting target and created credentials (SSH key or cloud provider token) for GitHub Actions to deploy with. Once you've provisioned the VM above, the missing piece is a final job in `ci.yml` that SSHes in and runs `docker compose pull && up -d` — a small addition once the target exists.

### When to move past this

Single-VM Docker Compose comfortably handles a moderate trainee count. Revisit before you approach 150k+ concurrent load per the "Scaling path" above — namely: move Postgres to a managed service (RDS/Cloud SQL) before it becomes the bottleneck, since that's the hardest piece to migrate later without downtime.

## Status

Every item from the original build-out list is now done, including the two remaining polish items:
- **Merit List** auto-scopes to a trainee's own batch (no picker shown) and highlights their own row — admins/instructors still get the full batch selector.
- **Celery Beat** runs a periodic safety-net task every 15 minutes (`tasks.reconcile_all_ranks`) that walks every batch and every month/quarter with actual data, recomputing ranks fresh. This catches staleness from a dropped task (worker restart mid-job, exhausted retries) without anyone needing to notice and manually trigger a fix. Wired into both `docker-compose.yml` and `docker-compose.prod.yml` as a `celery_beat` service.

Confirmed: backend imports cleanly with 27 routes, the Beat schedule and periodic task both import without error, and the frontend type-checks and builds with zero errors.

Natural next horizons from here are less "finish the build" and more "operate it for real": actually deploying to a real VM and watching it under real usage, building out reporting/analytics views, or starting on the AI-integration roadmap mentioned above.
