#!/usr/bin/env bash
# =============================================================================
# LORNEWS — First-time production server initialization
# Run once on a fresh Ubuntu 22.04/24.04 server
# Usage: curl -sL https://raw.githubusercontent.com/.../init_production.sh | bash
# =============================================================================
set -euo pipefail

echo "🔧 LORNEWS Server Initialization"
echo ""

# --- System updates ---
apt-get update && apt-get upgrade -y
apt-get install -y \
  curl wget git ufw fail2ban \
  ca-certificates gnupg lsb-release

# --- Docker ---
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker

# --- Firewall ---
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# --- Fail2ban ---
systemctl enable fail2ban
systemctl start fail2ban

# --- Swap (for memory-constrained servers) ---
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "✅ 2GB swap created"
fi

# --- Sysctl tuning ---
cat >> /etc/sysctl.conf <<EOF
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
vm.swappiness = 10
EOF
sysctl -p

# --- Clone & deploy ---
cd /opt
git clone https://github.com/anomalyco/lornewspaper.git lornews
cd lornews

echo ""
echo "✅ Server initialized. Next steps:"
echo "   1. Configure /opt/lornews/.env"
echo "   2. Run: cd /opt/lornews && bash scripts/deploy.sh"
echo ""
echo "   Required env vars:"
echo "     SECRET_KEY=<random 64-char string>"
echo "     POSTGRES_PASSWORD=<secure password>"
echo "     DOMAIN=dailyent.ai"
echo "     ADMIN_EMAIL=you@email.com"
echo "     TELEGRAM_BOT_TOKEN=<from @BotFather>"
echo "     TELEGRAM_CHAT_ID=<channel id>"
