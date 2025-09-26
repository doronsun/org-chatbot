#!/bin/bash

# Enterprise Chatbot Startup Script
# מערכת מתקדמת ברמה enterprise

set -e

echo "🚀 Starting Enterprise Chatbot System..."
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/redis
mkdir -p data/postgres
mkdir -p data/weaviate
mkdir -p data/neo4j
mkdir -p data/minio
mkdir -p data/ollama
mkdir -p data/prometheus
mkdir -p data/grafana
mkdir -p data/elasticsearch
mkdir -p logs
mkdir -p ssl

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 data/
chmod 755 logs/
chmod 755 ssl/

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Copying environment file..."
    cp env.enterprise .env
    echo "✅ Environment file created. Please review .env file and update as needed."
fi

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.enterprise.yml pull

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.enterprise.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.enterprise.yml ps

# Display service URLs
echo ""
echo "🎉 Enterprise Chatbot System is running!"
echo "========================================"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "❤️ Health Check: http://localhost:8000/health"
echo "📊 Metrics: http://localhost:8000/metrics"
echo ""
echo "🔍 Monitoring:"
echo "📈 Prometheus: http://localhost:9090"
echo "📊 Grafana: http://localhost:3001 (admin/enterprise_grafana_2024)"
echo "🔍 Jaeger: http://localhost:16686"
echo "📋 Kibana: http://localhost:5601"
echo ""
echo "🗄️ Databases:"
echo "🔴 Redis: localhost:6379"
echo "🐘 PostgreSQL: localhost:5432"
echo "🔍 Weaviate: http://localhost:8080"
echo "🕸️ Neo4j: http://localhost:7474 (neo4j/enterprise_neo4j_2024)"
echo "📦 MinIO: http://localhost:9000 (admin/enterprise_minio_2024)"
echo "🤖 Ollama: http://localhost:11434"
echo ""
echo "🛠️ Management Commands:"
echo "📊 View logs: docker-compose -f docker-compose.enterprise.yml logs -f"
echo "🔄 Restart: docker-compose -f docker-compose.enterprise.yml restart"
echo "🛑 Stop: docker-compose -f docker-compose.enterprise.yml down"
echo "🧹 Clean: docker-compose -f docker-compose.enterprise.yml down -v"
echo ""
echo "✅ System is ready for use!"
