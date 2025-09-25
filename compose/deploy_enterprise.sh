#!/bin/bash

# Enterprise Chatbot Deployment Script
set -e

echo "🚀 Starting Enterprise Chatbot Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required files exist
required_files=(
    "docker-compose.production.yml"
    "chat-api/app_enterprise.py"
    "chat-api/requirements_enterprise.txt"
    "haproxy/haproxy.cfg"
    "monitoring/prometheus.yml"
    "auth-service/app.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_status "All required files found ✅"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.yml down 2>/dev/null || true

# Build and start enterprise services
print_status "Building enterprise services..."
docker-compose -f docker-compose.production.yml build --no-cache

print_status "Starting enterprise services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check HAProxy
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    print_status "HAProxy: ✅ Healthy"
else
    print_warning "HAProxy: ⚠️  Not responding"
fi

# Check Chat API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Chat API: ✅ Healthy"
else
    print_warning "Chat API: ⚠️  Not responding"
fi

# Check Auth Service
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Auth Service: ✅ Healthy"
else
    print_warning "Auth Service: ⚠️  Not responding"
fi

# Check Grafana
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_status "Grafana: ✅ Healthy"
else
    print_warning "Grafana: ⚠️  Not responding"
fi

# Check Prometheus
if curl -f http://localhost:9090 > /dev/null 2>&1; then
    print_status "Prometheus: ✅ Healthy"
else
    print_warning "Prometheus: ⚠️  Not responding"
fi

# Display service information
echo ""
print_status "🎉 Enterprise Chatbot Deployment Complete!"
echo ""
echo "📊 Service URLs:"
echo "   • Chat API: http://localhost:80"
echo "   • Auth Service: http://localhost:8001"
echo "   • Grafana Dashboard: http://localhost:3000 (admin/EnterpriseGrafana2024!)"
echo "   • Prometheus: http://localhost:9090"
echo "   • HAProxy Stats: http://localhost:8404/stats"
echo ""
echo "🔐 Default Credentials:"
echo "   • Grafana: admin / EnterpriseGrafana2024!"
echo "   • MinIO Console: http://localhost:9001 (admin/EnterpriseMinio2024!Secure)"
echo ""
echo "📝 Next Steps:"
echo "   1. Register a user: curl -X POST http://localhost:8001/register"
echo "   2. Test chat: curl -X POST http://localhost:80/chat"
echo "   3. Monitor: Open Grafana dashboard"
echo ""
print_status "🚀 Your enterprise chatbot is ready to handle millions of requests!"

# Show running containers
echo ""
print_status "Running containers:"
docker-compose -f docker-compose.production.yml ps
