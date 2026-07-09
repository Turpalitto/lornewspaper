# Production Deployment Guide

## One-Command Deployment

### DigitalOcean (recommended)

```bash
# 1. Create a Droplet
#    Ubuntu 24.04, 4GB RAM, 2 CPU, 80GB SSD ($24/mo)

# 2. Initialize server
ssh root@<server-ip>
curl -sL https://raw.githubusercontent.com/anomalyco/lornewspaper/main/scripts/init_production.sh | bash

# 3. Deploy
cd /opt/lornews
cp .env.example .env
# Edit .env with your secrets

bash scripts/deploy.sh dailyent.ai admin@dailyent.ai
```

### What It Sets Up

```
┌─────────────────────────────────────────────────────────┐
│                        Caddy                             │
│            HTTPS · Reverse Proxy · Auto SSL              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Frontend │  │ Backend  │  │  Crontab  │  │  Bot   │  │
│  │ :3000    │  │ :8000    │  │ 06:00 UTC │  │Telegram│  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│       │              │              │              │     │
│       ▼              ▼              ▼              ▼     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │ PostgreSQL│  │  Redis   │  │     Daily Pipeline    │  │
│  │ :5432    │  │ :6379    │  │ Discovery → Digest →  │  │
│  └──────────┘  └──────────┘  │ Editorial → Telegram  │  │
│       │              │       └───────────────────────┘  │
│       ▼              ▼                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │                   Qdrant                          │   │
│  │              Vector Database                       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────┐  ┌──────────┐                              │
│  │Prometheus│  │ Grafana  │  (monitoring profile)        │
│  └──────────┘  └──────────┘                              │
└─────────────────────────────────────────────────────────┘
```

## Required Environment Variables

```bash
# === REQUIRED ===
SECRET_KEY=<openssl rand -hex 64>        # Random 64-byte hex string
POSTGRES_PASSWORD=<secure password>      # Database password
DOMAIN=dailyent.ai                        # Your domain
ADMIN_EMAIL=admin@dailyent.ai            # For SSL cert notifications

# === RECOMMENDED ===
LLM_API_KEY=<openai-key>                 # For RAG and editorial summaries
TELEGRAM_BOT_TOKEN=<bot-token>           # From @BotFather
TELEGRAM_CHAT_ID=<chat-id>               # Channel/group ID for daily digests

# === OPTIONAL ===
S3_BUCKET=my-backups                     # For offsite backups
GRAFANA_PASSWORD=<secure>                # Monitoring dashboard
```

## Daily Pipeline

```bash
# The pipeline runs automatically at 06:00 UTC via cron:
curl -X POST http://localhost:8000/api/v1/pipeline/daily

# Pipeline stages:
#   1. Content Discovery — 6 strategies
#   2. Digest Generation — Daily Digest
#   3. Editorial Generation — Editorial Digest
#   4. Telegram Delivery — Send to subscribers
```

## Telegram Setup

```bash
# 1. Create bot with @BotFather
#    Send: /newbot
#    Name: LORNEWS Daily Digest
#    Username: lornews_bot
#    → Get TELEGRAM_BOT_TOKEN

# 2. Create channel
#    @LORNEWS_Digest
#    Add bot as admin

# 3. Get chat ID
#    Send message to channel
#    curl https://api.telegram.org/bot<TOKEN>/getUpdates
#    → Get TELEGRAM_CHAT_ID

# 4. Test
curl -X POST http://localhost:8000/api/v1/telegram/send-digest
```

## Monitoring

```bash
# Health endpoints:
curl https://dailyent.ai/api/v1/health           # System health
curl https://dailyent.ai/api/v1/liveness          # Liveness probe
curl https://dailyent.ai/api/v1/readiness         # Readiness probe
curl https://dailyent.ai/metrics                  # Prometheus metrics

# Pipeline status:
curl https://api.dailyent.ai/api/v1/pipeline/status
curl https://api.dailyent.ai/api/v1/pipeline/verify

# Telegram status:
curl https://api.dailyent.ai/api/v1/telegram/health

# Monitoring stack (optional):
docker compose -f docker-compose.prod.yml --profile monitoring up -d
# Grafana: https://dailyent.ai:3001 (admin:password)
```

## Backup Strategy

```bash
# Automatic: daily at 04:00 UTC
#   → PostgreSQL dump (compressed)
#   → Qdrant snapshot
#   → Application data archive
#   → S3 upload (if configured)
#   → 30-day retention

# Manual backup:
docker compose -f docker-compose.prod.yml exec backup sh /backup.sh

# Restore:
pg_restore -U lornews -d lornews /backup/2024-01-01/postgres_*.dump
```

## Scaling

```bash
# Increase backend workers:
docker compose -f docker-compose.prod.yml up -d --scale backend=3 backend

# Add monitoring:
docker compose -f docker-compose.prod.yml --profile monitoring up -d

# Migrate to larger droplet:
#   1. Backup: docker compose exec backup sh /backup.sh
#   2. Copy backup to new droplet
#   3. Run deploy.sh on new droplet
#   4. Restore data
```

## Production Checklist

- [ ] `SECRET_KEY` = unique random 64-char string
- [ ] `POSTGRES_PASSWORD` = strong password
- [ ] `TRUSTED_HOSTS` = specific hostnames (not `*`)
- [ ] `API_CORS_ORIGINS` = specific origins (not `*`)
- [ ] `API_DEBUG` = `false`
- [ ] SSL certificate valid (auto-renew via Let's Encrypt)
- [ ] Firewall enabled (ufw)
- [ ] Fail2ban enabled
- [ ] Daily cron configured (`crontab -l` shows pipeline job)
- [ ] Telegram bot configured (`/api/v1/telegram/health`)
- [ ] Backups running (`/backup` has recent files)
- [ ] Monitoring accessible (Prometheus + Grafana)
