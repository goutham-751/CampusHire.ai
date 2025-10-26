"""
CampusHire.ai FastAPI Application

Main API server with resume parsing and job matching functionality.
"""

import os
import logging
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import our modules
from backend.config import settings
from backend.parser.extract_resume import ResumeParser
from semantic_ranker import calculate_match_score

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
resume_parser = ResumeParser()
semantic_ranker = calculate_match_score  # Using the function directly

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume parsing and job matching service",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
from fastapi import APIRouter
api_router = APIRouter(prefix=settings.API_V1_STR)

@api_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

@api_router.post("/parse-resume")
async def parse_resume(file_path: str):
    """
    Parse a resume file and extract structured information.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dict containing parsed resume information
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
            
        # Parse the resume
        result = resume_parser.parse_resume(file_path)
        
        if not result.get('parse_success', False):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse resume: {result.get('error', 'Unknown error')}"
            )
            
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )

@api_router.post("/match-job")
async def match_job(resume_data: dict, job_description: str):
    """
    Match a resume against a job description.
    
    Args:
        resume_data: Parsed resume data
        job_description: Job description text
        
    Returns:
        Dict containing matching scores and analysis
    """
    try:
        if not resume_data or not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both resume_data and job_description are required"
            )
            
        # Calculate match score
        match_result = semantic_ranker(resume_data, job_description)
        
        return {
            "success": True,
            "data": match_result
        }
        
    except Exception as e:
        logger.error(f"Error matching job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error matching job: {str(e)}"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail)
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error"
            }
        }
    )

# Include API router
app.include_router(api_router)

# Mount static files (if any)
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_FOLDER}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application...")

# For development
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
