#!/bin/bash
# n8n deployment script
set -e

echo "🚀 Rozpoczynam wdrażanie n8n na wizardengine.fixtra.io"

# Sprawdzenie, czy .env istnieje
if [ ! -f ".env" ]; then
    echo "❌ Błąd: Plik .env nie znaleziony. Skopiuj .env.example do .env i skonfiguruj go najpierw."
    exit 1
fi

echo "🔧 Instaluję wymagane pakiety..."
apt update && apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw fail2ban

echo "⚙️ Konfiguracja Docker..."
systemctl enable docker
systemctl start docker

echo "🔒 Konfiguracja firewalla..."
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw --force enable

echo "🛡️ Konfiguracja fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Pobierz domenę z pliku .env
N8N_HOST=$(grep "N8N_HOST" .env | cut -d '=' -f2)
if [ -z "$N8N_HOST" ]; then
    echo "❌ Błąd: N8N_HOST nie znaleziony w pliku .env. Skonfiguruj go najpierw."
    exit 1
fi

echo "📁 Tworzę katalogi dla danych..."
mkdir -p n8n_data redis_data

echo "🔄 Konfiguracja NGINX..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
ln -sf "$(pwd)/nginx/n8n.conf" /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "🐳 Uruchamiam kontenery Docker..."
docker-compose down || true
docker-compose up -d

echo "✅ Wdrażanie zakończone!"
echo ""
echo "🔷 Następny krok - konfiguracja SSL:"
echo "  certbot --nginx -d $N8N_HOST"
echo ""
echo "🌐 Po zakończeniu, n8n będzie dostępne pod adresem:"
echo "  https://$N8N_HOST"