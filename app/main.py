# app/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.core.config import get_settings
from app.db.session import init_db, close_db_connections
from app.api import document, payment
from app.services.stripe_service import stripe_service
from app.core.security import add_security_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    try:
        # Startup
        logger.info("Starting application...")

        # Initialize database
        init_db()

        # Create required directories
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        # Verify Stripe configuration
        await stripe_service.create_payment_intent(
            settings.MIN_CHARGE,
            metadata={"test": "startup_check"}
        )

        logger.info("Application startup completed")
        yield

    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        close_db_connections()
        logger.info("Application shutdown completed")


# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered document analysis service",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
add_security_middleware(app)

# Include routers
app.include_router(
    document.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)
app.include_router(
    payment.router,
    prefix=f"{settings.API_V1_STR}/payments",
    tags=["payments"]
)


# Root endpoint
@app.get("/")
async def root(request: Request):
    """
    Render the main application page.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
            "min_charge": settings.MIN_CHARGE / 100  # Convert to currency units
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions.
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": exc.status_code,
            "error_message": exc.detail
        },
        status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "Internal server error"
        },
        status_code=500
    )


# Development server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,
        log_level="info"
    )