# Fixtra n8n Stack

Self-hosted n8n deployment on Hetzner with Docker, HTTPS, Redis and NGINX.

## Komponenty stosu

- **n8n** - platforma automatyzacji workflow
- **Redis** - szybka baza danych w pamięci, obsługująca kolejkę zadań
- **NGINX** - serwer proxy obsługujący SSL i przekierowania
- **Docker** - konteneryzacja aplikacji
- **Certbot** - automatyczne certyfikaty SSL (Let's Encrypt)
- **Fail2ban** - ochrona przed atakami brute-force
- **UFW** - prosty firewall

## Szybki start

1. Utwórz VPS (np. Hetzner CX22)

2. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/Fixtra/fixtra-n8n-stack.git
   cd fixtra-n8n-stack
   ```

3. Skonfiguruj plik `.env` na podstawie `.env.example`:
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   **Ważne:** Zmień domyślne hasła i ustaw domenę (wizardengine.fixtra.io)

4. Wykonaj skrypt wdrożeniowy:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

5. Uzyskaj certyfikat SSL:
   ```bash
   certbot --nginx -d wizardengine.fixtra.io
   ```

## Utrzymanie systemu

### Kopie zapasowe

Dane n8n przechowywane są w katalogach `./n8n_data` i `./redis_data`. Zalecamy regularne kopie:

```bash
# Utworzenie kopii zapasowej
tar -czvf n8n-backup-$(date +%Y%m%d).tar.gz ./n8n_data ./redis_data
```

### Automatyczne kopie zapasowe

Utworzenie automatycznych kopii zapasowych przy użyciu crontab:

```bash
# Edycja crontab
crontab -e

# Dodaj linię by tworzyć kopię co tydzień o 2:00 AM w niedzielę
0 2 * * 0 cd /opt/fixtra-n8n-stack && tar -czvf backups/n8n-backup-$(date +\%Y\%m\%d).tar.gz ./n8n_data ./redis_data
```

### Aktualizacje

Aby zaktualizować n8n do najnowszej wersji:

```bash
docker-compose pull
docker-compose up -d
```

## Monitorowanie

### Logi

Aby sprawdzić logi n8n:

```bash
docker-compose logs -f n8n
```

### Monitoring zasobów

Sprawdzenie zużycia zasobów:

```bash
docker stats
```

## Rozwiązywanie problemów

- **Logi kontenerów**: `docker-compose logs -f [n8n|redis]`
- **Status usług**: `docker-compose ps`
- **Restart usług**: `docker-compose restart`
- **Sprawdzenie NGINX**: `nginx -t && systemctl status nginx`

## Bezpieczeństwo

- Regularnie aktualizuj hasła w pliku `.env`
- Dbaj o aktualizacje systemu operacyjnego (`apt update && apt upgrade`)
- Monitoruj logi pod kątem nieautoryzowanych prób dostępu
- Włącz automatyczne aktualizacje certyfikatu: `certbot renew --dry-run`
