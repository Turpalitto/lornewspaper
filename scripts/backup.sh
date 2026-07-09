#!/usr/bin/env bash
# =============================================================================
# LORNEWS Automated Backup
# Runs daily via cron in the backup container (04:00 UTC)
# Backups: PostgreSQL, Qdrant vectors, application data
# Retention: 30 days by default
# S3 upload: optional (set S3_BUCKET env var)
# =============================================================================
set -euo pipefail

BACKUP_DIR="/backup/$(date +%Y-%m-%d)"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

log() { echo "[$(date +%H:%M:%S)] $*"; }

# --- 1. PostgreSQL dump ---
log "📦 Backing up PostgreSQL..."
pg_dump --no-owner --no-acl -Fc "$PGDATABASE" > "$BACKUP_DIR/postgres_$TIMESTAMP.dump"
gzip "$BACKUP_DIR/postgres_$TIMESTAMP.dump"
log "   Done: $(ls -lh "$BACKUP_DIR"/postgres_*.dump.gz | awk '{print $5}')"

# --- 2. Qdrant vectors (via snapshot API) ---
log "📦 Backing up Qdrant..."
curl -sf -X POST "http://qdrant:6333/snapshots" > /dev/null 2>&1 && {
  SNAPSHOT=$(curl -sf "http://qdrant:6333/snapshots" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['name'])" 2>/dev/null || echo "")
  if [ -n "$SNAPSHOT" ]; then
    cp "/data/qdrant/snapshots/$SNAPSHOT" "$BACKUP_DIR/qdrant_$TIMESTAMP.snapshot" 2>/dev/null || true
  fi
} || log "   Qdrant snapshot API not available, skipping"

# --- 3. Application data ---
log "📦 Backing up application data..."
tar czf "$BACKUP_DIR/app_data_$TIMESTAMP.tar.gz" -C /data/app . 2>/dev/null || log "   No app data to backup"
log "   Done"

# --- 4. Cleanup old backups ---
log "🧹 Cleaning backups older than $RETENTION_DAYS days..."
find /backup -maxdepth 1 -type d -ctime "+$RETENTION_DAYS" -exec rm -rf {} \; -print 2>/dev/null || true

# --- 5. Upload to S3 (if configured) ---
if [ -n "${S3_BUCKET:-}" ]; then
  log "☁️  Uploading to S3://$S3_BUCKET/$S3_PREFIX..."
  aws s3 sync /backup "s3://$S3_BUCKET/$S3_PREFIX/" --quiet --delete
  log "   Upload complete"
fi

log "✅ Backup complete: $BACKUP_DIR"

# --- Restore instructions (log) ---
cat << 'EOF'

To restore:
  PostgreSQL: pg_restore -U lornews -d lornews latest.dump
  Qdrant:     Copy snapshot to qdrant/snapshots and restore via API
  App data:   tar xzf app_data.tar.gz -C /app/data
EOF
