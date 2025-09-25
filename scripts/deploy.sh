#!/bin/bash

# =============================================================================
# Org Chatbot Production Deployment Script
# =============================================================================
# This script deploys the Org Chatbot application to production
# Usage: ./deploy.sh [environment] [options]
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$PROJECT_ROOT/compose"
ENVIRONMENT="${1:-production}"
BACKUP_DIR="/opt/org-chatbot/backups"
LOG_DIR="/opt/org-chatbot/logs"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ▒█████   ██▀███   ▄▄▄       ▄████▄   ██▓    ▓██   ██▓ ██▓ ▄▄▄▄    ▄▄▄▄     ║
║   ▒██▒  ██▒▓██ ▒ ██▒▒████▄    ▒██▀ ▀█   ▓██▒     ▒██  ██▒▓██▒▓█████▄ ▒████▄   ║
║   ▒██░  ██▒▓██ ░▄█ ▒▒██  ▀█▄  ▒▓█    ▄  ▒██░      ▒██ ██░▒██░▒██▒ ▄██▒██  ▀█▄ ║
║   ▒██   ██░▒██▀▀█▄  ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▒██░      ░ ▐██▓░░██░▒██░█▀  ░██▄▄▄▄██ ║
║   ░ ████▓▒░░██▓ ▒██▒ ▓█   ▓██▒▒ ▓███▀ ░░██████▒  ░ ██▒▓░░██░░▓█  ▀█▓ ▓█   ▓██▒║
║   ░ ▒░▒░▒░ ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░ ░▒ ▒  ░░ ▒░▓  ░   ██▒▒▒ ░▓ ░░▒▓███▀▒ ▒▒   ▓▒█░║
║     ░ ▒ ▒░   ░▒ ░ ▒░  ▒   ▒▒ ░  ░  ▒   ░ ░ ▒  ░ ▓██ ░▒░  ▒ ░▒░▒   ░  ▒   ▒▒ ░║
║   ░ ░ ░ ▒    ░░   ░   ░   ▒   ░          ░ ░    ▒ ▒ ░░   ▒ ░ ░    ░  ░   ▒   ║
║       ░ ░     ░           ░  ░░ ░          ░  ░ ░ ░      ░   ░         ░  ░║
║                      ░  ░░            ░     ░ ░      ░     ░              ║
║                                                                              ║
║                    🚀 PRODUCTION DEPLOYMENT SCRIPT 🚀                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Check if environment file exists
    if [[ ! -f "$COMPOSE_DIR/.env" ]]; then
        error "Environment file not found at $COMPOSE_DIR/.env"
    fi
    
    # Check disk space
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $DISK_USAGE -gt 90 ]]; then
        error "Disk usage is above 90% ($DISK_USAGE%)"
    fi
    
    # Check memory
    MEMORY_AVAILABLE=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [[ $MEMORY_AVAILABLE -lt 2048 ]]; then
        warn "Available memory is low ($MEMORY_AVAILABLE MB)"
    fi
    
    success "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "/opt/org-chatbot/data"
    sudo mkdir -p "/opt/org-chatbot/ssl"
    
    # Set proper permissions
    sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR"
    sudo chown -R $(whoami):$(whoami) "$LOG_DIR"
    sudo chown -R $(whoami):$(whoami) "/opt/org-chatbot/data"
    
    success "Directories created successfully"
}

# Backup existing data
backup_data() {
    log "Creating backup of existing data..."
    
    BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup PostgreSQL data
    if docker ps --format "table {{.Names}}" | grep -q "postgres-primary"; then
        log "Backing up PostgreSQL data..."
        docker exec org-chatbot-postgres-primary pg_dump -U postgres org_chatbot > "$BACKUP_PATH/postgres_backup.sql"
    fi
    
    # Backup Redis data
    if docker ps --format "table {{.Names}}" | grep -q "redis-master"; then
        log "Backing up Redis data..."
        docker exec org-chatbot-redis-master redis-cli --rdb /data/dump.rdb
        docker cp org-chatbot-redis-master:/data/dump.rdb "$BACKUP_PATH/redis_dump.rdb"
    fi
    
    # Backup configuration files
    cp -r "$COMPOSE_DIR" "$BACKUP_PATH/compose"
    cp -r "$PROJECT_ROOT/k8s" "$BACKUP_PATH/k8s" 2>/dev/null || true
    
    # Compress backup
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "backup_$BACKUP_TIMESTAMP"
    rm -rf "$BACKUP_PATH"
    
    success "Backup created at $BACKUP_PATH.tar.gz"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build API image
    log "Building API image..."
    docker build -t org-chatbot/chat-api:latest ./api
    
    # Build Frontend image
    log "Building Frontend image..."
    docker build -t org-chatbot/frontend:latest ./frontend
    
    success "Docker images built successfully"
}

# Deploy with Docker Compose
deploy_compose() {
    log "Deploying with Docker Compose..."
    
    cd "$COMPOSE_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.production.yml pull
    
    # Start services
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_service_health
    
    success "Docker Compose deployment completed"
}

# Deploy with Kubernetes
deploy_kubernetes() {
    log "Deploying with Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        error "Kubernetes cluster is not accessible"
    fi
    
    cd "$PROJECT_ROOT"
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/ollama.yaml
    kubectl apply -f k8s/chat-api.yaml
    kubectl apply -f k8s/frontend.yaml
    kubectl apply -f k8s/monitoring.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for deployments
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/chat-api -n org-chatbot
    kubectl wait --for=condition=available --timeout=300s deployment/frontend -n org-chatbot
    
    success "Kubernetes deployment completed"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        success "API service is healthy"
    else
        error "API service is not responding"
    fi
    
    # Check Frontend health
    if curl -f http://localhost:3000/health &> /dev/null; then
        success "Frontend service is healthy"
    else
        error "Frontend service is not responding"
    fi
    
    # Check Database connectivity
    if docker exec org-chatbot-postgres-primary pg_isready -U postgres &> /dev/null; then
        success "PostgreSQL is healthy"
    else
        error "PostgreSQL is not responding"
    fi
    
    # Check Redis connectivity
    if docker exec org-chatbot-redis-master redis-cli ping &> /dev/null; then
        success "Redis is healthy"
    else
        error "Redis is not responding"
    fi
    
    # Check Ollama connectivity
    if curl -f http://localhost:11434/api/tags &> /dev/null; then
        success "Ollama service is healthy"
    else
        error "Ollama service is not responding"
    fi
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Test API endpoints
    curl -f http://localhost:8000/health || error "API health check failed"
    curl -f http://localhost:8000/metrics || error "API metrics endpoint failed"
    
    # Test Frontend
    curl -f http://localhost:3000/health || error "Frontend health check failed"
    
    # Test chat functionality
    CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Hello, test message"}' \
        | jq -r '.response' 2>/dev/null || echo "error")
    
    if [[ "$CHAT_RESPONSE" != "error" && -n "$CHAT_RESPONSE" ]]; then
        success "Chat functionality is working"
    else
        error "Chat functionality test failed"
    fi
    
    success "Smoke tests completed successfully"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        success "Prometheus is running"
    else
        warn "Prometheus is not responding"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3001/api/health &> /dev/null; then
        success "Grafana is running"
    else
        warn "Grafana is not responding"
    fi
    
    # Create Grafana dashboard
    if command -v curl &> /dev/null; then
        log "Creating Grafana dashboard..."
        # Dashboard creation would go here
    fi
    
    success "Monitoring setup completed"
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 7 backups
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +7 -delete
    
    success "Backup cleanup completed"
}

# Send deployment notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 Org Chatbot Deployment $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" &> /dev/null || true
    fi
    
    # Email notification
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        echo "Org Chatbot Deployment $status: $message" | \
            mail -s "Org Chatbot Deployment $status" "$NOTIFICATION_EMAIL" || true
    fi
}

# Main deployment function
main() {
    show_banner
    
    log "Starting Org Chatbot deployment to $ENVIRONMENT environment"
    
    # Load environment variables
    if [[ -f "$COMPOSE_DIR/.env" ]]; then
        source "$COMPOSE_DIR/.env"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_directories
    
    # Backup existing data
    backup_data
    
    # Build images
    build_images
    
    # Deploy based on environment
    if [[ "$ENVIRONMENT" == "kubernetes" ]]; then
        deploy_kubernetes
    else
        deploy_compose
    fi
    
    # Check service health
    check_service_health
    
    # Run smoke tests
    run_smoke_tests
    
    # Setup monitoring
    setup_monitoring
    
    # Cleanup old backups
    cleanup_backups
    
    # Send success notification
    send_notification "SUCCESS" "Deployment completed successfully"
    
    success "🎉 Deployment completed successfully!"
    info "Application is available at:"
    info "  Frontend: http://localhost:3000"
    info "  API: http://localhost:8000"
    info "  Grafana: http://localhost:3001"
    info "  Prometheus: http://localhost:9090"
    
    # Show service status
    if [[ "$ENVIRONMENT" == "kubernetes" ]]; then
        kubectl get pods -n org-chatbot
    else
        docker-compose -f "$COMPOSE_DIR/docker-compose.production.yml" ps
    fi
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
