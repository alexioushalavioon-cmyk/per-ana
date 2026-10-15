# PER ANA

PER ANA is an evidence-based policy actor intelligence and decision-support platform.

This repository contains the online pilot implementation for the PER ANA platform, including research and evidence management, actor intelligence, analytical methods, policy strategy, reporting, administration and guardrails, and deployment configuration for Railway/Supabase/Upstash-compatible infrastructure.

## Architecture

- `apps/web`: Next.js + TypeScript, Persian-first RTL UI
- `apps/api`: FastAPI + SQLAlchemy API and worker
- PostgreSQL: canonical application data (Supabase)
- Redis: queue/cache boundary (Upstash)
- Object storage: S3-compatible adapter
- Auth: Supabase JWT adapter for production

## Production

Production secrets are not committed to this repository. Deployment values are configured through Railway environment variables.
