"""
Main FastAPI application for vision AI backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from .config import settings
from .api import vision, chat, agent, images, ml_proxy, voice_query
from .services.ollama_service import ollama_service
from .services.context_manager import context_manager
from .services.ml_client import ml_client
from .models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting up application...")
    logger.info(f"  Vision Model: {settings.vision_model}")
    logger.info(f"  Chat Model: {settings.chat_model}")

    context_manager.start_cleanup_task()

    # Check Ollama connection
    connected, models = await ollama_service.check_health()
    if connected:
        logger.info(f"Connected to Ollama. Available models: {len(models)}")

        # Check required models
        vision_available = await ollama_service.verify_model_available(settings.vision_model)
        chat_available = await ollama_service.verify_model_available(settings.chat_model)

        if vision_available:
            logger.info(f"✓ Vision model '{settings.vision_model}' is available")
        else:
            logger.warning(
                f"✗ Vision model '{settings.vision_model}' NOT available. "
                f"Run: ollama pull {settings.vision_model}"
            )

        if chat_available:
            logger.info(f"✓ Chat model '{settings.chat_model}' is available")
        else:
            logger.warning(
                f"✗ Chat model '{settings.chat_model}' NOT available. "
                f"Run: ollama pull {settings.chat_model}"
            )

        # Warm up models for faster first request
        if vision_available and chat_available:
            await ollama_service.warmup_models()
    else:
        logger.warning("Could not connect to Ollama. Please ensure it's running.")

    # Check ML service connection
    try:
        ml_health = await ml_client.health_check()
        if ml_health.get("status") == "healthy":
            logger.info(f"✓ ML Service connected ({ml_health.get('device')})")
            logger.info(f"  Models loaded: {ml_health.get('models_loaded')}")
        else:
            logger.warning("✗ ML Service is not healthy")
    except Exception as e:
        logger.warning(f"✗ Could not connect to ML Service: {e}")
        logger.warning("  Agent features will not work without ML Service")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Vision AI Backend",
    description="Object detection and description API using Ollama",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vision.router)
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(images.router)
app.include_router(ml_proxy.router)  # ML service proxy for live camera
app.include_router(ml_proxy.api_router)  # ML service proxy for static images
app.include_router(voice_query.router)  # Voice query with hallucination prevention

# Mount static files for annotated images
annotated_images_path = Path(__file__).parent.parent / "annotated_images"
annotated_images_path.mkdir(exist_ok=True)
app.mount("/annotated", StaticFiles(directory=str(annotated_images_path)), name="annotated")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Vision AI Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    connected, models = await ollama_service.check_health()

    return HealthResponse(
        status="healthy" if connected else "degraded",
        ollama_connected=connected,
        available_models=models
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
