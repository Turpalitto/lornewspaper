# LORNEWS — Free Deployment Guide

**Zero monthly cost.** Deploy the complete platform: frontend, API, database, vector search, and caching.

**Estimated time: 45 minutes**

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                      Cloudflare Pages                      │
│                   CDN · HTTPS · Free · Always On            │
│                    lornews.pages.dev                        │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend (static)                Backend (Render Free)   │
│  ┌──────────────────────┐        ┌────────────────────┐  │
│  │  Cloudflare Pages    │        │  Render Web Service │  │
│  │  · Global CDN        │────API─►  · Python FastAPI   │  │
│  │  · No cold starts    │  /api/ │  · Sleeps on idle   │  │
│  │  · Unlimited requests│  proxy │  · Wakes on request │  │
│  │  · Next.js static    │        │  · 512 MB RAM       │  │
│  └──────────────────────┘        └────────┬───────────┘  │
│                                           │              │
│  ┌──────────────┐  ┌──────────────┐  ┌────┴───────────┐  │
│  │  PostgreSQL  │  │  Upstash     │  │  Qdrant Cloud  │  │
│  │  Supabase    │  │  Redis       │  │  Vector DB     │  │
│  │  Free 500MB  │  │  Free 10MB   │  │  Free 1GB      │  │
│  │  No expiry   │  │  1000 cmd/d  │  │  1 node        │  │
│  └──────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

**All services are FREE.** No credit card required for Render, Supabase, or Qdrant. Upstash needs a card for verification only.

---

## Prerequisites

| Account | Sign Up URL | Required? | Cost |
|---------|-------------|-----------|------|
| GitHub | https://github.com/signup | ✅ Yes | Free |
| Cloudflare | https://dash.cloudflare.com/sign-up | ✅ Yes | Free (no credit card) |
| Render | https://render.com/register | ✅ Yes | Free (no credit card) |
| Supabase | https://supabase.com/dashboard/sign-up | ✅ Yes | Free (no credit card) |
| Upstash | https://console.upstash.com | ✅ Yes | Free (credit card for verification) |
| Qdrant Cloud | https://cloud.qdrant.io | ✅ Yes | Free (no credit card) |
| OpenAI | https://platform.openai.com | Optional | Pay-as-you-go (~$0.15/day for gpt-4o-mini) |

**Before you start:** Create all 5 accounts. This takes 10 minutes.

---

## Step 1: Fork the Repository

**Why:** Render needs access to your GitHub repository to deploy automatically.

1. Go to https://github.com/anomalyco/lornewspaper
2. Click the **Fork** button (top-right)
3. Select your GitHub account
4. Wait for the fork to complete (5 seconds)

You will now have `https://github.com/YOUR_USERNAME/lornewspaper`

---

## Step 2: Create Upstash Redis (Free 10MB)

**Why:** Redis is used for rate limiting and caching API responses. Without it, rate limiting defaults to in-memory (per-process).

1. Go to https://console.upstash.com
2. Click **Sign in with GitHub** (use your GitHub account)
3. Click **Create Database**
4. Fill in:
   - **Database Name:** `lornews-redis`
   - **Region:** Choose the closest one to you (e.g., `us-east-1`)
   - **Tier:** `Free` (10MB, 1000 commands/day — enough for rate limiting)
5. Click **Create**
6. On the database detail page, find the **UPSTASH_REDIS_REST_URL** or **Endpoint** field
7. **Copy the Redis URL.** It looks like: `redis://default:AVNS_xxxxx@xxxxx.upstash.io:6379`
   - ⚠️ Note: Some Upstash databases use `rediss://` (SSL). Use `rediss://` if available.

**Keep this tab open.** You'll need the URL in Step 5.

---

## Step 3: Create Qdrant Cloud Cluster (Free 1GB)

**Why:** Qdrant stores vector embeddings for semantic search. Without it, knowledge base search falls back to keyword matching.

1. Go to https://cloud.qdrant.io
2. Click **Sign in with GitHub**
3. Click **Create Cluster**
4. Fill in:
   - **Cluster Name:** `lornews`
   - **Configuration:** `Free` (1GB storage, 1 node)
   - **Cloud Provider:** `AWS`
   - **Region:** `us-east-1` (or closest to you)
5. Click **Create Cluster**
6. Wait 2-3 minutes for the cluster to provision
7. Click on the cluster name to open its details
8. Copy the **Cluster URL**. It looks like: `https://xxxxx-0000.us-east-1-0.aws.cloud.qdrant.io:6333`

**Keep this tab open.** You'll need the URL in Step 5.

---

## Step 4: Create Supabase PostgreSQL (Free 500MB)

**Why:** PostgreSQL stores document metadata, user preferences, and job queue state.
**Why Supabase instead of Render PostgreSQL:** Supabase free tier has no 90-day expiry. Render's free PostgreSQL is deleted after 90 days.

1. Go to https://supabase.com/dashboard/sign-up
2. Sign in with your GitHub account
3. Click **New Project**
4. Fill in:
   - **Name:** `lornews-db`
   - **Database Password:** Click **Generate** then **copy the password** (you will not see it again)
   - **Region:** Choose the closest to you (e.g., `us-east-1`)
   - **Pricing Plan:** `Free` (500MB storage, 2GB RAM — enough for metadata)
5. Click **Create New Project**
6. Wait 2-3 minutes for the database to provision
7. In the project dashboard, go to **Project Settings** → **Database**
8. Find the **Connection string** section
9. Copy the **URI** field. It looks like:
   `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`
   - ⚠️ Replace `PASSWORD` with the password you saved in step 4
   - ⚠️ Replace `/postgres` at the end with `/lornews`:
   `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/lornews`

**Keep this tab open.** You'll need this URL in Step 5.

⚠️ **Important:** Supabase gives you `postgresql://postgres:...@db.xxxxx.supabase.co:5432/postgres`
You MUST change `/postgres` to `/lornews` at the end. This creates a new database name.
Actually, you can use the default `postgres` database — it works fine. Just leave it as is:
`postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`

Also copy the **Host** (`db.xxxxx.supabase.co`) and **Password** separately — you may need them.

---

## Step 5: Create Render Backend Web Service

**Why:** This runs the Python FastAPI application that powers all API endpoints.

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub account (if not already connected)
4. Select the repository: `YOUR_USERNAME/lornewspaper`
5. Fill in:
   - **Name:** `lornews-backend`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```
     pip install -r requirements.txt && pip install -e . uvicorn[standard]
     ```
   - **Start Command:**
     ```
     uvicorn api.app:app --host 0.0.0.0 --port 10000
     ```
   - **Plan:** `Free`
6. Click **Add Environment Variable** and add each of these:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Generate: run `openssl rand -hex 64` in terminal (or use https://generate-secret.vercel.app/64) |
   | `API_DEBUG` | `false` |
   | `API_LOG_LEVEL` | `INFO` |
   | `API_CORS_ORIGINS` | `https://lornews-frontend.onrender.com` |
   | `TRUSTED_HOSTS` | `lornews-backend.onrender.com,*.onrender.com` |
   | `DATABASE_URL` | Paste the **Internal Database URL** from Step 4 |
   | `REDIS_URL` | Paste the Redis URL from Step 2 |
   | `QDRANT_URL` | Paste the Cluster URL from Step 3 |
   | `LLM_API_KEY` | Your OpenAI API key (or any LLM provider's key) |
   | `LLM_PROVIDER` | `openai` |
   | `LLM_MODEL` | `gpt-4o-mini` (cheapest option) |
   | `ENABLE_METRICS` | `true` |
   | `ENABLE_RATE_LIMIT` | `true` |
   | `ENABLE_COMPRESSION` | `true` |

7. Click **Create Web Service**
8. Wait 3-5 minutes for the build to complete
9. Once deployed, click the URL shown at the top of the page
   - It will be something like: `https://lornews-backend.onrender.com`
10. Test by visiting: `https://lornews-backend.onrender.com/api/v1/health`
    - Expected response: `{"status":"ok","version":"0.1.0","uptime_seconds":N,"timestamp":"..."}`

⚠️ **Important:** Copy the backend URL. You'll need it for Step 6.
It looks like: `https://lornews-backend.onrender.com`

---

## Step 6: Create Cloudflare Pages (Frontend)

**Why:** Cloudflare Pages is free, globally distributed CDN with zero cold starts.
Unlike Render free tier, Cloudflare Pages never sleeps and responds instantly.

### 6.1 Create Cloudflare Pages Project

1. Go to https://dash.cloudflare.com
2. Sign in with your Cloudflare account
3. Go to **Workers & Pages** (left sidebar)
4. Click **Create application** → **Pages** → **Connect to Git**
5. Click **Connect GitHub** (authorize Cloudflare to access your GitHub)
6. Select your repository: `YOUR_USERNAME/lornewspaper`
7. Click **Begin setup**

### 6.2 Configure Build

Fill in:
   - **Project name:** `lornews` (this becomes your URL: `lornews.pages.dev`)
   - **Production branch:** `main`
   - **Framework preset:** `Next.js` (⚠️ If not in the dropdown, select "None" and configure manually)
   - **Build command:**
     ```
     cd web && npm ci && npm run build
     ```
   - **Build output directory:** `.next` (⚠️ Wait — Cloudflare Pages needs a static output. Next.js `output: "standalone"` is not static.)

### 6.3 Important: Static Export

Cloudflare Pages serves **static files only**. The current next.config.ts uses `output: "standalone"` which requires a Node.js server.

**You have two options:**

**Option A: Switch to static export (recommended for free tier)**
In `web/next.config.ts`, change:
```ts
output: "standalone",
```
to:
```ts
output: "export",
images: { unoptimized: true },
```

Then set the build output directory to `out`.

```
cd web && npm ci && npm run build
```
Build output directory: `web/out`

**Option B: Keep dynamic routes**
If you need SSR (server-side rendering), use Cloudflare Pages with `@cloudflare/next-on-pages`. This is more complex.
For this guide, we use **Option A (static export)**.

### 6.4 Environment Variables

Click **Environment variables (advanced)** and add:

| Key | Value | Branch |
|-----|-------|--------|
| `NODE_VERSION` | `22` | Production |
| `NEXT_PUBLIC_API_URL` | `https://lornews-backend.onrender.com` | Production |

### 6.5 API Proxy Configuration

Since Cloudflare Pages serves static files, `/api/v1/*` requests need to be proxied to Render.

Create a file at `web/_redirects` (this tells Cloudflare Pages how to route requests):

```
/api/v1/*  https://lornews-backend.onrender.com/api/v1/:splat  200
```

⚠️ **Important:** This `_redirects` file must be in the `public/` directory of the Next.js app so it's copied to the output.

Create the file: `web/public/_redirects` with content:
```
/api/v1/*  https://lornews-backend.onrender.com/api/v1/:splat  200
```

### 6.6 Deploy

1. Click **Save and Deploy**
2. Wait 2-3 minutes for the build to complete
3. Once deployed, click the URL: `https://lornews.pages.dev`

### Verify Frontend

1. Visit `https://lornews.pages.dev`
   - ✅ You should see the LORNEWS home page with 4 quick action cards
2. Visit `https://lornews.pages.dev/search`
   - ✅ You should see the search page with input field
3. Visit `https://lornews.pages.dev/api/v1/health`
   - ✅ This should proxy to Render and return the health JSON

⚠️ **Unlike Render, Cloudflare Pages loads instantly.** No cold start delay.

---

## Step 7: Verify End-to-End

### 7.1 Backend Health
```bash
curl https://lornews-backend.onrender.com/api/v1/health
# Expected: {"status":"ok","version":"0.1.0",...}
```

### 7.2 API Docs
```bash
# Open in browser:
https://lornews-backend.onrender.com/api/v1/docs
# You should see Swagger UI with all endpoints
```

### 7.3 Search API
```bash
curl -X POST https://lornews-backend.onrender.com/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"hearing loss","max_results":3}'
# Expected: {"articles":[...],"total":N,"elapsed_ms":N}
```

### 7.4 Metrics Endpoint
```bash
curl https://lornews-backend.onrender.com/metrics
# Expected: Prometheus-formatted metrics starting with "# HELP lornews_..."
```

### 7.5 Frontend Loads
Open `https://lornews-frontend.onrender.com` in a browser.
- ✅ Home page renders
- ✅ Navigation links work
- ✅ Dark/light theme toggle works

### 7.6 Frontend API Proxy
The frontend proxies `/api/v1/*` to the backend. Test this:

Visit: `https://lornews-frontend.onrender.com/api/v1/health`

Expected: Same JSON response as the backend health endpoint.
If this fails, the `NEXT_PUBLIC_API_URL` environment variable is wrong in Step 6.

---

## Step 8: Set Up Automatic Deployments

### 8.1 Render Auto-Deploy (Already Done)

Render automatically deploys when you push to the `main` branch of your forked repository.

**To trigger a redeploy:**
```bash
git commit --allow-empty -m "chore: trigger deploy"
git push origin main
```

### 8.2 GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` for CI before deploy:

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -X POST https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_DEPLOY_KEY }}
```

This requires Render Deploy Hook URL from: Dashboard → Service → Settings → Deploy Hook.

---

## Step 9: Daily Pipeline (Cron Job)

**Why:** To automatically discover, digest, and publish new research every day.

### Using a Free Cron Service (cron-job.org)

1. Go to https://cron-job.org
2. Sign up (free, no credit card)
3. Click **Create Cronjob**
4. Fill in:
   - **Title:** `LORNEWS Daily Pipeline`
   - **URL:** `https://lornews-backend.onrender.com/api/v1/pipeline/daily`
   - **Method:** `POST`
   - **Schedule:** `Every day at 06:00`
5. Click **Create**

For Telegram delivery, also set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in Render dashboard (backend environment variables).

---

## Step 10: Environment Summary

### Backend (Render lornews-backend)

| Variable | Value | Where to Get It |
|----------|-------|-----------------|
| `SECRET_KEY` | 64-char hex | `openssl rand -hex 64` |
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres` | Supabase dashboard → Project Settings → Database → Connection string |
| `REDIS_URL` | `redis://...` | Upstash dashboard → Redis URL |
| `QDRANT_URL` | `https://...:6333` | Qdrant Cloud dashboard → Cluster URL |
| `LLM_API_KEY` | `sk-proj-...` | https://platform.openai.com/api-keys |
| `API_CORS_ORIGINS` | `https://lornews.pages.dev` | Your Cloudflare Pages URL |
| `TRUSTED_HOSTS` | `lornews-backend.onrender.com,*.onrender.com` | Your backend URL |
| `ENABLE_RATE_LIMIT` | `true` | Fixed |
| `ENABLE_METRICS` | `true` | Fixed |

### Frontend (Cloudflare Pages)

| Variable | Value | Where to Get It |
|----------|-------|-----------------|
| `NEXT_PUBLIC_API_URL` | `https://lornews-backend.onrender.com` | Backend URL from Step 5 |
| `NODE_VERSION` | `22` | Fixed |

---

## Deployment Checklist

### Required
- [ ] GitHub repository forked
- [ ] Upstash Redis created (URL copied)
- [ ] Qdrant Cloud cluster created (URL copied)
- [ ] Supabase PostgreSQL created (URL copied)
- [ ] Render backend deployed (health endpoint ✅)
- [ ] Cloudflare Pages deployed (`web/public/_redirects` created, home page ✅)

### Configuration
- [ ] `SECRET_KEY` is a random 64-char string (not `change-me-in-production`)
- [ ] `API_CORS_ORIGINS` points to the frontend URL
- [ ] `TRUSTED_HOSTS` includes the backend URL
- [ ] `NEXT_PUBLIC_API_URL` points to the backend URL
- [ ] `API_DEBUG` is `false`

### Verification
- [ ] `GET /api/v1/health` returns 200
- [ ] `GET /api/v1/liveness` returns 200
- [ ] `GET /api/v1/readiness` returns 200
- [ ] `GET /metrics` returns Prometheus text
- [ ] `POST /api/v1/search` returns articles
- [ ] Frontend loads without errors
- [ ] Frontend API proxy works (`/api/v1/health` from frontend URL)
- [ ] Dark/light theme toggle works
- [ ] Navigation links work

### Optional
- [ ] OpenAI API key set (for RAG question answering)
- [ ] Telegram bot configured (for daily digest delivery)
- [ ] Cron job created (for daily pipeline)
- [ ] Custom domain configured (via Cloudflare or Render)

---

## Troubleshooting

### Frontend shows blank page
- Check Cloudflare Pages build logs: Dashboard → Pages → lornews → View build
- Common cause: `NEXT_PUBLIC_API_URL` is wrong in Cloudflare Pages environment variables
- Common cause: `_redirects` file is missing from `web/public/` directory
- Cloudflare Pages never sleeps — if it fails, it's a build error, not a cold start

### Backend health check fails
- Check Render logs: Dashboard → lornews-backend → Logs
- Common cause: `SECRET_KEY` is missing or default
- Run `curl https://lornews-backend.onrender.com/api/v1/health` and check the response

### Database connection fails
- Make sure `DATABASE_URL` uses the Supabase connection string format:
  `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`
- Check that the password is URL-encoded (e.g., `@` → `%40`, `#` → `%23`)

### Redis connection fails
- Verify the `REDIS_URL` format: `redis://default:password@endpoint.upstash.io:6379`
- Some Upstash instances use `rediss://` (SSL) instead of `redis://`

### Rate limiting too strict
- In Render dashboard, set `RATE_LIMIT_PER_MINUTE` to a higher value
- Without Redis, rate limiting is per-process (in-memory)

### Costs

| Service | Free Tier Limit | What Happens at Limit |
|---------|----------------|----------------------|
| Cloudflare Pages | Unlimited requests, 500 builds/mo | Builds queue until next month |
| Render Web Service | 750 hours/month | Service sleeps for rest of month |
| Supabase PostgreSQL | 500MB, no expiry | Cannot insert new data |
| Upstash Redis | 10MB, 1000 commands/day | Commands rejected until next day |
| Qdrant Cloud | 1GB, 1 node | Cannot upsert new vectors |
| OpenAI API | Pay-as-you-go (~$0.15/day) | API returns 402 payment required |

---

## Upgrading from Free

When you outgrow the free tier, upgrade in this order:

1. **Supabase Pro** ($25/mo) — 8GB PostgreSQL, no row limits
2. **Render Web Service Starter** ($7/mo) — no sleep, 24/7 uptime
3. **Qdrant Cloud Standard** ($25/mo) — 10GB, higher throughput
4. **Custom domain** ($10/yr + Cloudflare Free for DNS)

---

## Complete Service List

| Service | URL | Purpose | Free Tier |
|---------|-----|---------|-----------|
| Frontend | https://lornews.pages.dev | User interface (Cloudflare CDN) | ✅ |
| Backend API | https://lornews-backend.onrender.com | REST API | ✅ |
| API Docs | https://lornews-backend.onrender.com/api/v1/docs | Swagger UI | ✅ |
| Database | postgresql://...@lornews-db.internal:5432/lornews | PostgreSQL | ✅ |
| Redis | redis://...@xxxxx.upstash.io:6379 | Rate limiting + cache | ✅ |
| Vector DB | https://xxxxx.cloud.qdrant.io:6333 | Vector storage | ✅ |
| GitHub | https://github.com/YOUR_USERNAME/lornewspaper | Source code | ✅ |
| Cron | https://cron-job.org | Daily pipeline trigger | ✅ |
