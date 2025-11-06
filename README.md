# Iris - AI-Powered Real-Time Assistant

An AI-powered real-time assistant that combines generative AI (LLM-based conversational system) with agentic AI (autonomous tool usage) for object detection and information retrieval.

## Features

- 🎥 **Real-Time Camera Processing** - Stream camera feed for live object detection
- 🤖 **Conversational AI** - LLM-powered chat interface using Ollama
- 👁️ **Object Detection** - YOLOv8 for real-time object recognition
- 👤 **Face Detection** - MediaPipe for face detection
- 🔍 **Web Search** - Autonomous web search using SearXNG for object information
- 📚 **RAG System** - Retrieval-Augmented Generation for knowledge base queries
- 🛠️ **Agentic AI** - AI autonomously decides when to use tools (search, RAG, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flutter Frontend                         │
│                    (Camera + Chat UI)                        │
└────────────────────┬─────────────────────────────────────────┘
                     │ WebSocket
┌────────────────────┼─────────────────────────────────────────┐
│                    │       Docker Containers                  │
│         ┌──────────▼──────────┐                              │
│         │  FastAPI Backend    │──────┐                       │
│         │  (Object Detection, │      │                       │
│         │   Face Detection,   │      │                       │
│         │   Agent, RAG)       │      │                       │
│         └──────────┬──────────┘      │                       │
│                    │                  ▼                       │
│                    │          ┌──────────────┐               │
│                    │          │   SearXNG    │               │
│                    │          │ (Web Search) │               │
│                    │          └──────────────┘               │
└────────────────────┼─────────────────────────────────────────┘
                     │
┌────────────────────┼─────────────────────────────────────────┐
│                    │          Host System                     │
│         ┌──────────▼──────────┐                              │
│         │       Ollama        │                              │
│         │   (LLM on M4 GPU)   │                              │
│         └─────────────────────┘                              │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **macOS** (M1/M2/M3/M4 for GPU acceleration)
- **Docker** and **Docker Compose**
- **Make** (usually pre-installed on macOS)
- **Python 3.11+** (for local development)

## Quick Start

### 1. Install Ollama and Pull Models

```bash
make install-ollama
make pull-models
```

Or manually:
```bash
# Install Ollama
brew install ollama

# Start Ollama
brew services start ollama

# Pull required models
ollama pull llama3.2:3b
ollama pull llava:7b  # Optional, for vision tasks
```

### 2. Build and Start Services

```bash
# Build Docker containers
make build

# Start all services
make up
```

This will start:
- **Backend API** on http://localhost:8000
- **SearXNG** on http://localhost:8080
- **ChromaDB** on http://localhost:8001

### 3. Verify Services

```bash
make health
```

Expected output:
```
🏥 Checking service health...

Ollama (host):
  ✅ Running
  Models: llama3.2:3b, llava:7b

Backend API:
  ✅ Running

SearXNG:
  ✅ Running
```

### 4. Initialize RAG Knowledge Base

```bash
# Initialize the knowledge base with mock data
make init-rag
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/health | jq

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}' | jq

# Test web search
curl "http://localhost:8000/search?q=laptop+computer" | jq

# Test RAG query
curl "http://localhost:8000/rag/query?q=what+is+a+computer" | jq

# Get object info from RAG
curl http://localhost:8000/rag/object/laptop | jq

# Check RAG status
curl http://localhost:8000/rag/status | jq
```

## Makefile Commands

```bash
make help              # Show all available commands
make setup             # Complete setup (Ollama, models, Docker build)
make build             # Build Docker containers
make up                # Start all services
make down              # Stop all services
make restart           # Restart all services
make logs              # View logs from all services
make logs-backend      # View backend logs only
make logs-searxng      # View SearXNG logs only
make health            # Check health of all services
make status            # Show status of all containers
make test              # Run basic tests
make clean             # Stop and remove containers
make shell-backend     # Open shell in backend container
make dev               # Start in development mode (with logs)
```

## API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | Health check (Ollama + SearXNG status) |
| GET | `/models` | List available Ollama models |
| GET | `/sessions` | List active WebSocket sessions |
| POST | `/chat` | Chat endpoint (REST) |
| GET | `/search?q=query` | Web search |
| GET | `/search/object/{name}` | Search for object information |
| GET | `/search/history/{name}` | Search for historical facts |
| GET | `/detection/status` | Detection services status |
| POST | `/detection/analyze` | Analyze image (objects + faces) |
| POST | `/detection/objects` | Detect objects in image |
| POST | `/detection/faces` | Detect faces in image |
| GET | `/detection/classes` | List detectable object classes |

### WebSocket Endpoint

| Type | Endpoint | Description |
|------|----------|-------------|
| WS | `/ws/{session_id}` | WebSocket for camera stream + chat |

Full API documentation available at: http://localhost:8000/docs

## Testing

Iris includes comprehensive testing infrastructure:

### Backend Tests

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Performance Benchmarks

```bash
# Run performance benchmarks
cd backend
python tests/benchmark.py

# Benchmarks:
# - Ollama response time
# - RAG query performance
# - Web search speed
# - Object/face detection speed
# - Agentic AI with tools
```

### Load Testing

```bash
# Test WebSocket server capacity
cd backend
python tests/load_test.py --clients 10 --duration 30
```

### Integration Testing

See `docs/phase5-testing.md` for complete testing guide including:
- Unit tests
- Integration tests
- End-to-end scenarios
- Performance targets
- Acceptance criteria

### User Acceptance Testing

See `docs/user-acceptance-testing.md` for 15 comprehensive test scenarios covering:
- Object and face detection
- AI chat functionality
- Tool usage (RAG, web search)
- Error handling
- Performance under load
- UI/UX validation

## Configuration

### Environment Variables

Create `backend/.env` from `backend/.env.example`:

```bash
# Server
PORT=8000
DEBUG=True

# Ollama (on host for GPU access)
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_VISION_MODEL=llava:7b

# SearXNG (in Docker)
SEARXNG_URL=http://searxng:8080

# Object Detection
YOLO_MODEL=yolov8n.pt
DETECTION_CONFIDENCE=0.5

# RAG
VECTOR_DB_PATH=./data/vectordb
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Project Structure

```
iris/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── api/
│   │   │   ├── routes.py        # REST endpoints
│   │   │   └── websocket.py     # WebSocket handler
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── services/
│   │   │   ├── ollama_service.py      # LLM integration
│   │   │   ├── web_search_service.py  # SearXNG integration
│   │   │   ├── agent_service.py       # Agentic AI
│   │   │   ├── rag_service.py         # RAG system
│   │   │   └── *_detection_service.py # Detection services
│   │   └── utils/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── lib/
│   │   ├── main.dart            # Flutter entry point
│   │   ├── models/              # Data models
│   │   ├── services/            # Camera & WebSocket services
│   │   ├── screens/             # UI screens
│   │   └── widgets/             # Reusable widgets
│   ├── android/                 # Android configuration
│   ├── ios/                     # iOS configuration
│   ├── pubspec.yaml             # Flutter dependencies
│   └── README.md
├── searxng/
│   └── settings.yml             # SearXNG configuration
├── docs/
│   ├── project-plan.md
│   ├── phase1-quickstart.md
│   ├── phase2-detection.md
│   └── phase4-flutter.md
├── docker-compose.yml
├── Makefile
└── README.md
```

## Development

### Local Development (Without Docker)

If you want to run the backend locally:

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Update .env for local development
OLLAMA_HOST=http://localhost:11434
SEARXNG_URL=http://localhost:8080

# Run the server
python -m app.main
```

### Docker Development Mode

```bash
# Start with live logs
make dev

# Or with docker-compose directly
docker-compose up
```

### View Logs

```bash
# All services
make logs

# Backend only
make logs-backend

# SearXNG only
make logs-searxng
```

### Access Container Shell

```bash
make shell-backend
```

## Example Use Cases

### 1. Object Detection + Web Search

User holds a laptop to the camera:

1. **Object Detection**: "I detect a laptop"
2. **User**: "Tell me more about it"
3. **Agentic AI**: Autonomously calls web search tool
4. **Web Search**: Searches SearXNG for "laptop information"
5. **Response**: Returns laptop info with sources
6. **Display**: Shows search results at bottom of UI

### 2. Face Detection

1. Camera detects faces in real-time
2. AI reports: "I detect 2 faces"
3. Privacy-focused: No identification, only counting

### 3. Historical Facts

User shows a computer:

1. **User**: "Tell me about the historical facts"
2. **Agentic AI**: Calls historical facts search tool
3. **Web Search**: Searches "computer history historical facts"
4. **Response**: Returns historical information with sources

## Technologies Used

### Backend
- **FastAPI** - Modern async web framework
- **Ollama** - Local LLM inference (GPU accelerated on M4)
- **SearXNG** - Privacy-respecting metasearch engine
- **YOLOv8** - Object detection
- **MediaPipe** - Face detection
- **ChromaDB** - Vector database for RAG
- **WebSocket** - Real-time communication

### Frontend (Coming in Phase 5)
- **Flutter** - Cross-platform mobile framework
- **Camera Plugin** - Camera access
- **WebSocket Client** - Real-time communication

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## Phase Status

- ✅ **Phase 1**: Backend Foundation (FastAPI, WebSocket, Ollama)
- ✅ **Phase 1.5**: Web Search Integration (SearXNG, Docker)
- ✅ **Phase 1.6**: RAG System (ChromaDB, Knowledge Base)
- ✅ **Phase 2**: Object & Face Detection (YOLOv8, MediaPipe)
- ✅ **Phase 3**: Agentic AI & Tool Calling
- ✅ **Phase 4**: Flutter Frontend (Camera Streaming, Chat UI, Detection Overlay)
- ✅ **Phase 5**: Integration & Testing (Complete Test Suite, Benchmarks, Deployment)
- ✅ **Phase 6**: Final Integration & Optimization (Model Warmup, Performance Testing, Production Ready)

## Deployment

Iris supports multiple deployment scenarios:

### Local Development (Current Setup)
- Backend in Docker containers
- Ollama on host for GPU acceleration
- Flutter app on simulator/emulator
- Perfect for development and testing

### Local Network Deployment
```bash
# 1. Get server IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. Update Flutter app WebSocket URL
# lib/screens/camera_screen.dart:
# serverUrl: 'ws://192.168.1.100:8000'

# 3. Configure firewall
sudo ufw allow 8000/tcp

# 4. Access from any device on network
```

### Production Cloud Deployment
- Deploy on AWS/GCP/Azure/DigitalOcean
- GPU instance for Ollama (recommended)
- Nginx reverse proxy with SSL
- HTTPS/WSS for secure connections
- Load balancing for scalability

See `docs/deployment-guide.md` for complete deployment instructions including:
- Server provisioning
- SSL certificate setup
- Production configuration
- Monitoring and logging
- Backup strategies
- Scaling options

## Documentation

Complete documentation available in `docs/`:

- **`project-plan.md`** - Original project plan and architecture
- **`phase1-quickstart.md`** - Phase 1 backend setup
- **`phase2-detection.md`** - Detection services documentation
- **`phase4-flutter.md`** - Flutter implementation guide
- **`flutter-quickstart.md`** - Quick Flutter setup guide
- **`phase5-testing.md`** - Complete testing guide
- **`phase6-completion-report.md`** - Phase 6 integration test results (4/4 scenarios passed)
- **`phase6-optimizations.md`** - Performance optimization details (67% faster first request)
- **`user-acceptance-testing.md`** - UAT scenarios (15 test cases)
- **`deployment-guide.md`** - Production deployment guide
- **`troubleshooting-guide.md`** - Comprehensive troubleshooting

## Troubleshooting

For detailed troubleshooting, see `docs/troubleshooting-guide.md`.

### Quick Fixes

### Ollama Not Available

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
brew services start ollama
# Or
ollama serve
```

### SearXNG Not Working

```bash
# Check SearXNG container
docker-compose logs searxng

# Restart SearXNG
docker-compose restart searxng

# Test SearXNG directly
curl "http://localhost:8080/search?q=test&format=json"
```

### Backend Can't Connect to Ollama

Make sure `host.docker.internal` is properly configured in docker-compose.yml:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Port Conflicts

Change ports in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8000 to 8001
```

## Performance

### Production Metrics (Phase 6 Testing)

- **Vision Analysis**: 2.9s first request (with warmup), 1.8-3.3s subsequent
- **Chat Responses**: 0.4-2.5s average response time
- **Model Warmup**: 1.7s during startup (loads models into memory)
- **Success Rate**: 100% (4/4 test scenarios passed)

### Infrastructure Performance

- **Ollama on M4**: Utilizes Metal GPU for fast inference
- **Frame Processing**: 10-15 FPS recommended for real-time detection
- **WebSocket**: Low-latency bidirectional communication
- **SearXNG**: Fast metasearch across multiple search engines

### Optimization Features

- ✅ Automatic model warmup on startup (67% faster first request)
- ✅ Context-aware conversation management
- ✅ Efficient model switching (vision → chat)
- ✅ Docker healthchecks for reliability

## Security & Privacy

- **SearXNG**: Privacy-respecting search, no tracking
- **Local LLM**: Ollama runs locally, no data sent to cloud
- **Face Detection**: Detection only, no identification or storage
- **No Data Collection**: All processing happens locally

## Contributing

This is a prototype project. Future enhancements:
- Multiple object detection models
- Custom RAG knowledge bases
- Voice interaction
- Mobile app optimization
- Cloud deployment options

## License

MIT

## Support

For issues and questions:
- Check `docs/` directory for detailed documentation
- Review `backend/README.md` for backend-specific info
- Check logs: `make logs`
- Health check: `make health`

## Credits

Built with:
- [Ollama](https://ollama.ai) - Local LLM inference
- [SearXNG](https://searxng.org) - Metasearch engine
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection
- [MediaPipe](https://mediapipe.dev) - Face detection
- [ChromaDB](https://www.trychroma.com) - Vector database
