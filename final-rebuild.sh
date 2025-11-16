#!/bin/bash

echo "🐳 Final Docker Rebuild..."
echo "============================================"

# Build and start services one by one
echo "1. Building and starting PostgreSQL..."
docker-compose up -d postgresql

echo "2. Waiting for PostgreSQL to be ready..."
sleep 10

echo "3. Building and starting Redis..."
docker-compose up -d redis

echo "4. Building and starting app..."
docker-compose up -d app

echo "5. Waiting for Backend to be ready..."
sleep 15

echo "6. Building and starting Frontend..."
docker-compose up -d frontend

echo "7. Starting monitoring services..."
docker-compose up -d prometheus grafana node-exporter cadvisor alertmanager

echo "8. Checking services status..."
docker-compose ps

echo ""
echo "✅ All services rebuilt successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:       http://localhost:3000"
echo "   Backend API:    http://localhost:8000"
echo "   Backend Docs:   http://localhost:8000/docs"
echo "   Grafana:        http://localhost:3002"
echo "   Prometheus:     http://localhost:19090"
echo "   Alertmanager:   http://localhost:19093"
echo "   Node Exporter:  http://localhost:19100"
echo "   cAdvisor:       http://localhost:18080"

echo ""
echo "📊 Pre-configured Dashboards:"
echo "   - 5G NR KPI Overview"
echo "   - 5G NR Anomaly Detection" 
echo "   - 5G NR Cell-Level Analysis"
echo ""
echo "🔔 Alerting:"
echo "   - KPI degradation alerts"
echo "   - Anomaly detection alerts"
echo "   - Resource utilization alerts"
echo ""
echo "📈 Metrics Collected:"
echo "   - All 10 enhanced KPIs with thresholds"
echo "   - Anomaly scores and detection rates"
echo "   - System resource utilization"
echo "   - Container performance metrics"
