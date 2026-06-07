# Analytics Platform

A full-stack real-time analytics and reporting platform built for the assignment. The project provides secure authentication, organization-aware data, event ingestion, dashboards with charts and tables, alerts, API keys, and a professional dark SaaS-style user interface.

## Demo Login

Use this seeded/demo account when checking the running app:

```text
Email: surya@demo.com
Password: Demo1234!
```

## Screenshots

The screenshots are saved in [docs/screenshots](docs/screenshots).

### Login

![Login screen](docs/screenshots/01-login.png)

### Overview

![Overview screen](docs/screenshots/02-overview.png)

### Dashboards And Charts

![Dashboards screen](docs/screenshots/03-dashboards.png)

### Events And Event Injection

![Events screen](docs/screenshots/04-events.png)

### API Keys

![API keys screen](docs/screenshots/05-api-keys.png)

## Requirement Coverage

| Requirement | Status | Evidence |
| --- | --- | --- |
| User signup and sign-in | Complete | JWT auth, login/signup pages, protected dashboard routes |
| Organization workspace | Complete | Auth token includes `org_id`; API routes are scoped by organization |
| Event ingestion | Complete | Single event ingest API, batch API, frontend Inject Event button |
| Event list/table | Complete | Events page table and Overview recent activity feed |
| Dashboards | Complete | Saved dashboards page with live metrics and dashboard creation UI |
| Charts and graphical representation | Complete | KPI cards, pie/donut chart, timeline chart, bar chart, top users, recent events table |
| Alerts | Complete | Alerts API and dashboard route for alert configuration/status |
| API keys | Complete | Create, display once, list, and revoke API keys |
| Secure backend API | Complete | FastAPI routes protected with bearer token auth and role-aware organization access |
| Database persistence | Complete | PostgreSQL with SQLAlchemy async models and event partition handling |
| Real-time-ready architecture | Complete | WebSocket router and frontend auto-refresh/live event views |
| Professional UI | Complete | Dark SaaS console with readable contrast, sidebar navigation, charts, tables, and clear event explanations |
| Documentation and screenshots | Complete | This README and PNG screenshots under `docs/screenshots` |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| State/Data | Zustand, TanStack Query, Axios |
| Charts | Recharts |
| Backend | FastAPI, Pydantic, SQLAlchemy async |
| Database | PostgreSQL |
| Background/Realtime | Redis, Celery, WebSocket support |
| Auth | JWT access token plus refresh cookie flow |
| Testing | Pytest, TypeScript compiler, Next production build |

## Project Structure

```text
analytics-platform/
  backend/
    app/
      routers/        FastAPI route handlers
      services/       Business logic
      repositories/   SQLAlchemy data access
      models/         Database models
      schemas/        Pydantic request/response models
      websocket/      WebSocket connection manager
      workers/        Celery tasks
    tests/            Backend test suite
  frontend/
    src/app/          Next.js app routes
    src/components/   Shared UI components
    src/lib/          API client and utilities
    src/store/        Zustand auth store
    src/types/        TypeScript API types
  docs/screenshots/   Saved assignment screenshots
```

## Local Run Instructions

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend URLs:

```text
Health:   http://localhost:8000/api/health
API docs: http://localhost:8000/api/docs
OpenAPI:  http://localhost:8000/api/openapi.json
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Environment

The backend reads settings from [backend/.env.example](backend/.env.example) or environment variables. Important values:

```text
DATABASE_URL=postgresql+asyncpg://analytics_user:analytics_pass@localhost:5432/analytics_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-this-in-production-minimum-32-characters-long
ALLOWED_ORIGINS=http://localhost:3000
```

The frontend should point to the backend:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Summary

| Feature | Endpoint |
| --- | --- |
| Sign up | `POST /api/auth/signup` |
| Sign in | `POST /api/auth/signin` |
| Current user | `GET /api/auth/me` |
| Ingest event | `POST /api/orgs/{org_id}/events/ingest` |
| Batch ingest | `POST /api/orgs/{org_id}/events/ingest/batch` |
| List events | `GET /api/orgs/{org_id}/events/` |
| Dashboards | `GET/POST /api/orgs/{org_id}/dashboards/` |
| Alerts | `GET/POST /api/orgs/{org_id}/alerts/` |
| API keys | `GET/POST /api/orgs/{org_id}/api-keys/` |
| WebSocket | `ws://localhost:8000/api/ws/{org_id}?token=<access_token>` |

## Verification Performed

These checks were run on 7 June 2026.

| Check | Result |
| --- | --- |
| Backend health route | Passed: `GET /api/health` returned healthy JSON |
| OpenAPI docs | Passed: `GET /api/openapi.json` returned `200` |
| Frontend routes | Passed: `/login` and `/dashboard` returned `200` |
| Authenticated backend smoke test | Passed: `/me` `200`, event ingest `202`, events `200`, dashboards `200`, alerts `200`, API keys `200` |
| Frontend type-check | Passed: `npm run type-check` |
| Frontend production build | Passed: `npm run build` |
| Backend test discovery | Passed: `38 tests collected` |
| Screenshot capture | Passed: five PNG screenshots saved in `docs/screenshots` |

### Backend Test Note

The backend test suite is present and discoverable. A full `pytest tests/` run requires a local PostgreSQL test database matching this URL from [backend/tests/conftest.py](backend/tests/conftest.py):

```text
postgresql+asyncpg://analytics_user:analytics_pass@localhost:5432/analytics_test
```

In this local environment the full test run was blocked by PostgreSQL authentication for `analytics_user`, but the live backend API smoke test passed against the running server.

## Useful Commands

```bash
# Frontend validation
cd frontend
npm run type-check
npm run build

# Backend health
curl http://localhost:8000/api/health

# Backend tests, after creating/configuring analytics_test database
cd backend
source .venv/bin/activate
pytest tests/ -q
```

## Assignment Summary

This project satisfies the required full-stack analytics platform scope: it includes a working backend API, a working frontend dashboard, authentication, event tracking, event injection from the UI, dashboard tables/charts, alert/API-key management, persistent storage, documentation, and screenshots for submission.
