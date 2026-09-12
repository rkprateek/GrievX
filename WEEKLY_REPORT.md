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
