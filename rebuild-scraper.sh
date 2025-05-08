#!/bin/bash
# Script to rebuild and restart the scraper containers

echo "🔄 Rebuilding and restarting the scraper containers..."

# Navigate to the project directory
cd "$(dirname "$0")"

# Stop and remove the existing containers
echo "🛑 Stopping existing containers..."
docker stop n8n-scraper n8n-scraper-postgres || true
docker rm n8n-scraper n8n-scraper-postgres || true

# Start the new containers using docker-compose
echo "🚀 Starting new containers..."
docker-compose -f scraper-compose.yml up -d

# Check if the containers are running
echo "✅ Checking container status..."
docker ps | grep n8n-scraper

echo "📋 Container logs:"
sleep 5
docker logs n8n-scraper

echo "✨ Done! The scraper has been rebuilt and restarted."