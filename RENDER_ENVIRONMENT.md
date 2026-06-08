# Render Environment Variables

Use this checklist when filling **Render -> Environment Variables** for the backend web service.

For where each URL comes from and where it is reused later, see [DEPLOYMENT_URLS_CHECKLIST.md](DEPLOYMENT_URLS_CHECKLIST.md).

Do not commit real passwords, database URLs with passwords, Redis URLs, or secret keys into GitHub. Paste real values only into the Render dashboard.

## Service Settings

Before adding env vars, make sure the Render service fields are:

```text
Name: analytics-platform-api
Language: Python 3
Branch: analytics-platform
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python -m alembic upgrade head && python -m app.seed_demo && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

## Environment Variables To Add

Add these one by one in Render.

| Key | Value To Put |
| --- | --- |
| `PYTHON_VERSION` | `3.11.9` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `SECRET_KEY` | A long random key from `openssl rand -hex 32` |
| `DATABASE_URL` | Neon pooled PostgreSQL URL, see below |
| `REDIS_URL` | Upstash TCP URL starting with `rediss://`, see below |
| `CELERY_BROKER_URL` | Same value as `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Same value as `REDIS_URL` |
| `ALLOWED_ORIGINS` | `https://temporary.vercel.app` for now |
| `FRONTEND_URL` | `https://temporary.vercel.app` for now |
| `DEMO_USER_EMAIL` | `surya@demo.com` |
| `DEMO_USER_PASSWORD` | `Demo1234!` |
| `DEMO_USER_NAME` | `Surya Demo` |
| `DEMO_ORGANIZATION_NAME` | `Demo Analytics Workspace` |

## DATABASE_URL Format

Use the Neon **pooler** host, not the normal host.

```text
postgresql://neondb_owner:<YOUR_NEON_PASSWORD>@ep-sweet-water-aqfcd1v5-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Replace only:

```text
<YOUR_NEON_PASSWORD>
```

Do not include labels like `Host`, `Database`, `Role`, or commas.

## REDIS_URL Format

In Upstash, open your Redis database, then go to:

```text
Connect -> TCP
```

Copy the URL that starts with:

```text
rediss://
```

It will look similar to:

```text
rediss://default:<UPSTASH_PASSWORD>@simple-worm-67933.upstash.io:6379
```

Use the same exact `rediss://...` value for:

```text
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

Do not use these REST values for this backend:

```text
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
```

## Generate SECRET_KEY

Run this locally and paste the output into Render as `SECRET_KEY`:

```bash
openssl rand -hex 32
```

## After Backend Deploys

When Render gives the backend URL, test:

```text
https://<your-render-service>.onrender.com/api/health
```

It should return:

```json
{"status":"healthy","version":"1.0.0"}
```

After Vercel gives the frontend URL, come back to Render and update:

```text
ALLOWED_ORIGINS=<your Vercel URL>
FRONTEND_URL=<your Vercel URL>
```

Then redeploy the backend once.