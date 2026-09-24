# GrievX Notifications and Real-Time Updates

## Week 6 scope

Week 6 adds persistent complaint notifications and a real-time delivery channel without introducing ML or Week 7 functionality.

### Notification events

| Event | Persistent notification recipient |
| --- | --- |
| Complaint submitted | Student who submitted it |
| Department assigned | Active Department Heads in the assigned department |
| Staff assigned | Newly assigned staff member |
| Status changed | Student who submitted the complaint |
| Complaint resolved | Student who submitted the complaint |

A resolution also produces the normal STATUS_CHANGED notification, plus a dedicated COMPLAINT_RESOLVED notification.

### Notification persistence

The notifications table stores:

- id
- recipient_user_id
- optional complaint_id
- type
- title
- message
- read_at
- created_at

Notifications are only readable and markable as read by their recipient.

### HTTP API

- GET /api/v1/notifications
- GET /api/v1/notifications/unread-count
- PATCH /api/v1/notifications/{notification_id}/read

All notification APIs require an authenticated user.

### Real-time channel

The API exposes:

- WS /api/v1/ws/notifications?token=<JWT>

The WebSocket authenticates the JWT subject and creates a per-user connection. Two event shapes are used:

- notification — a persisted notification payload.
- complaint.updated — a scoped lifecycle update used by the student app and operations dashboard to refresh complaint state.

The current connection manager is intentionally single-process. The project already has Redis infrastructure, so the manager interface can later be backed by Redis pub/sub when horizontal API scaling is introduced.

### Security and authorization

- JWT authentication is required for the WebSocket.
- Notification reads are restricted to the recipient.
- Complaint lifecycle APIs retain the Week 5 role and department scope.
- Real-time complaint update events are sent only to the complaint's student and operators whose existing role/scope permits the complaint.
- Password hashes and tokens are never included in notification payloads.

### Client behavior

The student mobile app:

- displays current complaint status;
- displays every recorded lifecycle transition as a timeline;
- displays notifications in a dedicated Alerts tab;
- listens for WebSocket events and refreshes complaint data.

The admin dashboard:

- listens for scoped complaint lifecycle events;
- updates the visible queue without a manual page reload;
- keeps a 10-second polling fallback for cases where the WebSocket is unavailable.
