#!/bin/bash

# ============================================
# Fugue Docker Startup Script
# ============================================

set -e

echo ""
echo "========================================"
echo "  Fugue Docker Startup Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check Docker
check_docker() {
    info "Checking Docker..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker Desktop first."
    fi

    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available."
    fi

    success "Docker check passed"
}

# Check and create .env file
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            warn ".env file not found, creating from template..."
            cp .env.example .env
            info "Please edit .env file to configure your settings"
        fi
    fi
}

# Create necessary directories
create_dirs() {
    info "Creating necessary directories..."
    mkdir -p logs uploads
    success "Directories created"
}

# Start services
start_services() {
    info "Starting development environment..."
    docker compose --profile development up -d --build
    success "Services started"
}

# Wait for services
wait_for_services() {
    info "Waiting for services to initialize (30 seconds)..."
    sleep 30
}

# Initialize data
init_data() {
    info "Initializing database..."
    docker compose exec backend alembic upgrade head
    docker compose exec backend python init_data.py
    success "Database initialized"
}

# Show status
show_status() {
    echo ""
    echo "========================================"
    echo "  Service Status"
    echo "========================================"
    docker compose ps

    echo ""
    echo "========================================"
    echo "  Access URLs"
    echo "========================================"
    echo -e "  Frontend:    ${GREEN}http://localhost:3000${NC}"
    echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  MinIO:       ${GREEN}http://localhost:9001${NC}"

    echo ""
    echo "========================================"
    echo "  Demo Account"
    echo "========================================"
    echo -e "  Email:    ${YELLOW}demo@fugue.com${NC}"
    echo -e "  Password: ${YELLOW}Demo123456${NC}"
    echo ""
}

# Stop services
stop_services() {
    info "Stopping services..."
    docker compose down
    success "Services stopped"
}

# Show logs
show_logs() {
    local service=${1:-backend}
    info "Showing $service logs (Ctrl+C to exit)..."
    docker compose logs -f "$service"
}

# Show help
show_help() {
    echo "Usage: ./docker-start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start           Start all services (default)"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show service status"
    echo "  logs [service]  Show service logs (default: backend)"
    echo "  init            Initialize database only"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker-start.sh start"
    echo "  ./docker-start.sh stop"
    echo "  ./docker-start.sh logs backend"
    echo "  ./docker-start.sh status"
    echo ""
}

# Main function
main() {
    local command=${1:-start}

    case $command in
        start)
            check_docker
            check_env
            create_dirs
            start_services
            wait_for_services
            init_data
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 3
            start_services
            wait_for_services
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        init)
            init_data
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $command. Use './docker-start.sh help' for usage."
            ;;
    esac
}

main "$@"
