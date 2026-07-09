# Deployment Guide

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 22+
- PostgreSQL 16+ (optional, uses SQLite by default)
- Redis 7+ (optional)

### Backend
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Set env vars
export API_DEBUG=true
export LLM_PROVIDER=ollama

# Run
uvicorn api.app:app --reload --port 8000
```

### Frontend
```bash
cd web
npm install
npm run dev
```

### Services (via docker compose)
```bash
# Start infrastructure only
docker compose up postgres redis qdrant -d

# Start everything including optional services
docker compose --profile optional up -d
```

---

## Docker Deployment

### Build
```bash
# Backend
docker build -t lornews-backend:latest .

# Frontend
docker build -t lornews-frontend:latest ./web

# Or both via compose
docker compose build
```

### Run
```bash
# Full stack
docker compose --profile optional up -d

# Verify
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

---

## Railway

Railway uses `railway.json` or detects Dockerfiles automatically.

1. Create two services in Railway dashboard:
   - **lornews-backend** — root `Dockerfile`
   - **lornews-frontend** — `web/Dockerfile`

2. Add infrastructure:
   - PostgreSQL plugin
   - Redis plugin

3. Set environment variables from `.env.example`

4. Deploy from GitHub via Railway integration

### Backend health check
Railway health check path: `/api/v1/health`

### Frontend health check
Railway health check path: `/api/v1/health`

---

## Fly.io

### Prerequisites
```bash
flyctl auth login
```

### Backend
```bash
# Create app
flyctl launch --name lornews-backend --dockerfile Dockerfile --no-deploy

# Set secrets
flyctl secrets set SECRET_KEY=<random-64-char-string>
flyctl secrets set LLM_API_KEY=<your-key>
flyctl secrets set DATABASE_URL=<postgres-url>

# Deploy
flyctl deploy

# Scale
flyctl scale count 2
flyctl scale memory 1024
```

### Frontend
```bash
# Create app
flyctl launch --name lornews-frontend --dockerfile web/Dockerfile --no-deploy

# Set env
flyctl secrets set NEXT_PUBLIC_API_URL=https://lornews-backend.fly.dev

# Deploy
flyctl deploy
```

### PostgreSQL on Fly
```bash
flyctl postgres create --name lornews-db
flyctl postgres attach lornews-db --app lornews-backend
```

---

## Render

### Web Service (Backend)
1. Create **Web Service**
2. Connect GitHub repo
3. Settings:
   - **Root Directory:** (leave blank)
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Health Check Path:** `/api/v1/health`
   - **Start Command:** (leave blank — Dockerfile handles it)

### Web Service (Frontend)
1. Create **Web Service**
2. Settings:
   - **Root Directory:** `web`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Health Check Path:** `/api/v1/health`

### PostgreSQL
- Add Render PostgreSQL from dashboard
- Copy internal connection string to `DATABASE_URL` env var

---

## DigitalOcean App Platform

### Backend
1. Create **App** from GitHub
2. Edit `app.yaml` or use UI:
   - **Source Directory:** `/`
   - **Dockerfile Path:** `Dockerfile`
   - **HTTP Port:** 8000
   - **Health Check:** `/api/v1/health`

### Frontend
1. Add **Frontend** component to app:
   - **Source Directory:** `/web`
   - **Dockerfile Path:** `Dockerfile`
   - **HTTP Port:** 3000

### Database
- Add DigitalOcean Managed PostgreSQL
- Add Managed Redis

---

## Environment Variables (Required)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | 32+ char random string for signing |
| `LLM_PROVIDER` | `openai`, `anthropic`, `google`, `ollama` |
| `LLM_API_KEY` | API key for chosen LLM provider |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

See `.env.example` for all available variables.

## Production Checklist

See [`production_checklist.md`](./production_checklist.md).
