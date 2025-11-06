.PHONY: help build up down restart logs clean install-ollama pull-models test test-vision create-test-image test-chromadb health status services dev-local check-prereqs

# Default target
help:
	@echo "Iris - AI-Powered Real-Time Assistant"
	@echo "========================================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Local Development (with GPU):"
	@echo "  make check-prereqs  - Check prerequisites for local development"
	@echo "  make services       - Start ChromaDB + SearXNG in Docker"
	@echo "  make dev-local      - Run backend locally with GPU support"
	@echo ""
	@echo "Docker Development (no GPU):"
	@echo "  make setup          - Complete setup (Ollama, models, Docker build)"
	@echo "  make build          - Build Docker containers"
	@echo "  make up             - Start all services (detached mode)"
	@echo "  make dev            - Start in dev mode (Docker, no GPU)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-searxng   - View SearXNG logs"
	@echo "  make health         - Check health of all services"
	@echo "  make status         - Show status of all services"
	@echo "  make clean          - Stop and remove all containers, networks, and volumes"
	@echo "  make install-ollama - Install Ollama (macOS)"
	@echo "  make pull-models    - Pull required Ollama models"
	@echo "  make test           - Run basic tests"
	@echo "  make create-test-image - Create a test image for vision testing"
	@echo "  make test-vision    - Test vision query with image (requires IMAGE=path)"
	@echo "  make test-chromadb  - Test ChromaDB connection and functionality"
	@echo "  make init-rag       - Initialize RAG knowledge base"
	@echo "  make query-rag      - Query RAG system (interactive)"
	@echo "  make rag-status     - Check RAG system status"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo ""

# Complete setup
setup: install-ollama pull-models build
	@echo "✅ Setup complete!"
	@echo "Now run: make up"

# Install Ollama (macOS with Homebrew)
install-ollama:
	@echo "📦 Installing Ollama..."
	@if command -v ollama >/dev/null 2>&1; then \
		echo "✅ Ollama is already installed"; \
		ollama --version; \
	else \
		echo "Installing Ollama via Homebrew..."; \
		brew install ollama; \
	fi
	@echo "Starting Ollama service..."
	@brew services start ollama || ollama serve &
	@sleep 3
	@echo "✅ Ollama installed and started"

# Pull required Ollama models
pull-models:
	@echo "📥 Pulling Ollama models..."
	@echo "This may take a few minutes..."
	@echo ""
	@echo "Pulling llama3.2:3b (conversational model)..."
	@ollama pull llama3.2:3b
	@echo "✅ llama3.2:3b downloaded"
	@echo ""
	@read -p "Pull llava:7b for vision tasks? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "Pulling llava:7b (vision model)..."; \
		ollama pull llava:7b; \
		echo "✅ llava:7b downloaded"; \
	else \
		echo "⏭️  Skipping llava:7b"; \
	fi
	@echo ""
	@echo "Available models:"
	@ollama list

# Build Docker containers
build:
	@echo "🔨 Building Docker containers..."
	docker-compose build
	@echo "✅ Build complete"

# Start all services
up:
	@echo "🚀 Starting Iris services..."
	@echo "Make sure Ollama is running on host..."
	@if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "⚠️  Ollama is not running. Starting Ollama..."; \
		ollama serve & \
		sleep 3; \
	fi
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Service URLs:"
	@echo "   Backend API:  http://localhost:8888"
	@echo "   API Docs:     http://localhost:8888/docs"
	@echo "   SearXNG:      http://localhost:8080"
	@echo ""
	@echo "Check status with: make status"

# Start services only (ChromaDB + SearXNG) for local backend development
services:
	@echo "🐳 Starting support services (ChromaDB + SearXNG)..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Service URLs:"
	@echo "   ChromaDB:     http://localhost:8001"
	@echo "   SearXNG:      http://localhost:8080"
	@echo ""
	@echo "Next: Run backend locally with 'make dev-local'"

# Check prerequisites for local development
check-prereqs:
	@echo "🔍 Checking prerequisites for local development..."
	@python3 backend/check_prerequisites.py

# Start backend locally with GPU support (for development)
dev-local:
	@echo "🚀 Starting backend locally (with GPU support)..."
	@echo ""
	@echo "Checking prerequisites..."
	@echo ""
	@if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "⚠️  Ollama is not running. Starting Ollama..."; \
		ollama serve & \
		sleep 3; \
	fi
	@if ! curl -s http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then \
		echo "⚠️  ChromaDB is not running. Start services first:"; \
		echo "    make services"; \
		exit 1; \
	fi
	@if ! curl -s http://localhost:8080 >/dev/null 2>&1; then \
		echo "⚠️  SearXNG is not running. Start services first:"; \
		echo "    make services"; \
		exit 1; \
	fi
	@echo "✅ All prerequisites running"
	@echo ""
	@echo "Starting backend with auto-reload..."
	@echo "Backend URL: http://localhost:8888"
	@echo "API Docs:    http://localhost:8888/docs"
	@echo ""
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload

# Start in development mode with live reload (LEGACY - runs backend in Docker)
dev:
	@echo "Backend will auto-reload on code changes..."
	@if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "⚠️  Ollama is not running. Starting Ollama..."; \
		ollama serve & \
		sleep 3; \
	fi
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop all services
down:
	@echo "🛑 Stopping Iris services..."
	docker-compose down
	@echo "✅ Services stopped"

# Restart all services
restart: down up

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-searxng:
	docker-compose logs -f searxng

# Check health of services
health:
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Ollama (host):"
	@if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "  ✅ Running"; \
		echo "  Models: $$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ', ')"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo ""
	@echo "Backend API:"
	@if curl -s http://localhost:8888/health >/dev/null 2>&1; then \
		echo "  ✅ Running"; \
		curl -s http://localhost:8888/health | python3 -m json.tool | grep -A 4 '"services"' || echo ""; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo ""
	@echo "SearXNG:"
	@if curl -s http://localhost:8080 >/dev/null 2>&1; then \
		echo "  ✅ Running"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo ""
	@echo "ChromaDB:"
	@if curl -s http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then \
		echo "  ✅ Running"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo ""

# Show status of containers
status:
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose ps
	@echo ""
	@make health

# Run basic tests
test:
	@echo "🧪 Running basic tests..."
	@echo ""
	@echo "Testing backend health endpoint..."
	@curl -s http://localhost:8888/health | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "Testing chat endpoint..."
	@curl -s -X POST http://localhost:8888/agent/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "Hello!"}' | python3 -m json.tool || echo "❌ Chat endpoint failed"
	@echo ""
	@echo "Testing SearXNG..."
	@curl -s "http://localhost:8080/search?q=test&format=json" | python3 -m json.tool | head -20 || echo "❌ SearXNG not responding"
	@echo ""

# Create a test image for vision testing
create-test-image:
	@echo "🎨 Creating test image..."
	@python3 backend/tests/create_test_image.py --output test_image.jpg
	@echo ""
	@echo "Test image created: test_image.jpg"
	@echo "Run: make test-vision IMAGE=test_image.jpg"

# Test vision query with an image
test-vision:
	@echo "🔍 Testing vision query..."
	@if [ -z "$(IMAGE)" ]; then \
		echo "❌ Error: IMAGE parameter required"; \
		echo "Usage: make test-vision IMAGE=path/to/image.jpg"; \
		echo ""; \
		echo "Example: make test-vision IMAGE=./test_image.jpg"; \
		echo ""; \
		echo "To create a test image first, run: make create-test-image"; \
		exit 1; \
	fi
	@echo "Testing with image: $(IMAGE)"
	@python3 backend/tests/test_vision_cli.py "$(IMAGE)" --url http://localhost:8888

# Initialize RAG knowledge base
init-rag:
	@echo "📚 Initializing RAG knowledge base..."
	@curl -s -X POST http://localhost:8888/rag/initialize | python3 -m json.tool
	@echo ""
	@echo "✅ Knowledge base initialized!"

# Query RAG system
query-rag:
	@read -p "Enter query: " query; \
	echo "🔍 Querying RAG: $$query"; \
	curl -s "http://localhost:8888/rag/query?q=$$query" | python3 -m json.tool

# Check RAG status
rag-status:
	@echo "📊 RAG System Status:"
	@curl -s http://localhost:8888/rag/status | python3 -m json.tool

# Test ChromaDB connection
test-chromadb:
	@echo "🔍 Testing ChromaDB connection..."
	@python3 backend/tests/test_chromadb_connection.py --host localhost --port 8001

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Clean up everything
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

# Deep clean (including images)
clean-all: clean
	@echo "🗑️  Removing Docker images..."
	docker-compose down -v --rmi all --remove-orphans
	@echo "✅ Deep cleanup complete"

# Show Docker resource usage
stats:
	docker stats --no-stream

# Update dependencies
update-deps:
	@echo "📦 Updating dependencies..."
	docker-compose build --no-cache
	@echo "✅ Dependencies updated"
