#!/bin/bash
# n8n deployment script
set -e

echo "🚀 Rozpoczynam wdrażanie n8n na wizardengine.fixtra.io"

# Sprawdzenie, czy .env istnieje
if [ ! -f ".env" ]; then
    echo "❌ Błąd: Plik .env nie znaleziony. Skonfiguruj go najpierw."
    exit 1
fi

# Instalacja pakietów z sudo
echo "🔧 Instaluję wymagane pakiety..."
sudo apt update && sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw fail2ban

# Konfiguracja Docker
echo "⚙️ Konfiguracja Docker..."
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
echo "⚠️ Dodano użytkownika do grupy docker. Może być wymagane ponowne zalogowanie."

# Konfiguracja firewalla
echo "🔒 Konfiguracja firewalla..."
sudo ufw allow OpenSSH
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

# Konfiguracja fail2ban
echo "🛡️ Konfiguracja fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Pobranie domeny z pliku .env
N8N_HOST=$(grep "N8N_HOST" .env | cut -d '=' -f2)
if [ -z "$N8N_HOST" ]; then
    echo "❌ Błąd: N8N_HOST nie znaleziony w pliku .env. Skonfiguruj go najpierw."
    exit 1
fi

# Tworzenie katalogu dla pliku nginx
echo "📁 Tworzę katalog dla konfiguracji nginx..."
mkdir -p nginx

# Kopiowanie pliku konfiguracyjnego nginx
echo "📄 Kopiuję plik konfiguracyjny nginx..."
cp n8n.conf nginx/n8n.conf

# Konfiguracja NGINX
echo "🔄 Konfiguracja NGINX..."
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo ln -sf "$(pwd)/nginx/n8n.conf" /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Tworzenie katalogów
echo "📁 Tworzę katalogi dla danych..."
mkdir -p n8n_data redis_data backups

# Uruchamianie kontenerów
echo "🐳 Uruchamiam kontenery Docker..."
if ! docker-compose down 2>/dev/null; then
    echo "Nie znaleziono istniejących kontenerów, kontynuuję..."
fi
docker-compose up -d

echo "✅ Wdrażanie zakończone!"
echo ""
echo "🔷 Następny krok - konfiguracja SSL:"
echo "  sudo certbot --nginx -d $N8N_HOST"
echo ""
echo "🌐 Po zakończeniu, n8n będzie dostępne pod adresem:"
echo "  https://$N8N_HOST"