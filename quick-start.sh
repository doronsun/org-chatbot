#!/bin/bash

# =============================================================================
# Org Chatbot Quick Start Script
# =============================================================================
# This script provides a quick way to get started with Org Chatbot
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
COMPOSE_DIR="$SCRIPT_DIR/compose"

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
║                    🚀 QUICK START SCRIPT 🚀                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$COMPOSE_DIR/.env" ]]; then
        if [[ -f "$COMPOSE_DIR/env.example" ]]; then
            cp "$COMPOSE_DIR/env.example" "$COMPOSE_DIR/.env"
            warn "Created .env file from env.example. Please review and update the configuration."
        else
            # Create basic .env file
            cat > "$COMPOSE_DIR/.env" << 'EOF'
# Basic configuration for quick start
REDIS_PASSWORD=password123
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=password123
S3_BUCKET=chat-archive
OLLAMA_MODEL=llama3.2:3b
OLLAMA_FAST_MODEL=phi3:3.8b
SESSION_TTL_SECONDS=259200
JWT_SECRET=your-secret-key-for-development
RATE_LIMIT_PER_MINUTE=60
EOF
            warn "Created basic .env file. Please review and update the configuration."
        fi
    fi
    
    success "Environment setup completed"
}

# Start services
start_services() {
    log "Starting Org Chatbot services..."
    
    cd "$COMPOSE_DIR"
    
    # Start services with Docker Compose
    docker-compose up -d
    
    success "Services started successfully"
}

# Wait for services
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for API service
    log "Waiting for API service..."
    timeout=60
    while [[ $timeout -gt 0 ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            success "API service is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [[ $timeout -le 0 ]]; then
        error "API service failed to start within 60 seconds"
    fi
    
    # Wait for Frontend service
    log "Waiting for Frontend service..."
    timeout=60
    while [[ $timeout -gt 0 ]]; then
        if curl -f http://localhost:3000 &> /dev/null; then
            success "Frontend service is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [[ $timeout -le 0 ]]; then
        error "Frontend service failed to start within 60 seconds"
    fi
}

# Test services
test_services() {
    log "Testing services..."
    
    # Test API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        success "API health check passed"
    else
        error "API health check failed"
    fi
    
    # Test chat functionality
    log "Testing chat functionality..."
    response=$(curl -s -X POST http://localhost:8000/chat \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Hello, this is a test message"}' \
        | jq -r '.response' 2>/dev/null || echo "error")
    
    if [[ "$response" != "error" && -n "$response" ]]; then
        success "Chat functionality is working"
    else
        warn "Chat functionality test failed, but services are running"
    fi
}

# Show status
show_status() {
    log "Showing service status..."
    
    cd "$COMPOSE_DIR"
    docker-compose ps
    
    echo ""
    success "🎉 Org Chatbot is now running!"
    echo ""
    info "Access the application at:"
    info "  🌐 Frontend: http://localhost:3000"
    info "  🔌 API: http://localhost:8000"
    info "  📊 API Docs: http://localhost:8000/docs"
    echo ""
    info "Example questions to try:"
    info "  • מה השעה?"
    info "  • איך מנהלים צוות?"
    info "  • מה זה בינה מלאכותית?"
    info "  • איך לפתח מוצר חדש?"
    echo ""
    info "To stop the services, run:"
    info "  docker-compose down"
    echo ""
    info "To view logs, run:"
    info "  docker-compose logs -f"
}

# Main function
main() {
    show_banner
    
    log "Starting Org Chatbot Quick Start"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Start services
    start_services
    
    # Wait for services
    wait_for_services
    
    # Test services
    test_services
    
    # Show status
    show_status
}

# Error handling
trap 'error "Quick start failed at line $LINENO"' ERR

# Run main function
main "$@"
