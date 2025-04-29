#!/bin/bash
# Script to rebuild and restart the scraper container

echo "🔄 Rebuilding and restarting the scraper container..."

# Navigate to the project directory
cd "$(dirname "$0")"

# Stop and remove the existing container
echo "🛑 Stopping existing container..."
docker stop n8n-scraper || true
docker rm n8n-scraper || true

# Build the new image
echo "🏗️ Building new image..."
docker build -t n8n-scraper:latest ./scraper

# Start the new container
echo "🚀 Starting new container..."
docker run -d --name n8n-scraper \
  --restart always \
  --network fixtra-n8n-stack_n8n-network \
  -p 127.0.0.1:5000:5000 \
  n8n-scraper:latest

# Check if the container is running
echo "✅ Checking container status..."
docker ps | grep n8n-scraper

echo "📋 Container logs:"
sleep 2
docker logs n8n-scraper

echo "✨ Done! The scraper has been rebuilt and restarted."
