# Week 3 Authentication

## Roles

- `student`: student application access and personal resources.
- `staff`: assigned/department operational resources.
- `department_head`: department-wide operational resources.
- `admin`: campus-wide administrative resources.

## Endpoints

- `POST /api/v1/auth/register` — creates a student account only.
- `POST /api/v1/auth/login` — authenticates an existing active account.
- `POST /api/v1/auth/logout` — client-side token disposal endpoint; access tokens remain short-lived and stateless.
- `GET /api/v1/auth/me` — returns the authenticated user's safe profile.

## Token

JWT access tokens contain the user ID, role, issued-at time, expiration, and token ID. Signing configuration is supplied through environment variables (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`).

## Authorization

Protected routes use the shared `get_current_user` and `require_roles` dependencies. Authorization is enforced on the API, not trusted from mobile or dashboard UI state.

## Passwords

Passwords are hashed with Argon2. Raw passwords are never stored, logged, or returned in API responses.

## Local setup

Copy `services/api/.env.example` to the local environment and replace the placeholder JWT secret with a long random value. Install API dependencies with the project's normal Python package workflow, then run the Alembic migration before starting the API.
