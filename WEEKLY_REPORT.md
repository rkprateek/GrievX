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

## Week 2 - Project Foundation

### Completed

- Created a Git-friendly monorepo layout: `apps/mobile`, `apps/admin`, `services/api`, `services/ml`, and `infra`.
- Added the Expo + React Native TypeScript student-app shell with typed navigation tabs for Home, Report, and Profile.
- Added a Next.js + TypeScript + Tailwind operations-dashboard shell.
- Added FastAPI configuration, versioned `/api/v1` routing, CORS configuration, and live/readiness health endpoints.
- Added asynchronous PostgreSQL connection adapter, Redis adapter, and S3-compatible MinIO adapter.
- Added Docker Compose definitions for PostgreSQL 16, Redis 7, MinIO, bucket initialization, API, and admin dashboard.

### Verification

| Check | Result |
| --- | --- |
| Backend foundation tests | Pass - 3 passed, 1 skipped |
| Admin TypeScript validation | Pass |
| Docker Compose runtime | Not run - Docker unavailable in execution environment |
| Expo validation | Not run - dependency installation unavailable in execution environment |

## Week 3 - Authentication and Role Management

### Completed

- Implemented JWT-based authentication with environment-configured signing secret, algorithm, and expiration.
- Added Argon2 password hashing and verification; raw passwords are never persisted or returned by API responses.
- Added four roles: `student`, `staff`, `department_head`, and `admin`.
- Added `users`, `roles`, and `departments` SQLAlchemy models.
- Added Alembic configuration and migration `0001_auth_roles` with role seed data.
- Added student-only registration, login, current-user (`/auth/me`), and logout/token-handling endpoints.
- Added reusable authenticated-user and role-based authorization dependencies.
- Added protected student, staff, department-head, and admin routes.
- Added mobile student login/register screens and secure token storage using Expo SecureStore.
- Added authenticated mobile profile/logout flow.
- Added admin/staff operations login and role-aware dashboard access.
- Added authentication/authorization tests covering valid login, invalid login, unauthenticated access, student-to-admin denial, admin access, staff access, and password non-exposure.

### Verification

| Check | Result |
| --- | --- |
| Authentication source implementation | Complete |
| Authorization implementation | Complete |
| Database migration | Added |
| Mobile authentication UI | Added |
| Admin/staff portal | Added |
| Automated authentication tests | Added; execution requires the project's Python dependencies/runtime |
| Full test execution in this environment | Not verified - repository runtime dependencies were not available to the connected workspace |

### Security notes

- JWT secrets are read from environment configuration and are not committed as real secrets.
- Passwords are hashed with Argon2 and never included in user responses.
- Student registration always assigns the `student` role; clients cannot self-register as staff, department head, or admin.
- Backend authorization is authoritative; frontend role checks are only a usability layer.

### Week 4 boundary

Week 4 will implement complaint submission, image upload, location capture, complaint history, and MinIO persistence. No complaint or AI implementation was added to Week 3.
