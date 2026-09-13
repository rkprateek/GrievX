# Week 2 Development Environment

## Repository layout

```text
apps/mobile/        Expo + React Native student application shell
apps/admin/         Next.js operations-dashboard shell
services/api/       FastAPI API, infrastructure adapters, and tests
services/ml/        Reserved for Week 7+ ML code
infra/              Reserved for production deployment assets
compose.yaml        Local PostgreSQL, Redis, MinIO, API, and admin stack
```

## Environment configuration

Copy the root `.env.example` to `.env`. It contains local-development values only and must never be used for a deployed environment. `services/api/.env.example`, `apps/admin/.env.local.example`, and `apps/mobile/.env.example` document service-specific host-run settings.

`DATABASE_URL` uses `postgresql+asyncpg`; when the API runs from the host, use `localhost` rather than `postgres`. When it runs through Compose, its service hostname is `postgres`. The same distinction applies to Redis and MinIO.

## Health API

- `GET /api/v1/health/live` is process-only and returns `200` when FastAPI can serve requests.
- `GET /api/v1/health/ready` probes PostgreSQL, Redis, and the configured S3-compatible bucket concurrently. It returns `200` only if all dependencies are available and `503` otherwise.

No protected application resources, authentication routes, database domain tables, or complaint operations are implemented in Week 2.

## Commands

```powershell
# Full local dependency stack + API + web dashboard
Copy-Item .env.example .env
docker compose up --build

# Backend checks from the host
cd services/api
python -m pip install -e ".[dev]"
pytest

# Frontend dependency installation and static checks
cd ../..
npm install
npm run check:admin
npm run check:mobile
```

## Troubleshooting

- If `ready` is `503`, inspect the `dependencies` object in its response and then run `docker compose ps` / `docker compose logs <service>`.
- Do not use `localhost` in `DATABASE_URL`, `REDIS_URL`, or `S3_ENDPOINT_URL` inside the API Compose container; use Compose service names.
- MinIO creates the `grievx-uploads` bucket through the one-shot `minio-init` service. It is safe to rerun.
