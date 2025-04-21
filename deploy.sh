#!/bin/bash
set -e

echo "🔧 Instaluję wymagane pakiety..."
apt update && apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw fail2ban

echo "🔐 Konfiguruję firewall..."
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw --force enable

echo "🗂️ Tworzę link do nginx config..."
ln -s /opt/n8n-stack/nginx/n8n.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "🚀 Odpalam stack..."
docker-compose up -d

echo "✅ Zrób certyfikat SSL:"
echo "  certbot --nginx -d n8n.twojadomena.pl"