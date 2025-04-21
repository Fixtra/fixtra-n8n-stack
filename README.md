# Fixtra n8n Stack

Self-hosted n8n deployment on Hetzner with Docker, HTTPS, Redis and NGINX.

## Szybki start

1. Utwórz VPS (np. Hetzner CX22)
2. Sklonuj repo:
   ```bash
   git clone https://github.com/Fixtra/fixtra-n8n-stack.git
   cd fixtra-n8n-stack
   ```
3. Skonfiguruj `.env` na podstawie `.env.example`
4. Wykonaj skrypt:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
5. Uzyskaj certyfikat:
   ```bash
   certbot --nginx -d n8n.twojadomena.pl
   ```

Gotowe!