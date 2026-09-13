# GrievX

AI-powered multimodal campus complaint and incident management system.

## Week 2 development foundation

The repository contains an Expo mobile app, Next.js operations dashboard, FastAPI service, and Docker Compose dependencies for PostgreSQL, Redis, and MinIO. Authentication, complaints, and ML features deliberately begin in later weeks.

### Prerequisites

- Docker Desktop with Docker Compose
- Node.js 20.18+ and npm 10+
- Python 3.12+

### Start the local stack

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the admin shell at `http://localhost:3000`, FastAPI docs at `http://localhost:8000/docs`, MinIO console at `http://localhost:9001`, and check readiness at `http://localhost:8000/api/v1/health/ready`.

The Expo app runs on the host because it needs the Expo development server:

```powershell
npm install
npm run dev:mobile
```

For a physical device, set `EXPO_PUBLIC_API_BASE_URL` in `apps/mobile/.env` to your computer's LAN address, not `localhost`.

### Backend tests

```powershell
cd services/api
python -m pip install -e ".[dev]"
pytest
```

See [docs/development.md](docs/development.md) for service configuration and troubleshooting.
