# Week 5 Admin Complaint Management

## Scope
This milestone implements the operations-side complaint queue and detail workflow. It does not implement ML.

## Roles
- Admin: campus-wide visibility, department/staff assignment, priority and status controls.
- Department Head: department-scoped visibility and lifecycle/priority operations.
- Staff: department or explicit-assignment visibility and lifecycle/priority operations.
- Student: no access to admin complaint-management endpoints.

## Complaint lifecycle
SUBMITTED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED, with REJECTED available from active intake/work states. RESOLVED may return to IN_PROGRESS for a reopened case.

## Main API operations
- GET /api/v1/admin/overview
- GET /api/v1/admin/complaints
- GET /api/v1/admin/complaints/{id}
- GET /api/v1/admin/complaints/{id}/images/{image_id}
- GET /api/v1/admin/complaints/departments
- GET /api/v1/admin/complaints/staff
- PATCH /api/v1/admin/complaints/{id}/assignment
- PATCH /api/v1/admin/complaints/{id}/priority
- PATCH /api/v1/admin/complaints/{id}/status

## UI
The Next.js dashboard provides overview cards, queue search/filter/sort, complaint details, permission-scoped student information, location, evidence viewing, assignment controls, priority/status controls, and lifecycle history.

## Verification
The Week 5 test suite covers admin access, staff scope restrictions, student denial, assignment, priority/status updates, and invalid status transitions.
