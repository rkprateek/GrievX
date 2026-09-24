# Weekly Report

## Week 1 - Requirements, Architecture and Project Planning

### Completed

- Inspected the new repository and initialized Git because no repository existed.
- Added the provided CampusFix reference as `reference/CampusFix.pdf` and analyzed it as architectural inspiration.
- Produced functional and non-functional requirements, role definitions, frontend/backend/ML architecture, normalized PostgreSQL design, API groups, mobile and operations-dashboard wireframes, and the complete 14-week roadmap.
- Added project-specific engineering, security, data, ML integrity, and quality rules in `AGENTS.md`.

## Week 2 - Project Foundation

### Completed

- Created the Git-friendly monorepo foundation for mobile, admin, API, ML, and infrastructure work.
- Added the Expo student-app shell and Next.js operations-dashboard shell.
- Added FastAPI configuration, versioned routing, health endpoints, PostgreSQL, Redis, MinIO, and Docker Compose foundations.

### Verification

| Check | Result |
| --- | --- |
| Backend foundation tests | Pass - 3 passed, 1 skipped |
| Admin TypeScript validation | Pass |
| Docker Compose runtime | Not run - Docker unavailable in execution environment |
| Expo validation | Not run - dependency installation unavailable in execution environment |

## Week 3 - Authentication and Role Management

### Completed

- Implemented JWT authentication with environment-configured signing secret, algorithm, and expiration.
- Added Argon2 password hashing and verification; raw passwords are never persisted or returned.
- Added `student`, `staff`, `department_head`, and `admin` roles with users and departments.
- Added student registration, login, logout/token handling, `/auth/me`, protected routes, and backend role authorization.
- Added mobile student authentication with secure token storage and admin/staff role-aware dashboard access.
- Added authentication and authorization tests.

## Week 4 - Complaint Submission

### Completed

- Added `complaints`, `complaint_images`, and `complaint_status_history` persistence models.
- Added Alembic migration `0002_complaints`, linked after the Week 3 authentication migration.
- Implemented `POST /api/v1/complaints`, `GET /api/v1/complaints`, and `GET /api/v1/complaints/{id}`.
- Restricted complaint creation and reads to authenticated students and scoped reads to the student's own complaints.
- Added description validation, coordinate validation, optional location label validation, and authenticated-user enforcement.
- Added JPEG, PNG, and WebP validation using both declared MIME type and actual image content verification.
- Added a configurable 10 MiB default image-size limit.
- Added MinIO/S3-compatible evidence storage using generated object keys and safe metadata handling.
- Added cleanup of uploaded objects when the database transaction fails, preventing orphaned evidence objects.
- Every new complaint starts in `SUBMITTED` status and receives an initial status-history entry.
- Added mobile complaint reporting UI with description entry, camera capture, photo selection, current campus location capture, submission feedback, complaint ID display, and complaint history/detail viewing.
- Added multipart support to the mobile API client.
- Added backend tests for valid submission/retrieval, missing description, invalid image, unauthorized submission, image storage, and cross-student access isolation.

### Verification

| Check | Result |
| --- | --- |
| Complaint API implementation | Complete |
| Database migration | Added |
| MinIO storage integration | Complete |
| Validation/security controls | Added |
| Mobile complaint UI | Added |
| Complaint tests | Added |
| Full automated test execution | Pending execution in a Python 3.12 environment with project dependencies installed |
| Docker/MinIO live integration | Pending Docker-enabled environment |

### Week 4 boundary

No AI classification, prioritization, routing, duplicate detection, incident clustering, or other Week 5 functionality was implemented.


## Week 5 - Admin Complaint Management

### Completed

- Expanded complaint lifecycle support to `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, and `REJECTED`.
- Added complaint priority with manual `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL` values.
- Added department ownership and current staff assignment fields.
- Added `staff_assignments` history and `audit_logs` persistence through Alembic migration `0003_admin_complaint_management`.
- Added role-scoped admin complaint APIs for overview, queue search/filter/sort, detail, department/staff lookup, assignment, priority changes, status changes, and evidence-image viewing.
- Enforced lifecycle transition rules in the backend and return `409 Conflict` for invalid transitions.
- Admins have campus-wide visibility and assignment authority. Department Heads are limited to their department. Staff are limited to their department or explicitly assigned complaints. Students are denied admin-queue access.
- Reporter data exposed to operations is limited to non-secret identity information.
- Added a responsive Next.js operations dashboard with overview cards, queue filters/search/sort, complaint detail workspace, assignment controls, priority/status controls, location link, evidence viewer, and lifecycle timeline.
- Kept ML out of Week 5 as requested.

### Verification

| Check | Result |
| --- | --- |
| Admin complaint models and migration | Added |
| Admin/operations APIs | Added |
| RBAC and scope enforcement | Added |
| Status transition validation | Added |
| Assignment and audit history | Added |
| Responsive admin UI | Added |
| Admin access tests | Added |
| Staff restriction tests | Added |
| Assignment tests | Added |
| Status change tests | Added |
| Invalid transition tests | Added |
| ML functionality | Not implemented by design |

### Week 5 boundary

No ML classification, priority prediction, auto-routing, duplicate detection, incident clustering, or other Week 6+ functionality was implemented.
