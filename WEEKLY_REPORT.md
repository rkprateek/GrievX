# Weekly Report

## Week 1 - Requirements, Architecture and Project Planning

### Completed

- Inspected the new repository and initialized Git because no repository existed.
- Added the provided CampusFix reference as `reference/CampusFix.pdf` and analyzed it as architectural inspiration.
- Produced functional and non-functional requirements, role definitions, frontend/backend/ML architecture, normalized PostgreSQL design, API groups, mobile and operations-dashboard wireframes, and the complete 14-week roadmap.
- Added project-specific engineering, security, data, ML integrity, and quality rules in `AGENTS.md`.
- Added a `.gitignore` for secrets, dependencies, generated artefacts, and local service data.

### Reference decisions

CampusFix supports the choice of a modular FastAPI-centered workflow with multimodal assistance, PostgreSQL, Redis, and object storage. Its reported accuracy/latency values are not adopted. GrievX requires its own versioned datasets, evaluation reports, and human review before ML claims or automated operational use.

### Verification

| Check | Result |
| --- | --- |
| Repository inspection | Pass - repository was empty before initialization |
| Reference PDF inspection | Pass - all 8 pages reviewed |
| Required Week 1 documents present | Pass |
| Markdown structural checks | Pass - all 10 required artifacts present; Markdown code fences are balanced across 360 documentation lines |
| Application tests | Not applicable - no application code is authorized for Week 1 |

### How to review

1. Read `docs/requirements.md` to approve the scope, roles, and operational rules.
2. Review `docs/architecture.md`, then `docs/database-design.md` and `docs/api-design.md` together for service/data/API alignment.
3. Review `docs/ui-wireframes.md` with students and operations staff for flow feedback.
4. Confirm the Week 2 foundation decisions in `docs/14-week-roadmap.md`.

### Known limitations

- No running application, database migration, API, ML model, or UI implementation exists by design; these are outside Week 1.
- Campus SSO, notification provider, map provider, retention policy, labelled datasets, and production hosting remain stakeholder decisions.
- Wireframes are low fidelity and require usability review before visual implementation.

### Suggested professor demonstration

Walk through the student reporting flow and the staff/admin triage flow in the wireframes. Then show how one complaint becomes an auditable record: complaint, evidence metadata, status history, assignment history, AI prediction version, notification, and optional incident link. Emphasize that the architecture keeps AI advisory and evidence-based, rather than copying unsupported metrics from the reference paper.

### Week 2 prerequisites

- Approve the Week 1 documents and confirm the selected local development toolchain.
- Confirm whether users authenticate with campus SSO, local accounts, or a staged local-account implementation.
- Provide/approve local Docker availability and preferred Node.js/Python versions.
- Confirm initial environment names and local service ports if the institution has constraints.

## Week 2 - Project Foundation

### Completed

- Created a Git-friendly monorepo layout: `apps/mobile`, `apps/admin`, `services/api`, `services/ml`, and `infra`.
- Added the Expo + React Native TypeScript student-app shell with typed navigation tabs for Home, Report, and Profile. The Report/Profile screens explicitly state that their Week 3/4 features are not available.
- Added a Next.js + TypeScript + Tailwind operations-dashboard shell with responsive navigation and foundation-status layout.
- Added FastAPI configuration, versioned `/api/v1` routing, CORS configuration, and live/readiness health endpoints.
- Added asynchronous PostgreSQL connection adapter, Redis adapter, and S3-compatible MinIO adapter. Readiness checks all three dependencies concurrently.
- Added Docker Compose definitions for PostgreSQL 16, Redis 7, MinIO, bucket initialization, API, and the admin dashboard; persistent data uses named volumes.
- Added root and package-level environment templates, Dockerfiles, development documentation, and npm/Python project configuration.
- Added backend tests for liveness, dependency readiness failure handling, and a real asynchronous SQLAlchemy database-engine connectivity probe.

### Verification

| Check | Result |
| --- | --- |
| `python -m pytest -q` in `services/api` | Pass - 3 passed, 1 skipped in 10.39s (one third-party Starlette deprecation warning) |
| API test coverage | Pass - liveness, readiness state, async database-engine connectivity, and opt-in PostgreSQL integration probe covered |
| `npm run lint --prefix apps/admin` | Pass - TypeScript validation completed |
| Docker Compose runtime | Not run - Docker is not installed on this machine |
| Expo mobile TypeScript validation | Not run - Expo dependency installation stalled in this execution environment; source manifest and configuration are complete |

### How to run

1. Install Docker Desktop, Node.js 20.18+ / npm 10+, and Python 3.12+.
2. Copy `.env.example` to `.env` and replace local-only placeholder passwords before starting services.
3. Run `docker compose up --build` from the repository root.
4. Open the admin shell at `http://localhost:3000`, OpenAPI at `http://localhost:8000/docs`, and MinIO at `http://localhost:9001`.
5. Confirm `http://localhost:8000/api/v1/health/live` returns `200`; after dependencies start, `/health/ready` returns `200` with database, Redis, and object storage marked `ok`.
6. In another terminal, run `npm install` then `npm run dev:mobile` to start Expo. Use a LAN API address instead of `localhost` for a physical device.

### Known limitations

- Docker Desktop is unavailable in the current execution environment, so live PostgreSQL/Redis/MinIO and full Compose validation remain for a Docker-enabled machine.
- Authentication, roles, database domain migrations, complaints, uploads, notifications, and ML are intentionally not implemented; they belong to later roadmap weeks.
- The readiness route reports dependency health only; it does not expose credentials or service internals.

### Suggested professor demonstration

Show the project layout, then start Compose on a Docker-enabled machine. Open the admin foundation shell, FastAPI OpenAPI page, and MinIO console. Demonstrate `/health/live`, then `/health/ready` showing all three infrastructure dependencies. Finally start Expo and navigate Home, Report, and Profile to show the mobile architecture is connected and feature scope is intentionally staged.

### Week 3 prerequisites

- Confirm whether Week 3 begins with local accounts or campus SSO integration.
- Confirm JWT issuer/audience, access/refresh token lifetimes, password policy, and authorized CORS origins.
- Install Docker Desktop locally and complete `docker compose up --build` validation.
- Complete `npm install`, then run `npm run check:admin` and `npm run check:mobile` on the developer machine.
