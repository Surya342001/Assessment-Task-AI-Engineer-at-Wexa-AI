# Production Deployment

This setup gives reviewers one durable frontend URL while the frontend proxies `/api/*` to the hosted FastAPI backend.

For the exact Render environment variables checklist, see [RENDER_ENVIRONMENT.md](RENDER_ENVIRONMENT.md).

## 1. Create Cloud Services

1. Create a Neon PostgreSQL database.
2. Copy the pooled connection string and convert it if needed:
   - `postgresql://...` is accepted by the backend and normalized automatically.
   - `sslmode=require` is accepted and normalized automatically.
3. Create an Upstash Redis database.
4. Copy the Redis URL. Prefer the TLS URL starting with `rediss://`.

## 2. Deploy Backend On Render

Use the repository blueprint at `render.yaml`, or create a Render Web Service manually with:

```bash
Root directory: backend
Build command: pip install -r requirements.txt
Start command: python -m alembic upgrade head && python -m app.seed_demo && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check path: /api/health
Python version: 3.11.9
```

Set these Render environment variables:

```text
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate a long random string>
DATABASE_URL=<Neon PostgreSQL URL>
REDIS_URL=<Upstash Redis URL>
CELERY_BROKER_URL=<Upstash Redis URL>
CELERY_RESULT_BACKEND=<Upstash Redis URL>
ALLOWED_ORIGINS=<your Vercel frontend URL after deploy>
FRONTEND_URL=<your Vercel frontend URL after deploy>
DEMO_USER_EMAIL=surya@demo.com
DEMO_USER_PASSWORD=Demo1234!
DEMO_USER_NAME=Surya Demo
DEMO_ORGANIZATION_NAME=Demo Analytics Workspace
```

The backend start command runs migrations and seeds the demo account automatically.

## 3. Deploy Frontend On Vercel

Import the same GitHub repository into Vercel and set the project root directory to:

```text
frontend
```

Set Vercel environment variables:

```text
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_WS_URL=
INTERNAL_API_URL=<your Render backend URL>
```

Leave `NEXT_PUBLIC_API_URL` empty. The browser will call `/api` on the Vercel domain, and Vercel/Next will proxy to `INTERNAL_API_URL`.

## 4. Final Backend Update

After Vercel gives you the frontend URL, update the backend variables in Render:

```text
ALLOWED_ORIGINS=<your Vercel frontend URL>
FRONTEND_URL=<your Vercel frontend URL>
```

Redeploy the backend once after changing those values.

## Demo Login

```text
Email: surya@demo.com
Password: Demo1234!
```