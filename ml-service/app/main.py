"""
ML Service - Main FastAPI Application
YOLO-based object detection, segmentation, and face detection microservice

Refactored to use dependency injection for better testability and maintainability
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.services.yolo_service import YOLOService
from app.services.video_yolo_service import VideoYOLOService
from app.api import yolo
from app.models.schemas import HealthResponse, MetricsResponse
from app.dependencies import set_yolo_service_instance, set_video_yolo_service_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global service instances
yolo_service_instance = None
video_yolo_service_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting ML Service...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Device: {settings.device}")

    global yolo_service_instance, video_yolo_service_instance

    try:
        # Initialize YOLO service
        yolo_service_instance = YOLOService()

        # Set service instance for dependency injection
        set_yolo_service_instance(yolo_service_instance)

        # Load models
        await yolo_service_instance.load_models()

        # Initialize Video YOLO service (depends on YOLO service)
        logger.info("Initializing Video YOLO service...")
        video_yolo_service_instance = VideoYOLOService(yolo_service_instance)
        set_video_yolo_service_instance(video_yolo_service_instance)

        logger.info("✅ ML Service ready (with video support)")

    except Exception as e:
        logger.error(f"❌ Failed to start ML Service: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down ML Service...")


# Create FastAPI app
app = FastAPI(
    title="ML Service - YOLO",
    description="Microservice for object detection, segmentation, and face detection using YOLO",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression middleware (Phase 3 optimization)
# Compresses responses > 500 bytes with gzip encoding
# Reduces JSON response size by 70-80% for detection/segmentation responses
app.add_middleware(
    GZipMiddleware,
    minimum_size=500,  # Only compress responses larger than 500 bytes
    compresslevel=6    # Compression level 1-9 (6 is a good balance of speed/ratio)
)

# Include routers
app.include_router(yolo.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Service - YOLO",
        "version": "1.0.0",
        "status": "running",
        "device": settings.device,
        "endpoints": {
            "images": {
                "detect": "/api/detect",
                "detect_stream": "/api/detect-stream",
                "segment": "/api/segment",
                "detect_faces": "/api/detect-faces",
                "detect_annotated": "/api/detect-annotated",
                "detect_faces_annotated": "/api/detect-faces-annotated"
            },
            "videos": {
                "detect_video": "/api/detect-video",
                "detect_faces_video": "/api/detect-faces-video",
                "detect_video_annotated": "/api/detect-video-annotated",
                "detect_video_async": "/api/detect-video-async"
            },
            "tasks": {
                "task_status": "/api/task/{task_id}/status",
                "list_tasks": "/api/tasks"
            },
            "system": {
                "health": "/health",
                "metrics": "/metrics",
                "docs": "/docs"
            }
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring

    Returns service health status and model loading state
    """
    if yolo_service_instance is None:
        return {
            "status": "unhealthy",
            "models_loaded": False,
            "device": settings.device,
            "message": "YOLO service not initialized"
        }

    try:
        memory_usage = yolo_service_instance.get_memory_usage()

        return {
            "status": "healthy" if yolo_service_instance.models_loaded else "initializing",
            "models_loaded": yolo_service_instance.models_loaded,
            "device": yolo_service_instance.device,
            "memory_available": f"{memory_usage:.2f} MB"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "models_loaded": False,
            "device": settings.device,
            "message": str(e)
        }


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Service metrics endpoint for monitoring and observability

    Returns request counts, inference times, and resource usage
    """
    if yolo_service_instance is None:
        return {
            "total_requests": 0,
            "avg_inference_time_ms": 0.0,
            "memory_usage_mb": 0.0,
            "device": settings.device,
            "uptime_seconds": 0.0
        }

    return {
        "total_requests": yolo_service_instance.total_requests,
        "avg_inference_time_ms": yolo_service_instance.get_avg_inference_time(),
        "memory_usage_mb": yolo_service_instance.get_memory_usage(),
        "device": yolo_service_instance.device,
        "uptime_seconds": yolo_service_instance.get_uptime()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.environment == "development"),
        log_level="info"
    )
