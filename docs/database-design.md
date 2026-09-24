# GrievX PostgreSQL Database Design

## 1. Conventions

- PostgreSQL 16+; SQLAlchemy models and Alembic migrations will implement this design in a later week.
- Primary keys are `uuid`; timestamps are `timestamptz` in UTC; mutable records have `created_at` and `updated_at`.
- Enumerations are implemented as PostgreSQL enums or validated text values by migration decision: `user_status`, `complaint_status`, `priority`, `prediction_type`, `incident_status`, `notification_status`.
- Evidence is stored in object storage. Database rows retain opaque object keys, MIME type, bytes, checksum, and scan status.

## 2. Core tables

| Table | Key fields | Purpose and constraints |
| --- | --- | --- |
| `roles` | `id`, `code` (unique), `name`, `description` | Fixed system roles: student, staff, department_head, admin, super_admin |
| `users` | `id`, `email` (unique, case-insensitive), `password_hash`, `display_name`, `status`, `last_login_at` | Account identity; password hash nullable only for external SSO accounts |
| `user_roles` | `user_id`, `role_id` (composite PK), `assigned_by_id`, `assigned_at` | Supports future multi-role users without duplicating accounts |
| `departments` | `id`, `code` (unique), `name`, `email`, `is_active`, `head_user_id` | Operational departments, including Electrical, IT/Network, Plumbing, Housekeeping, Civil/Maintenance, Hostel, Other |
| `department_memberships` | `department_id`, `user_id`, `membership_role`, `is_active` | Staff/department-head scope; unique active association policy enforced by migration/query |
| `campus_locations` | `id`, `code` (unique), `name`, `building`, `floor`, `latitude`, `longitude`, `geography` | Managed location catalogue; PostGIS `geography(Point,4326)` is recommended for proximity queries |
| `complaints` | `id`, `reference_number` (unique), `reporter_id`, `title`, `description`, `location_id`, `latitude`, `longitude`, `category_code`, `priority`, `status`, `department_id`, `assigned_staff_id`, `submitted_at`, `resolved_at`, `closed_at`, `version` | Transactional complaint record; nullable coordinates support non-map reports; optimistic-lock `version` prevents conflicting edits |
| `complaint_images` | `id`, `complaint_id`, `object_key` (unique), `original_filename`, `mime_type`, `byte_size`, `sha256`, `scan_status`, `uploaded_by_id`, `kind` | Student and resolution evidence; `kind` is `report` or `resolution` |
| `complaint_status_history` | `id`, `complaint_id`, `from_status`, `to_status`, `changed_by_id`, `reason`, `metadata`, `created_at` | Append-only lifecycle history |
| `staff_assignments` | `id`, `complaint_id`, `staff_id`, `assigned_by_id`, `department_id`, `assignment_status`, `assigned_at`, `unassigned_at`, `reason` | Assignment history; only one active assignment per complaint enforced with partial unique index |
| `ai_predictions` | `id`, `complaint_id`, `prediction_type`, `model_version_id`, `status`, `output`, `confidence`, `input_fingerprint`, `created_at`, `reviewed_by_id`, `reviewed_at`, `override_value`, `override_reason` | Immutable inference outputs and human review; JSONB `output` holds structured labels/features safely |
| `notifications` | `id`, `user_id`, `complaint_id`, `channel`, `event_type`, `title`, `body`, `payload`, `status`, `sent_at`, `read_at`, `failure_reason` | In-app notification source of truth; delivery attempts are retryable |
| `incidents` | `id`, `reference_number` (unique), `title`, `summary`, `category_code`, `status`, `priority`, `location_id`, `centroid`, `opened_at`, `resolved_at`, `created_by_id` | Master real-world issue, human-governed |
| `incident_complaints` | `incident_id`, `complaint_id` (composite PK), `relationship_type`, `linked_by_id`, `linked_at`, `similarity_evidence` | Junction table; links preserve suggested/confirmed/rejected decision evidence |
| `model_versions` | `id`, `model_key`, `version`, `framework`, `artifact_uri`, `data_snapshot_id`, `feature_schema_version`, `evaluation_uri`, `rollout_state`, `metrics`, `activated_at`, `retired_at` | Version registry; unique `(model_key, version)` |
| `audit_logs` | `id`, `actor_id`, `action`, `resource_type`, `resource_id`, `before_state`, `after_state`, `reason`, `request_id`, `ip_hash`, `created_at` | Append-only operational audit record; do not store secrets or raw tokens |
| `refresh_tokens` | `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`, `device_label` | Rotating refresh-token sessions; store only hashes |

## 3. Relationships

```text
users --< user_roles >-- roles
users --< department_memberships >-- departments
users --< complaints (reporter)           departments --< complaints
complaints --< complaint_images
complaints --< complaint_status_history
complaints --< staff_assignments >-- users
complaints --< ai_predictions >-- model_versions
complaints --< incident_complaints >-- incidents
users --< notifications; complaints --< notifications
users --< audit_logs
```

## 4. Integrity rules and indexes

- Complaint `reference_number` and incident `reference_number` are human-readable, generated server-side, and immutable.
- State transitions are checked by the application service; each successful transition inserts `complaint_status_history` in the same transaction.
- `complaint_images.byte_size` is constrained to the configured maximum; type/signature validation occurs before insert.
- Required indexes: `complaints(reporter_id, submitted_at desc)`, `complaints(department_id, status, priority, submitted_at)`, `complaints(status, submitted_at)`, `complaints(location_id)`, `complaint_status_history(complaint_id, created_at)`, `notifications(user_id, read_at, created_at desc)`, and `ai_predictions(complaint_id, prediction_type, created_at desc)`.
- With PostGIS: GIST indexes on complaint and incident geography/centroids; otherwise use indexed latitude/longitude bounding-box prefiltering.
- A partial unique index ensures one active `staff_assignments` row per complaint. Incident membership is unique per `(incident_id, complaint_id)`.

## 5. Lifecycle retention

Soft-delete is not used for auditable complaints. User account deactivation preserves required operational history. Evidence and personal data retention/deletion schedules require campus policy approval before implementation; object deletion must be coordinated with database records and audit logging.


## 6. Week 5 implemented schema additions

Migration `0003_admin_complaint_management` extends the Week 4 complaint record with:

- `priority` with default `MEDIUM`.
- `department_id` for operational ownership.
- `assigned_staff_id` for current staff assignment.

It also creates:

- `staff_assignments` for assignment history.
- `audit_logs` for append-only administrative actions.

The implemented lifecycle statuses are `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, and `REJECTED`. Every successful status change records the previous and next state in `complaint_status_history`.

The current implementation uses the existing repository's integer department identifiers and string UUID user/complaint identifiers; the broader design above remains the target model for later normalization work.

## 7. Week 6 implemented notification schema

Migration 0004_notifications creates the implemented notifications table:

| Field | Purpose |
| --- | --- |
| id | Notification UUID |
| recipient_user_id | Authenticated recipient |
| complaint_id | Optional related complaint |
| type | Notification event type |
| title | Short notification heading |
| message | Human-readable notification body |
| read_at | Null until the recipient marks it read |
| created_at | UTC creation timestamp |

Indexes support recipient, complaint, and notification-type lookups. Foreign keys preserve referential integrity.

Notification rows are the in-app source of truth. WebSocket delivery is an additional real-time transport and is not required for historical notification retrieval.

### Week 6 lifecycle integrity

The implemented service records each successful status transition and creates the relevant notification(s) in the same transaction. Real-time publication happens after commit, so a failed database transaction does not intentionally publish a lifecycle event.