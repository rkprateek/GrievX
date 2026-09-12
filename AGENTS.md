# GrievX Development Rules

## Scope and delivery

- Follow the approved 14-week roadmap. Do not begin a later week's feature without an explicit request.
- Inspect the repository, relevant documentation, and existing tests before changing code.
- Preserve existing behaviour and avoid unrelated refactors.
- Keep the mobile app, web apps, backend, infrastructure, and ML code in separate top-level packages once Week 2 scaffolding begins.
- Update the affected design documentation, `WEEKLY_REPORT.md`, and tests in the same change as a feature.

## Security and data

- Never commit secrets, credentials, tokens, `.env` files, or production data.
- Use environment variables and provide documented `.env.example` templates only.
- Hash passwords with a vetted password-hashing library; never log passwords or access tokens.
- Enforce authorization server-side for every protected action. UI visibility is not authorization.
- Validate all request payloads and uploads. Store media in object storage, not as database blobs.
- Treat complaint descriptions, locations, and images as sensitive operational data; minimize access and log administrative actions.

## API, database, and workflow

- Use FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, and S3-compatible object storage as documented in `docs/architecture.md`.
- Make schema changes through Alembic migrations; never alter a shared database manually.
- Use UUID primary keys, UTC timestamps, explicit status history, and immutable AI prediction records.
- Keep AI output advisory: authorized staff can review and override category, priority, route, and incident grouping, with an audit reason.
- Design idempotent creation and status-changing APIs where retries are likely.

## ML integrity

- Do not present a rule, heuristic, untrained model, or third-party paper result as a validated ML result.
- Version data, features, models, and evaluation runs. Record metrics, dataset split, and limitations before publishing a model.
- Require human review for low-confidence, safety-related, or ambiguous AI outputs.
- Keep ML inference interfaces independent of individual model frameworks so a baseline can be replaced safely.

## Quality

- Use meaningful names and small, cohesive modules. Add comments only for non-obvious decisions.
- Add tests for important behaviour and run the relevant test suite before concluding a weekly task.
- Document commands actually run and their result. Do not claim tests or deployment were run when they were not.
