#!/usr/bin/env python3
"""
Startup script for the Vision AI backend.
Ensures settings from .env are properly loaded.
"""
import uvicorn
from app.config import settings


if __name__ == "__main__":
    print(f"Starting Vision AI Backend...")
    print(f"  Host: {settings.api_host}")
    print(f"  Port: {settings.api_port}")
    print(f"  Ollama: {settings.ollama_host}")
    print(f"  Vision Model: {settings.vision_model}")
    print(f"  Chat Model: {settings.chat_model}")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
