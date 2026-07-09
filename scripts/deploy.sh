#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# LORNEWS Production Deployment — One-command setup
# Usage: bash <(curl -sL https://raw.githubusercontent.com/anomalyco/lornewspaper/main/scripts/deploy.sh)
# =============================================================================

REPO="https://github.com/anomalyco/lornewspaper.git"
BRANCH="main"
DOMAIN="${1:-dailyent.ai}"
ADMIN_EMAIL="${2:-admin@dailyent.ai}"

echo "🚀 LORNEWS Production Deployment"
echo "   Domain: $DOMAIN"
echo "   Email:  $ADMIN_EMAIL"
echo ""

# --- Prerequisites ---
command -v docker >/dev/null 2>&1 || { echo "Installing Docker..."; curl -fsSL https://get.docker.com | bash; }
command -v docker compose >/dev/null 2>&1 || { echo "Installing Docker Compose..."; apt-get install -y docker-compose-plugin; }

# --- Clone ---
if [ ! -d /opt/lornews ]; then
  git clone --branch "$BRANCH" "$REPO" /opt/lornews
fi
cd /opt/lornews
git pull origin "$BRANCH"

# --- Environment ---
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s/SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 64)/" .env
  sed -i "s/TRUSTED_HOSTS=.*/TRUSTED_HOSTS=$DOMAIN/" .env
  sed -i "s/API_CORS_ORIGINS=.*/API_CORS_ORIGINS=https:\/\/$DOMAIN/" .env
  sed -i "s/ADMIN_EMAIL=.*/ADMIN_EMAIL=$ADMIN_EMAIL/" .env
  echo "✅ .env created with secure random SECRET_KEY"
fi

# --- SSL (Let's Encrypt) ---
if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
  echo "📜 Obtaining SSL certificate..."
  apt-get install -y certbot
  certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL"
fi

# --- Build & Start ---
echo "🏗️  Building images..."
docker compose -f docker-compose.prod.yml build

echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

# --- Health Check ---
echo "⏳ Waiting for health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend healthy"
    break
  fi
  sleep 2
done

for i in $(seq 1 30); do
  if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend healthy"
    break
  fi
  sleep 2
done

# --- Caddy reverse proxy ---
if [ ! -f /etc/caddy/Caddyfile ]; then
  echo "📝 Configuring reverse proxy..."
  mkdir -p /etc/caddy
  cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    reverse_proxy frontend:3000
}

api.$DOMAIN {
    reverse_proxy backend:8000
}
EOF
  docker run -d \
    --name caddy \
    --restart unless-stopped \
    -p 80:80 -p 443:443 \
    -v /etc/caddy/Caddyfile:/etc/caddy/Caddyfile \
    -v caddy_data:/data \
    -v /etc/letsencrypt:/etc/letsencrypt:ro \
    caddy:2
fi

# --- Daily cron ---
(crontab -l 2>/dev/null | grep -q "lornews") || {
  echo "⏰ Setting up daily pipeline cron..."
  (crontab -l 2>/dev/null; echo "0 6 * * * curl -sf -X POST http://localhost:8000/api/v1/pipeline/daily > /dev/null 2>&1") | crontab -
  echo "✅ Cron: daily pipeline at 06:00 UTC"
}

echo ""
echo "✅ Deployment complete!"
echo "   https://$DOMAIN"
echo "   https://api.$DOMAIN/api/v1/docs"
echo ""
echo "📊 Monitoring:"
echo "   https://$DOMAIN/api/v1/health"
echo "   https://$DOMAIN/metrics"
echo ""
echo "📧 Admin: $ADMIN_EMAIL"
