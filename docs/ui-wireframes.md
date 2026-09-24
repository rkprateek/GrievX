# GrievX Initial UI Wireframes

These low-fidelity wireframes establish information hierarchy and flows for later UI implementation. They are not working screens and intentionally avoid fake data.

## 1. Student mobile application

### Home

```text
+----------------------------------+
| GrievX                    (bell) |
| Good morning, Student             |
|                                  |
| [ + Report a campus issue ]      |
|                                  |
| My recent complaints              |
| +------------------------------+ |
| | REF-...  In progress         | |
| | Lighting issue - Block A     | |
| +------------------------------+ |
| [View all complaints]            |
|                                  |
| Help / emergency guidance        |
+----------------------------------+
| Home       Report       Profile  |
+----------------------------------+
```

### Create complaint: progressive form

```text
+----------------------------------+
| < Report an issue           2/3  |
|                                  |
| What happened?                   |
| [Title________________________]  |
| [Describe the issue...________]  |
|                                  |
| Where is it?                     |
| [ Select campus location       >]|
| [ Use current location          ]|
|                                  |
| Evidence (optional)              |
| [ Camera ] [ Photo library ]     |
| [ thumbnail ] [ thumbnail ]      |
|                                  |
| [ Continue ]                     |
+----------------------------------+
```

The review step displays entered content, location accuracy/privacy notice, upload/analysis state, and a clear `Submit complaint` action. The app must offer a prominent emergency instruction for immediately dangerous situations rather than implying the complaint queue is emergency response.

### Complaint detail and timeline

```text
+----------------------------------+
| < REF-2026-000123         (more) |
| Plumbing issue                    |
| [HIGH] [In progress]              |
| Department: Plumbing              |
| Estimated update: when available  |
|                                  |
| Evidence carousel                 |
|                                  |
| Timeline                          |
| o Submitted                       |
| o Triaged                         |
| o Assigned                        |
|                                  |
| [Add requested information]       |
+----------------------------------+
```

## 2. Operations web dashboard

### Queue dashboard

```text
+--------------------------------------------------------------------------------+
| GrievX | Dashboard  Complaints  Incidents  Map  Analytics      Admin  (avatar) |
+-----------+--------------------------------------------------------------------+
| Filters   | Complaints                                      [Export policy]    |
| Status v  | [ Search reference, title, location...                         ]    |
| Priority  | [Status] [Department] [Priority] [Date] [AI review] [Clear]        |
| Dept v    |                                                                    |
| Date v    | REF        Title / location          Status       Priority  SLA    |
|           | 123        Leak, Block A              In progress  High      At risk|
|           | 124        Wi-Fi outage, Library      Triaged      Medium    On time|
|           |                                                                    |
|           | < Prev  1  2  Next >                                         |
+-----------+--------------------------------------------------------------------+
```

Role-aware filters restrict Staff and Department Heads to their permitted queues. Table rows use text labels and icons, not color alone.

### Complaint detail workspace

```text
+--------------------------------------------------------------------------------+
| < Queue | REF-...  [High] [In progress]            [Assign] [Change status]   |
+-------------------------------------------+------------------------------------+
| Report                                    | Activity                           |
| Title, description, reported location     | timeline / assignments / comments  |
| Map preview / evidence gallery             |                                    |
|                                            | AI assistance                       |
| Reporter data (role-permitted)             | category / route / priority / ETA  |
|                                            | confidence + model version          |
| Resolution notes + evidence                | [Accept] [Override with reason]    |
+-------------------------------------------+------------------------------------+
```

### Admin intelligence screens

- **Dashboard:** accessible metric cards (open, at risk, resolved, new), trend chart, department workload, and incident alerts. Each metric links to a filtered queue.
- **Map:** filter rail, clustered markers/heat layer, privacy-safe aggregation at low zoom, complaint/incident side panel.
- **Incidents:** candidate group list, similarity evidence, confirm/reject/merge/split controls with mandatory reason and audit trail.
- **Administration:** departments, users, roles, model versions, and audit viewer; Super Admin-only controls are visually distinct and confirmation-protected.

## 3. UX rules for later implementation

- Always show status in words, not just color; support screen readers and keyboard users on web.
- State what AI did, model/version availability, and how a human overrode it; avoid conveying unvalidated suggestions as fact.
- Use loading, empty, error, permission-denied, offline, and retry states in every feature specification.
- Ensure mobile capture has consent/permission explanations and preserves a draft on transient network failure.


## 4. Week 5 implemented operations UI

The Next.js operations dashboard now implements the complaint-management flow rather than only the Week 2 shell.

- **Dashboard overview:** total, submitted, in-progress, and resolved counters.
- **Complaint queue:** search by complaint/student, status and priority filters, department filter, sorting, refresh, and responsive table.
- **Complaint detail:** description, status, priority, reporter information, department/staff assignment, campus coordinates, map link, evidence list, and status history.
- **Operations controls:** admins can assign/reassign departments and staff; admins, staff, and department heads can change priority and status within their permitted scope.
- **Evidence viewer:** image metadata is shown in the detail panel and the API provides a short-lived object-storage URL on request.
- **Responsive behavior:** desktop queue/detail workspace collapses into stacked panels on smaller screens; mobile-sized controls remain usable without relying on color alone.
- **Security:** frontend role visibility is only a usability layer; FastAPI enforces the actual permission scope.
