"""
ML Service Runner
Start the ML service with uvicorn
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.auto_reload,  # Explicit control over auto-reload (default: False)
        log_level="info",
        access_log=True
    )
