# GrievX 14-Week Roadmap

| Week | Focus | Deliverable and exit criteria |
| --- | --- | --- |
| 1 | Requirements, architecture, planning | Approved requirements, architecture, schema/API design, wireframes, roadmap, report; no app features |
| 2 | Project foundation | Monorepo/package skeletons, Docker Compose, environment templates, lint/test tooling, health checks, developer setup docs |
| 3 | Authentication and roles | JWT/refresh flow, password hashing, RBAC policies, users/roles migrations, protected route shells, auth tests |
| 4 | Complaint submission | Complaint/location/evidence schema and migrations, secure upload flow, student submission/tracking UI, integration tests |
| 5 | Admin complaint management | Queue/detail views, filtering, assignment/reassignment, audit events, role-scope tests |
| 6 | Lifecycle and notifications | Valid transitions, status history, resolution evidence/notes, notification jobs and in-app delivery, SLA visibility |
| 7 | Text classification | Label/data contract, TF-IDF + SVM baseline training/evaluation pipeline, model registry, advisory inference integration |
| 8 | Priority prediction | Feature contract, priority baseline, evaluation report, prediction review/override workflow |
| 9 | Department auto-routing | Routing model or evaluated baseline, department assignment suggestion/review, routing metrics |
| 10 | Computer vision | Image processing pipeline, feature extraction; detection only if labelled dataset supports it; evidence and latency evaluation |
| 11 | Resolution-time prediction | Historical-data eligibility checks, regression evaluation (MAE/quantiles), ETA display and uncertainty policy |
| 12 | Duplicate and incident clustering | Candidate retrieval/scoring, human incident review, merge/split audit trail, clustering evaluation protocol |
| 13 | Analytics, map, intelligence | Aggregations, dashboards, campus map/heatmap, department performance, privacy controls |
| 14 | Quality and deployment | End-to-end testing, security review, load/backup checks, production deployment guide, final documentation/demo |

## Weekly operating standard

Each week begins with repository/documentation inspection and ends with relevant tests, test results, documentation updates, `WEEKLY_REPORT.md`, runnable instructions, limitations, and a professor demonstration. A milestone cannot claim ML quality without an experiment tracked in the repository.

## Dependencies and decision gates

- Before Week 2: agree Node/Python version policy, package manager, environment names, and Docker availability.
- Before Week 3: choose local accounts versus campus SSO and define account provisioning.
- Before Week 4: approve location catalogue, permitted media formats/sizes, object-storage policy, and privacy notice.
- Before Weeks 7-12: obtain ethically usable labelled data, data dictionary, train/validation/test strategy, evaluation acceptance criteria, and compute budget.
- Before Week 13: approve map provider/data source, aggregation thresholds, and retention/privacy policy.
