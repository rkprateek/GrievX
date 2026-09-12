# GrievX Requirements

## 1. Product purpose

GrievX is a campus complaint and incident-management platform. Students submit location-aware written complaints with optional image evidence; authorized campus teams triage, assign, resolve, and communicate progress. The system records an auditable lifecycle and will progressively add evidence-based AI assistance.

CampusFix informs the general layered, multimodal workflow. It does **not** establish GrievX performance targets: all model quality claims must come from GrievX datasets and reproducible evaluation.

## 2. Stakeholders and roles

| Role | Primary responsibility | Core permissions |
| --- | --- | --- |
| Student | Report and follow personal issues | Create complaints, upload permitted evidence, view own complaints, comment where enabled, receive notifications |
| Staff | Perform assigned work | View department-assigned or personally assigned complaints, update permitted statuses, add resolution notes and evidence |
| Department Head | Manage one department's queue and SLA | All staff capabilities plus assign/reassign staff within department, review queue and department metrics |
| Admin | Operate campus-wide service delivery | View and manage all complaints, override AI suggestions, reassign departments, manage incidents, analytics, departments and users within policy |
| Super Admin | Govern the platform | All admin capabilities plus role/permission management, system configuration, retention controls, model-version activation, and audit-log access |

The Super Admin role is required to separate platform governance from daily administration. Least privilege applies; staff and department heads are scoped to their department unless granted an explicit cross-department permission.

## 3. Functional requirements

### Identity and access

- FR-01: Users can authenticate using approved campus credentials or locally managed accounts, subject to the selected identity strategy.
- FR-02: The backend issues and validates short-lived JWT access tokens and refresh tokens; passwords are stored only as secure hashes.
- FR-03: The platform enforces role and department scope for every protected operation.
- FR-04: Super Admins can activate/deactivate accounts and manage role assignments, with an audit log.

### Student complaint experience

- FR-05: A student can create a complaint with title, description, campus location, optional map coordinates, and one or more valid image files.
- FR-06: The system validates required fields, duplicate submissions caused by network retries, file type, file size, and upload failures.
- FR-07: A student can list, search, and view only their own complaints, including status timeline, assignment department, ETA when available, and resolution evidence permitted by policy.
- FR-08: A student receives notification when a complaint is created, assigned, status changes, requires information, is resolved, reopened, or merged into an incident.

### Operations and lifecycle

- FR-09: Authorized users can view complaint queues with search, filters, sorting, pagination, and complaint detail.
- FR-10: Admins and Department Heads can assign staff; Admins can assign or reassign departments. Every assignment change records actor, timestamp, and reason.
- FR-11: Staff can move an assigned complaint through valid statuses and attach resolution notes and resolution evidence.
- FR-12: The lifecycle supports `submitted`, `triaged`, `assigned`, `in_progress`, `awaiting_student`, `resolved`, `closed`, `reopened`, and `cancelled`; transitions are validated server-side and retained in history.
- FR-13: Authorized users can set or override priority (`critical`, `high`, `medium`, `low`) and a target resolution time, with a reason for overrides.
- FR-14: The system records administrative and high-impact actions in immutable audit events.

### AI assistance and incident intelligence

- FR-15: On complaint submission, the orchestrator can request category, priority, route, ETA, image, and duplicate/incident analyses as each model becomes available.
- FR-16: Every prediction stores model version, inputs/features reference, confidence or uncertainty where supported, timestamp, and whether a human accepted or overrode it.
- FR-17: Until a trained model is deployed, the UI/API must clearly return that an analysis is unavailable or heuristic, never a fabricated confidence.
- FR-18: The duplicate service can propose an existing incident using text, image, location, time, and category signals; an authorized human confirms, rejects, merges, or splits incident membership.

### Reporting and administration

- FR-19: Admins can view aggregate volume, status, SLA, priority, department performance, category, and incident trends with privacy-preserving aggregation.
- FR-20: Authorized users can view a campus map/heatmap with complaint and incident data filtered by time, status, category, and priority.
- FR-21: Admins can manage departments, operational categories, notification templates, and documented system settings.

## 4. Non-functional requirements

| Area | Requirement |
| --- | --- |
| Security | OWASP-informed validation, JWT authentication, RBAC, password hashing, CORS allow-list, secure headers, upload validation, secrets in environment/configuration, and audit trails |
| Privacy | Collect the minimum personal/location data, restrict evidence access by role, document retention/deletion policy, and avoid exposing students to other students' complaints by default |
| Reliability | Preserve complaint submission durably before asynchronous analysis; use retries/idempotency and health checks for dependent services |
| Performance | Paginate queues; keep synchronous create operations responsive by moving costly media/ML work to workers. Establish actual targets only after baseline load tests |
| Scalability | Stateless API containers, PostgreSQL as source of truth, Redis for cache/queues, S3-compatible object storage, and independently scalable worker processes |
| Accessibility | Mobile and web UIs target WCAG 2.2 AA practices: semantic controls, keyboard navigation, visible focus, sufficient contrast, labels, and error messages |
| Maintainability | Typed interfaces, modular packages, migrations, linting/formatting, tests, API versioning, ADR-worthy decisions documented |
| Observability | Structured logs with request/correlation IDs, health/readiness endpoints, error tracking, metrics, and no sensitive payloads in logs |
| Portability | Docker Compose local setup; S3-compatible storage abstraction enables MinIO locally and managed object storage in production |
| ML governance | Versioned data/model/evaluation artefacts; human review for uncertain or safety-relevant suggestions; no unsupported performance claims |

## 5. Assumptions and out of scope for Week 1

- A campus map/location source, campus SSO, notification provider, retention periods, and real training datasets require stakeholder decisions before implementation.
- Week 1 delivers design documentation only. Authentication, database migrations, UIs, ML models, and live notifications begin in later approved weeks.
