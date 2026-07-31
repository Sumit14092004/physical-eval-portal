# Free Deployment Guide — Render + Neon + GitHub Pages

This is the zero-cost path: frontend on GitHub Pages, backend on Render's
free tier, database on Neon (Render's own free Postgres expires after 30
days, so we don't use it). Read `README.md`'s Deployment section first for
context on the trade-offs here vs. the real `docker-compose.prod.yml` path.

**What you're accepting with this path:** the Render free web service
sleeps after 15 minutes idle and takes 30-60s to wake on the next
request. Rank recomputation runs synchronously in the request instead of
in a background worker (see `app/core/celery_app.py` — no Redis/worker on
this path). Fine for a portfolio demo; not what you'd want serving real
trainees.

## 1. Database — Neon

1. Sign up at neon.tech (free, no credit card).
2. Create a project → note the connection string it gives you. It looks like:
   ```
   postgresql://user:password@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require
   ```
3. You need **two versions** of this for the two drivers our app uses:
   - `DATABASE_URL` (async, for the app): replace `postgresql://` with `postgresql+asyncpg://`
   - `SYNC_DATABASE_URL` (sync, for Alembic/Celery-eager-mode calls): replace `postgresql://` with `postgresql+psycopg2://`
   - Keep the `?sslmode=require` suffix on both.

## 2. Backend — Render

1. Push this repo to GitHub if you haven't already.
2. Sign up at render.com (free, no credit card).
3. New → Blueprint → connect your GitHub repo. Render reads `render.yaml` at the repo root and provisions the service.
4. Once created, go to the service's Environment tab and set the values marked `sync: false` in `render.yaml`:
   - `DATABASE_URL` — your Neon async connection string
   - `SYNC_DATABASE_URL` — your Neon sync connection string
   - `CORS_ORIGINS` — `["https://YOUR_GITHUB_USERNAME.github.io"]` (see step 3 below for the exact URL)
5. Deploy. First deploy also runs `alembic upgrade head` (baked into the start command) to create tables.
6. Once live, seed the reference data by opening a shell for the service (Render dashboard → Shell tab) and running:
   ```bash
   python -m app.db.seed_physical_standards
   python -m app.db.seed_demo_data
   ```
7. Note your backend's public URL — something like `https://physical-eval-backend.onrender.com`. You'll need `<that URL>/api/v1` for the next step.

## 3. Frontend — GitHub Pages

1. In your GitHub repo: Settings → Pages → set **Source** to "GitHub Actions" (not "Deploy from a branch").
2. Settings → Secrets and variables → Actions → add two repository secrets:
   - `VITE_API_BASE_URL` = `https://physical-eval-backend.onrender.com/api/v1` (your actual Render URL from step 2.7)
   - `VITE_BASE_PATH_REPO` = your repo's name exactly as it appears in the GitHub URL, e.g. `physical-eval-portal`
3. Push to `main` (or run the workflow manually from the Actions tab) — `.github/workflows/deploy-pages.yml` builds and deploys automatically.
4. Your app is live at `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/`.

## 4. Go back and fix CORS

Now that you know your exact GitHub Pages URL, double check it matches what you set for `CORS_ORIGINS` on Render in step 2.4 — if you guessed wrong, update it and Render will redeploy.

## Troubleshooting

- **Login hangs / network errors in the browser console:** almost always CORS — check `CORS_ORIGINS` on Render matches your GitHub Pages URL exactly (including `https://`, no trailing slash).
- **Blank page on GitHub Pages, assets 404 in Network tab:** `VITE_BASE_PATH_REPO` doesn't match your actual repo name.
- **First request takes ~40 seconds:** expected — Render free tier cold start. It'll be fast again for a few minutes after.
- **Refreshing on a route like `/merit` 404s:** shouldn't happen with `404.html` in place, but if you renamed the repo or serve from a custom domain, check `pathSegmentsToKeep` in `frontend/public/404.html` (0 for a root-served custom domain, 1 for a GitHub Pages project subpath).
