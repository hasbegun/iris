# Vision AI Backend

A focused, minimal backend for object detection and description using Ollama vision models.

## Overview

This backend provides a simple API for analyzing images and videos with vision AI models. It supports:
- Single image analysis
- Video stream frame analysis
- Conversational follow-up questions with context
- Session management for maintaining conversation history

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── api/
│   │   ├── vision.py        # Vision analysis endpoints
│   │   └── chat.py          # Chat endpoints
│   ├── services/
│   │   ├── ollama_service.py    # Ollama API integration
│   │   └── context_manager.py   # Session & context management
│   └── models/
│       └── schemas.py       # Pydantic models
├── tests/
│   ├── cli_test.py          # CLI testing tool
│   └── README.md            # CLI tool documentation
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Install Ollama Models

```bash
ollama pull llava:latest
ollama pull gemma3:latest

# Alternative vision models (if preferred):
# ollama pull granite3.2-vision:latest
```

### 2. Setup Environment

```bash
cd backend
cp .env.example .env
# Edit .env if needed
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
# Using the run script (recommended - loads .env automatically)
python run.py

# Or using app.main directly
python -m app.main

# Or with uvicorn (must specify port manually)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

The API will be available at `http://localhost:9000`

### 5. Test with CLI Tool

```bash
# Health check
python tests/cli_test.py health

# Analyze an image
python tests/cli_test.py image photo.jpg "What do you see?"

# Analyze a video
python tests/cli_test.py video clip.mp4 "What's happening?" --interval 2.0

# Interactive follow-ups
python tests/cli_test.py image photo.jpg "Describe this" --interactive
```

## API Endpoints

### Health Check
```
GET /api/health
```

Returns API status and available Ollama models.

### Analyze Image
```
POST /api/vision/analyze
```

**Form Data**:
- `image`: Image file (jpg, png, webp)
- `prompt`: Question or instruction
- `session_id` (optional): Session ID for context

**Response**:
```json
{
  "session_id": "uuid",
  "response": "AI response text",
  "model_used": "llama3.2-vision:latest",
  "timestamp": "2025-10-31T..."
}
```

### Analyze Video Frame
```
POST /api/vision/stream
```

**Form Data**:
- `frame`: Frame image
- `prompt`: Question or instruction
- `session_id` (optional): Session ID
- `frame_number` (optional): Frame index
- `timestamp_ms` (optional): Timestamp in ms

**Response**: Same as image analysis

### Chat (Follow-up)
```
POST /api/chat
```

**JSON Body**:
```json
{
  "message": "Follow-up question",
  "session_id": "uuid"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "response": "AI response",
  "model_used": "llama3.2:3b",
  "timestamp": "2025-10-31T..."
}
```

## Configuration

Edit `.env` file to customize:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
VISION_MODEL=llava:latest
CHAT_MODEL=gemma3:latest

# API Configuration
API_HOST=0.0.0.0
API_PORT=9000

# Context Management
MAX_CONTEXT_MESSAGES=10
CONTEXT_TTL_SECONDS=3600

# Video Processing
VIDEO_FRAME_INTERVAL=1.0
MAX_VIDEO_DURATION=300
```

## Model Selection

### Vision Models (for image/video analysis)
- `llava:latest` - Recommended (7B params, Q4_0)
- `granite3.2-vision:latest` - Alternative (2.5B params, Q4_K_M)
- Others: Check `ollama list` for available models

### Chat Models (for follow-up questions)
- `gemma3:latest` - Recommended (4.3B params, Q4_K_M)
- `mistral:latest` - Alternative (7.2B params, Q4_0)
- `deepseek-r1:32b` - More capable but slower

### Checking Available Models
```bash
# List installed models
ollama list

# Pull a new model
ollama pull <model-name>
```

## How It Works

### Session Management

1. User sends image/video with prompt
2. Backend creates a session (UUID) and stores context
3. Vision model analyzes the content
4. Response is returned with session_id
5. User can ask follow-ups using the session_id
6. Chat model uses context from previous interactions
7. Sessions expire after 1 hour of inactivity

### Video Processing

For videos, the CLI tool:
1. Opens the video file with OpenCV
2. Extracts frames at specified intervals
3. Sends each frame to `/api/vision/stream`
4. Maintains session context across frames
5. Aggregates responses for summary

## Testing

See [tests/README.md](tests/README.md) for comprehensive CLI testing guide.

Quick examples:

```bash
# Test image analysis
python tests/cli_test.py image test.jpg "What objects are visible?"

# Test 1-minute video (30 frames at 2s intervals)
python tests/cli_test.py video clip.mp4 "Describe activity" --interval 2.0 --max-frames 30

# Test with follow-up questions
python tests/cli_test.py image test.jpg "What do you see?" -i
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:9000/docs`
- ReDoc: `http://localhost:9000/redoc`

## Troubleshooting

### Ollama not connecting
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Model not found or incompatible
```bash
# List installed models
ollama list

# Pull required models
ollama pull llava:latest
ollama pull gemma3:latest

# If you get "no longer compatible" error:
# 1. Check your Ollama version: ollama --version
# 2. Update Ollama if needed
# 3. Re-pull the model: ollama pull <model-name>
```

### Model compatibility issues
If you see errors like "model is no longer compatible":
1. The model format has changed in newer Ollama versions
2. Delete and re-pull the model:
   ```bash
   ollama rm <model-name>
   ollama pull <model-name>
   ```
3. Or use an alternative model from the Model Selection section

### Port already in use
Edit `.env` and change `API_PORT` to a different port.

## Development

Run with auto-reload (recommended):
```bash
python run.py
```

This automatically loads settings from `.env` and starts the server on the configured port.

Alternative methods:
```bash
# Using app.main
python -m app.main

# Using uvicorn directly (must specify port)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

## License

See project root for license information.
