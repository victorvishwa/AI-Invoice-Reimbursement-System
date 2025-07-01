from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from contextlib import asynccontextmanager

from .routers import analysis, chat
from .database import db_manager
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Intelligent Invoice Reimbursement System...")
    try:
        await db_manager.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intelligent Invoice Reimbursement System...")
    await db_manager.disconnect()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Intelligent Invoice Reimbursement System",
    description="""
    An AI-powered system for analyzing employee invoices against HR policies.
    
    ## Features
    
    * **Invoice Analysis**: Automatically analyze invoices against HR policies
    * **AI-Powered Classification**: Classify invoices as Fully Reimbursed, Partially Reimbursed, or Declined
    * **Vector Search**: Store and search invoice embeddings for intelligent querying
    * **Chat Interface**: Natural language queries about past invoice analyses
    
    ## Endpoints
    
    * `POST /analyze-invoices/` - Analyze employee invoices against HR policy
    * `POST /chat-query/` - Query past invoice analyses using natural language
    """,
    version="1.0.0",
    contact={
        "name": "AI Reimbursement System",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Intelligent Invoice Reimbursement System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze_invoices": "/analyze-invoices/",
            "chat_query": "/chat-query/",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db_manager.client.admin.command('ping')
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "services": {
            "database": db_status,
            "api": "healthy"
        },
        "version": "1.0.0"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "status_code": 500,
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 