# Deployment URLs Checklist

Use this file to know **where each URL comes from** and **where to paste it** during deployment.

Do not commit real passwords, Redis tokens, database URLs with passwords, or secret keys. Paste real secret values only into Render/Vercel dashboards.

## URL Flow

```text
Neon PostgreSQL URL  -> Render DATABASE_URL
Upstash Redis URL    -> Render REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
Render Backend URL   -> Vercel INTERNAL_API_URL
Vercel Frontend URL  -> Render ALLOWED_ORIGINS, Render FRONTEND_URL
Vercel Frontend URL  -> Final URL to send to reviewers
```

## 1. Neon Database URL

Get it from:

```text
Neon Console -> Project -> Connection string
```

Use the **pooler host** version for Render.

Paste this into Render:

```text
Key: DATABASE_URL
Value: postgresql://neondb_owner:<YOUR_NEON_PASSWORD>@ep-sweet-water-aqfcd1v5-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Replace only:

```text
<YOUR_NEON_PASSWORD>
```

Do not paste extra copied text like:

```text
Host
Database
Role
Password
Pooler host
```

## 2. Upstash Redis TCP URL

Get it from:

```text
Upstash Console -> Redis database -> Connect -> TCP tab
```

Copy the URL that starts with:

```text
rediss://
```

It will look like:

```text
rediss://default:<UPSTASH_PASSWORD>@<UPSTASH_HOST>:6379
```

Paste the same full `rediss://...` URL into Render three times:

```text
Key: REDIS_URL
Value: <UPSTASH_TCP_REDISS_URL>

Key: CELERY_BROKER_URL
Value: <UPSTASH_TCP_REDISS_URL>

Key: CELERY_RESULT_BACKEND
Value: <UPSTASH_TCP_REDISS_URL>
```

Do not use these REST values for this backend:

```text
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
```

## 3. Render Backend URL

Get it after Render backend deployment finishes.

It will look like:

```text
https://analytics-platform-api.onrender.com
```

Test it in the browser:

```text
https://analytics-platform-api.onrender.com/api/health
```

Expected response:

```json
{"status":"healthy","version":"1.0.0"}
```

Paste the Render backend URL into Vercel:

```text
Key: INTERNAL_API_URL
Value: https://analytics-platform-api.onrender.com
```

Do not add `/api` at the end. Use only the base backend URL.

## 4. Vercel Frontend URL

Get it after Vercel frontend deployment finishes.

It will look like:

```text
https://analytics-platform-xxxx.vercel.app
```

This is the final hosted URL you send to reviewers:

```text
https://analytics-platform-xxxx.vercel.app/login
```

After Vercel gives this URL, go back to Render and update:

```text
Key: ALLOWED_ORIGINS
Value: https://analytics-platform-xxxx.vercel.app

Key: FRONTEND_URL
Value: https://analytics-platform-xxxx.vercel.app
```

Then redeploy the Render backend once.

## 5. Temporary Placeholder URLs

Before Vercel is created, Render needs temporary values:

```text
ALLOWED_ORIGINS=https://temporary.vercel.app
FRONTEND_URL=https://temporary.vercel.app
```

After Vercel deploys, replace both with the real Vercel frontend URL.

## 6. Vercel Environment Variables

In Vercel, set:

```text
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_WS_URL=
INTERNAL_API_URL=<YOUR_RENDER_BACKEND_URL>
```

Leave `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` empty.

## 7. Final Reviewer URL

Send reviewers only this URL:

```text
https://<your-vercel-frontend-url>/login
```

Demo login:

```text
Email: surya@demo.com
Password: Demo1234!
```

## Quick Copy Checklist

Render backend env vars:

```text
PYTHON_VERSION=3.11.9
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<GENERATED_SECRET_KEY>
DATABASE_URL=<NEON_POOLER_DATABASE_URL>
REDIS_URL=<UPSTASH_TCP_REDISS_URL>
CELERY_BROKER_URL=<UPSTASH_TCP_REDISS_URL>
CELERY_RESULT_BACKEND=<UPSTASH_TCP_REDISS_URL>
ALLOWED_ORIGINS=https://temporary.vercel.app
FRONTEND_URL=https://temporary.vercel.app
DEMO_USER_EMAIL=surya@demo.com
DEMO_USER_PASSWORD=Demo1234!
DEMO_USER_NAME=Surya Demo
DEMO_ORGANIZATION_NAME=Demo Analytics Workspace
```

Vercel frontend env vars:

```text
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_WS_URL=
INTERNAL_API_URL=<YOUR_RENDER_BACKEND_URL>
```