#!/bin/bash

echo "🔧 Fixing Port Conflicts..."

# List of ports we need
ports=(8000 3000 3002 9090 5432 6379)

echo "Checking port availability..."
for port in "${ports[@]}"; do
    if sudo lsof -i :$port > /dev/null 2>&1; then
        echo "❌ Port $port is in use:"
        sudo lsof -i :$port
        echo "Attempting to free port $port..."
        sudo fuser -k $port/tcp
        sleep 2
    else
        echo "✅ Port $port is available"
    fi
done

echo ""
echo "🧹 Cleaning up Docker containers and networks..."
docker-compose down
docker system prune -f
docker network prune -f

echo ""
echo "🚀 Starting application with fixed ports..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "🌐 Service URLs:"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Grafana:     http://localhost:3002 (admin/admin)"
echo "   Prometheus:  http://localhost:9090"

echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "✅ Port conflicts resolved!"
EOF
