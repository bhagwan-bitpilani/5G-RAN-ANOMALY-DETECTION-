#!/bin/bash

echo "🚀 Starting complete application rebuild..."
echo "============================================"

# Stop and remove all Docker containers
echo "1. Stopping and removing all Docker containers..."
docker-compose down --remove-orphans

# Remove all Docker containers (including those not in compose)
echo "2. Removing all Docker containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all Docker images
echo "3. Removing Docker images..."
docker rmi -f $(docker images -q) 2>/dev/null || echo "No images to remove"

# Remove all Docker volumes
echo "4. Removing Docker volumes..."
docker volume rm -f $(docker volume ls -q) 2>/dev/null || echo "No volumes to remove"

# Remove all Docker networks
echo "5. Removing Docker networks..."
docker network rm $(docker network ls -q) 2>/dev/null || echo "No networks to remove"

# Clean up frontend build artifacts
echo "6. Cleaning frontend build artifacts..."
rm -rf frontend/node_modules 2>/dev/null || echo "No frontend node_modules"
rm -rf frontend/dist 2>/dev/null || echo "No frontend dist"
rm -rf frontend/build 2>/dev/null || echo "No frontend build"
rm -f frontend/package-lock.json 2>/dev/null || echo "No package-lock.json"

# Clean up backend artifacts
echo "7. Cleaning backend artifacts..."
rm -rf backend/__pycache__ 2>/dev/null || echo "No backend cache"
rm -rf backend/app/__pycache__ 2>/dev/null || echo "No app cache"
rm -f backend/*.pyc 2>/dev/null || echo "No pyc files"
rm -f backend/app/*.pyc 2>/dev/null || echo "No app pyc files"

# Clean up any corrupted lock files
echo "8. Cleaning lock files..."
find . -name "package-lock.json" -delete 2>/dev/null || echo "No package-lock files"
find . -name "yarn.lock" -delete 2>/dev/null || echo "No yarn lock files"
find . -name "pnpm-lock.yaml" -delete 2>/dev/null || echo "No pnpm lock files"

# Clean up temporary files
echo "9. Cleaning temporary files..."
find . -name ".DS_Store" -delete 2>/dev/null || echo "No DS_Store files"
find . -name "*.log" -delete 2>/dev/null || echo "No log files"
find . -name "*.tmp" -delete 2>/dev/null || echo "No tmp files"

# Clean up any Docker dangling images
echo "10. Cleaning dangling images..."
docker system prune -f

echo "============================================"
echo "✅ Cleanup completed successfully!"
echo "============================================"
