"""
FastAPI application entry point for Pombi AI Assistant
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from contextlib import asynccontextmanager

from app.config import settings
from app.api.endpoints import chat, modes, health
from app.utils.logging import setup_logging

# Setup structured logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Pombi AI Assistant starting up")
    yield
    # Shutdown
    logger.info("Pombi AI Assistant shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Advanced conversational AI assistant with multiple modes",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Add request ID and timing information to requests"""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(process_time, 4))

    # Log request
    logger.info(
        "Request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
        }
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "type": type(exc).__name__,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "request_id": request_id,
        }
    )


# Include API routers
app.include_router(
    chat.router,
    prefix=f"{settings.api_prefix}/chat",
    tags=["chat"]
)

app.include_router(
    modes.router,
    prefix=f"{settings.api_prefix}/modes",
    tags=["modes"]
)

app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pombi AI Assistant API",
        "version": settings.version,
        "status": "operational",
        "docs": "/docs" if settings.debug else "Documentation disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )