# CLI Test Tool Documentation

A comprehensive command-line interface for testing the Vision AI backend with both images and videos.

## Features

- **Image Analysis**: Analyze single images with custom prompts
- **Video Analysis**: Extract and analyze frames from videos (up to 1 minute or longer)
- **Interactive Chat**: Ask follow-up questions about analyzed content
- **Session Management**: Maintains conversation context across interactions
- **Health Checks**: Verify API and Ollama connectivity

## Prerequisites

1. **Ollama**: Must be running locally with vision models installed
   ```bash
   # Install required models
   ollama pull llava:latest
   ollama pull gemma3:latest
   ```

2. **Backend API**: The FastAPI server must be running
   ```bash
   cd backend
   python run.py
   ```

3. **Dependencies**: Install Python packages
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Health Check

Verify the API is running and Ollama is connected:

```bash
python tests/cli_test.py health
```

Example output:
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "available_models": [
    "llava:latest",
    "gemma3:latest",
    "granite3.2-vision:latest"
  ]
}
```

### Image Analysis

Analyze a single image:

```bash
python tests/cli_test.py image path/to/image.jpg "What objects do you see in this image?"
```

**Supported formats**: JPG, PNG, WEBP

Example:
```bash
python tests/cli_test.py image photo.jpg "Describe the scene"
```

Output:
```
Analyzing image: photo.jpg
Prompt: Describe the scene

============================================================
Response:
============================================================
I can see a modern kitchen with stainless steel appliances,
granite countertops, and a large island in the center...

------------------------------------------------------------
Session ID: 550e8400-e29b-41d4-a716-446655440000
Model: llava:latest
```

### Video Analysis

Analyze video frames at specified intervals:

```bash
python tests/cli_test.py video path/to/video.mp4 "What is happening in this video?" --interval 2.0 --max-frames 30
```

**Parameters**:
- `--interval`: Time between analyzed frames in seconds (default: 1.0)
- `--max-frames`: Maximum number of frames to analyze (default: 60)

Example for 1-minute video:
```bash
# Analyze every 2 seconds (30 frames for 60-second video)
python tests/cli_test.py video recording.mp4 "Describe the activity" --interval 2.0 --max-frames 30
```

Output:
```
Processing video: recording.mp4
Frame interval: 2.0s, Max frames: 30
Video info: 30.00 FPS, 1800 frames, 60.00s duration

Analyzing frame 1/30 (video frame 0, 0.00s)... ✓
Analyzing frame 2/30 (video frame 60, 2.00s)... ✓
...

============================================================
Video Analysis Summary:
============================================================

[Frame 1 @ 0.00s]
The video shows a person entering a room...

[Frame 2 @ 2.00s]
The person is now walking towards the desk...
```

### Interactive Mode

Ask follow-up questions after analyzing an image or video:

```bash
python tests/cli_test.py image photo.jpg "What do you see?" --interactive
```

Or for video:
```bash
python tests/cli_test.py video clip.mp4 "What's happening?" --interval 1.0 --interactive
```

Interactive session:
```
============================================================
Interactive mode - Ask follow-up questions
Commands: 'quit' or 'exit' to end, 'new' for new analysis
============================================================

You: What color is the object you mentioned?