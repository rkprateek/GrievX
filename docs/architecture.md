# GrievX Architecture

## 1. Architectural principles

GrievX uses a modular monolith first: a FastAPI service owns the transactional domain and exposes a versioned REST API. Background workers perform slow, retryable work such as media scanning, notifications, ML inference, analytics aggregation, and duplicate-candidate generation. Clear internal interfaces allow future extraction only when load or ownership justifies it.

The source of truth is PostgreSQL. Redis is disposable cache/queue infrastructure, never the only copy of a complaint. Images and model artefacts live in S3-compatible storage (MinIO locally); PostgreSQL stores metadata and object keys only.

## 2. System context

```text
React Native / Expo mobile app        Next.js operations web app
            |                                      |
            +------------- HTTPS /api/v1 -----------+
                                  |
                    FastAPI API and domain services
       +----------+-----------+---------+-----------+----------+
       |          |           |         |           |          |
    Auth/RBAC  Complaints  Notifications AI Orchestrator Analytics
       |          |           |         |           |          |
       +----------+-----------+---------+-----------+----------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
        PostgreSQL            Redis              MinIO / S3
        system of record    cache + jobs       media + artefacts
                                  |
                       Background worker(s)
                                  |
             classifiers, image analysis, ETA, incident clustering
```

## 3. Frontend architecture

### Mobile (`apps/mobile`)

- React Native, Expo, TypeScript, Expo Router or React Navigation.
- Feature-oriented folders: `auth`, `complaints`, `notifications`, `profile`, and shared `ui`, `api`, `state`, `validation`.
- API client attaches access token, refreshes safely, handles offline/retry state, and never makes authorization decisions.
- Local form drafts are encrypted or minimized according to mobile platform policy; uploaded images are compressed only after user consent and remain original-quality where evidence policy requires.

### Operations web (`apps/web`)

- Next.js, TypeScript, Tailwind CSS, accessible shared components.
- One web application with route guards and role-based navigation for staff, department-head, admin, and super-admin surfaces.
- Server rendering is used for safe initial data where helpful; all authorization remains enforced by FastAPI.
- Features: queue, complaint detail, evidence viewer, assignment, lifecycle timeline, incident workspace, analytics, map, departments/users/settings.

## 4. Backend architecture (`services/api`)

```text
api/v1 routers -> dependency/auth layer -> application services -> repositories
                         |                         |                 |
                      Pydantic                 domain rules       SQLAlchemy
```

- **Routers**: HTTP concerns, schemas, response codes, dependency injection.
- **Application services**: complaint submission, lifecycle transitions, assignments, incident decisions, and audit creation inside transactions.
- **Domain policies**: transition matrix, authorization policies, SLA calculation, file validation, AI recommendation/override rules.
- **Repositories**: isolated SQLAlchemy queries; no business decisions hidden in routes.
- **Workers**: consume explicit job payloads keyed by immutable IDs; safely retry, record failures, and write prediction/notification results transactionally.
- **Storage adapter**: creates pre-signed upload/download flows and supports MinIO or production S3-compatible services through one interface.

## 5. ML architecture (`services/ml`)

```text
Complaint event -> feature preparation -> model adapters -> prediction records
                                          |       |       |
                                   text/image  priority/ETA  duplicate candidates
                                          \       |       /
                                           AI orchestrator
```

- The orchestrator invokes independently versioned model adapters and persists an `ai_predictions` record for each output.
- **Text**: TF-IDF + linear SVM baseline first; transformer classifier later after a labelled dataset and evaluation protocol exist.
- **Image**: feature extraction with a maintained lightweight model; defect detection only after a suitable labelled detection dataset exists.
- **Multimodal**: start with explicit, auditable late fusion of available features; introduce learned fusion only with paired, evaluated data.
- **Priority and routing**: begin as separate supervised tasks. Rule-based safety guardrails may raise human-review flags but are not described as trained predictions.
- **ETA**: regression trained on completed, sufficiently representative historical records; report error distributions, not a generic “accuracy.”
- **Duplicate/incidents**: retrieve candidates with weighted text embedding similarity, optional image embedding similarity, geospatial distance, recency, and category compatibility; a threshold creates a proposal, never an automatic irreversible merge.
- Every production model requires a version, training-data snapshot ID, feature contract, evaluation report, rollout state, and rollback path.

## 6. Deployment and environments

| Component | Local development | Production direction |
| --- | --- | --- |
| API and workers | Docker Compose containers | container orchestrator or managed container runtime |
| Database | PostgreSQL container | managed PostgreSQL with backups and encryption |
| Cache/queue | Redis container | managed Redis with persistence policy |
| Object store | MinIO container | private S3-compatible bucket with lifecycle policies |
| Secrets | local `.env` excluded from Git | secret manager / deployment secret store |
| Observability | structured console logs | centralized logs, metrics, alerts, tracing |

## 7. Security boundaries

- TLS terminates at the production ingress; services trust only configured proxy headers.
- Browser origins are explicitly allow-listed; mobile uses the same versioned API over TLS.
- Uploads pass content-type, signature, size, malware-scanning integration, and authorization checks before evidence becomes visible.
- Object URLs are short-lived and authorized per request; bucket/object keys are opaque.
- Administrative override, access, assignment, and model-activation actions produce audit logs.
