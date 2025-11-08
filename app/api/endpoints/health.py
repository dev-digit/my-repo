"""
Health check endpoints for Pombi AI Assistant
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.ai_engine import AIEngine
from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)

# Create router
router = APIRouter()

# Global AI engine instance (shared with other endpoints)
ai_engine = AIEngine()


async def get_ai_engine() -> AIEngine:
    """Dependency to get AI engine instance"""
    return ai_engine


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.version
    }


@router.get("/detailed")
async def detailed_health_check(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Detailed health check with component status"""
    try:
        health_data = await ai_engine.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.app_name,
            "version": settings.version,
            "components": health_data
        }
    except Exception as e:
        logger.error("Detailed health check failed", extra={"error": str(e)})
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": settings.app_name,
                "version": settings.version,
                "error": str(e)
            }
        )


@router.get("/models")
async def model_health_check(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Check health of available AI models"""
    try:
        models = await ai_engine.get_available_models()
        health_status = await ai_engine.health_check()

        model_health = []
        for model in models:
            model_name = model.get("model", "unknown")
            is_healthy = health_status.get("models", {}).get(model_name, False)

            model_health.append({
                "model": model_name,
                "provider": model.get("provider", "unknown"),
                "status": "healthy" if is_healthy else "unhealthy",
                "capabilities": model.get("capabilities", [])
            })

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "models": model_health,
            "healthy_count": sum(1 for m in model_health if m["status"] == "healthy"),
            "total_count": len(model_health)
        }

    except Exception as e:
        logger.error("Model health check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Model health check failed")


@router.get("/readiness")
async def readiness_check(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Kubernetes readiness probe"""
    try:
        # Check if at least one model is available
        models = await ai_engine.get_available_models()
        if not models:
            raise HTTPException(status_code=503, detail="No models available")

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "models_available": len(models)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }