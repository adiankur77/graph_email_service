import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import get_settings
from app.database import init_mongodb
from app.api import email, health
from app.services.scheduler import get_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Microsoft Graph Email Service",
    description="API for sending and retrieving emails using Microsoft Graph API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(health.router)
app.include_router(email.router)

# Initialize MongoDB on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        logger.info("Initializing MongoDB...")
        init_mongodb()
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        # Don't raise exception to allow app to start even if DB is not available

# Start the email scheduler on startup
@app.on_event("startup")
async def startup_scheduler():
    try:
        logger.info("Starting the email scheduler...")
        scheduler = get_scheduler()
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        # Don't raise exception to allow app to start even if scheduler fails

# Shutdown the email scheduler on app shutdown
@app.on_event("shutdown")
async def shutdown_scheduler():
    try:
        logger.info("Shutting down the email scheduler...")
        scheduler = get_scheduler()
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    # Run the FastAPI app using Uvicorn server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)