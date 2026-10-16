# PER ANA

PER ANA is an evidence-based policy actor intelligence and decision-support platform.

This repository implements Phases 1–4 of the approved v2 specification: the online core platform, case management, file ingestion, background-job skeleton, authentication adapter, and cloud-ready infrastructure boundaries.

## Architecture

- `apps/web`: Next.js 16.4 + TypeScript, Persian-first RTL UI
- `apps/api`: FastAPI + SQLAlchemy 2.1 API
- PostgreSQL: canonical application data (Supabase-compatible)
- Redis: queue/cache boundary (Upstash-compatible)
- Object storage: local adapter for development, S3-compatible adapter for Cloudflare R2
- Auth: dev adapter locally, Supabase JWT adapter for deployed environments

## Local quick start

1. Copy `.env.example` to `.env`.
2. Start infrastructure and apps:

   ```bash
   docker compose up --build
   ```

3. Open:
   - Web: http://localhost:3000
   - API docs: http://localhost:8000/docs
   - MinIO console: http://localhost:9001

Local development uses a deterministic developer identity when `AUTH_MODE=dev`. This is clearly isolated from production authentication and must not be used in production.

## Phase 1 acceptance target

A user can:

1. Open the web app.
2. Create a case.
3. Reopen the case.
4. Upload a source file.
5. See persisted case and file metadata.

The repository also exposes health, readiness, job, audit, and storage abstractions needed for later phases.

## Production adapters

Set these for deployed environments:

- `AUTH_MODE=supabase`
- `DATABASE_URL=<Supabase Postgres URL>`
- `SUPABASE_JWKS_URL=<Supabase JWKS URL>`
- `STORAGE_BACKEND=r2`
- `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`
- `REDIS_URL=<Upstash Redis URL>`

See `docs/PHASE1.md` for details and known limitations.


## Phase 2 — Research & Evidence

The current repository includes research-plan, source, evidence, actor-mention, deduplication, contradiction, Brave/Exa adapter and RTL Research Workspace foundations. See `docs/PHASE2.md`.


## Phase 3 status

Actor Intelligence is now available: canonical actors, aliases, merge/split, structured actor profiles, power decomposition, positions, constraints, relationships, evidence coverage, conservative baseline synthesis, and Deep Actor Research plans. See `docs/PHASE3.md`.


## Phase 4 status

The analytical engine now includes method selection, Power–Interest, Actor–Objective, network metrics, clustering, resource-dependency views and the deterministic MACTOR MVP core. See `docs/PHASE4.md`.

## Current build status
Phase 6 is implemented: report preview, snapshot/versioned report runs, evidence-linked citations, editable DOCX, PDF conversion, report-ready figures, validation, local downloads, and Persian Report Workspace.

## Phase 8 status
Integrated QA is complete. The deterministic analytical core passed the end-to-end Golden Cases and 28 automated tests. The repository is **not yet marked Pilot-Ready**; see `docs/PHASE8.md` for the P0/P1 remediation blockers (live AI Model Router, live search credentials, frontend production build, production Auth/RLS isolation, async worker validation).


## Phase 9 status
Online-pilot deployment configuration is prepared, including production browser authentication, Railway service configs, external verification scripts, and production environment contracts. A live URL is intentionally not claimed until user-owned cloud credentials are connected and the external gates in `docs/PHASE9.md` pass.
