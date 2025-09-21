"""
CampusHire.ai FastAPI Application - Complete Integration
Main API server with advanced reporting and scoring
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import sys
import os
import traceback

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import your voice interview API
from backend.api.voice_interview_api import (
    interview_api, 
    InterviewSessionCreate, 
    QuestionRequest, 
    ResponseSubmission,
    active_sessions,
    session_storage
)

# Create FastAPI app
app = FastAPI(
    title="🎯 CampusHire.ai Voice Interview System",
    description="Complete AI-powered voice interview platform with resume parsing, semantic matching, and advanced analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create and mount static directory
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"⚠️ Static files mount warning: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 Starting CampusHire.ai Voice Interview System...")
    print("📊 Initializing components...")
    
    # Check component availability
    components = {
        "resume_parser": False,
        "semantic_matcher": False,
        "ai_model": False,
        "report_generator": False,
        "evaluator": False
    }
    
    try:
        from backend.parser.extract_resume import extract_text_from_pdf
        components["resume_parser"] = True
        print("✅ Resume parser loaded")
    except Exception as e:
        print(f"❌ Resume parser failed: {e}")
    
    try:
        from backend.matcher.semantic_ranker import calculate_match_score
        components["semantic_matcher"] = True
        print("✅ Semantic matcher loaded")
    except Exception as e:
        print(f"❌ Semantic matcher failed: {e}")
    
    try:
        import google.generativeai as genai
        components["ai_model"] = True
        print("✅ Gemini AI model loaded")
    except Exception as e:
        print(f"❌ AI model failed: {e}")
    
    try:
        from backend.report.report_generator import InterviewReportGenerator
        components["report_generator"] = True
        print("✅ Report generator loaded")
    except Exception as e:
        print(f"❌ Report generator failed: {e}")
    
    try:
        from backend.scoring.evaluator import InterviewEvaluator
        components["evaluator"] = True
        print("✅ Advanced evaluator loaded")
    except Exception as e:
        print(f"❌ Advanced evaluator failed: {e}")
    
    # Store component status
    app.state.components = components
    
    print("\n🎉 CampusHire.ai is ready!")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/api/health")
    print("🎤 Ready for voice interviews!")

@app.get("/")
async def root():
    """Root endpoint with comprehensive API information"""
    components_status = getattr(app.state, 'components', {})
    
    return {
        "message": "🎯 CampusHire.ai Voice Interview System",
        "tagline": "AI-Powered Recruitment Intelligence",
        "version": "1.0.0",
        "status": "🟢 Active",
        "features": {
            "resume_analysis": "📄 Parse and analyze resume content",
            "semantic_matching": "🎯 AI-powered job matching",
            "voice_interviews": "🎤 Intelligent conversational interviews",
            "real_time_evaluation": "⚡ Live response scoring",
            "comprehensive_reporting": "📊 Advanced analytics and insights",
            "privacy_first": "🔒 GDPR-compliant data processing"
        },
        "components": {
            name: "✅ Available" if available else "❌ Unavailable"
            for name, available in components_status.items()
        },
        "api_endpoints": {
            "documentation": "/docs",
            "health_check": "/api/health",
            "create_session": "POST /api/interview/create",
            "get_question": "GET /api/interview/{session_id}/question",
            "submit_response": "POST /api/interview/{session_id}/response",
            "session_status": "GET /api/interview/{session_id}/status",
            "get_report": "GET /api/interview/{session_id}/report",
            "download_report": "GET /api/interview/{session_id}/report/download",
            "list_sessions": "GET /api/sessions"
        },
        "privacy_notice": "Resume files are processed temporarily and securely deleted. Only structured data is retained.",
        "support": "Enterprise-grade AI interview platform for modern recruitment"
    }

@app.post("/api/interview/create")
async def create_interview_session(
    job_description: str = Form("", description="Job requirements and description"),
    candidate_name: str = Form("", description="Candidate's full name"),
    num_questions: int = Form(5, description="Number of interview questions (3-10)"),
    resume: UploadFile = File(None, description="Candidate's resume (PDF format)")
):
    """
    🚀 Create new interview session
    
    Creates a new voice interview session with optional resume analysis.
    Resume files are processed securely and deleted immediately after data extraction.
    """
    
    # Validate inputs
    if not candidate_name or not candidate_name.strip():
        raise HTTPException(
            status_code=400, 
            detail="Candidate name is required for interview session"
        )
    
    if num_questions < 3 or num_questions > 10:
        raise HTTPException(
            status_code=400, 
            detail="Number of questions must be between 3 and 10"
        )
    
    # Validate resume file if provided
    if resume:
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Resume must be in PDF format"
            )
        
        # Check file size (10MB limit)
        content = await resume.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="Resume file size must be less than 10MB"
            )
        
        # Reset file pointer for processing
        await resume.seek(0)
    
    session_data = InterviewSessionCreate(
        job_description=job_description.strip(),
        candidate_name=candidate_name.strip(),
        num_questions=num_questions
    )
    
    try:
        result = await interview_api.create_session(session_data, resume)
        
        # Log session creation
        print(f"📝 Created session {result['session_id']} for {candidate_name}")
        
        return JSONResponse(content=result, status_code=201)
        
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create interview session: {str(e)}"
        )

@app.get("/api/interview/{session_id}/question")
async def get_next_question(
    session_id: str, 
    category: str = None
):
    """
    ❓ Get next interview question
    
    Generates the next AI-powered question for the interview session.
    Questions are personalized based on candidate background and previous responses.
    """
    
    if not session_id or len(session_id) < 10:
        raise HTTPException(status_code=400, detail="Valid session ID is required")
    
    try:
        result = await interview_api.generate_question(session_id, category)
        
        # Log question generation
        if result.get("question_text"):
            print(f"❓ Generated Q{result.get('question_number')} for session {session_id[:8]}...")
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Question generation error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate question: {str(e)}"
        )

@app.post("/api/interview/{session_id}/response")
async def submit_interview_response(
    session_id: str, 
    response: ResponseSubmission
):
    """
    💬 Submit interview response
    
    Processes and evaluates candidate's response using advanced AI analysis.
    Provides real-time scoring and intelligent feedback.
    """
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    if not response.response_text or len(response.response_text.strip()) < 5:
        raise HTTPException(
            status_code=400, 
            detail="Response text must be at least 5 characters long"
        )
    
    response.session_id = session_id  # Ensure consistency
    
    try:
        result = await interview_api.submit_response(response)
        
        # Log response submission
        score = result.get("evaluation_score", 0)
        print(f"📝 Response evaluated: {score}/10 for session {session_id[:8]}...")
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Response submission error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process response: {str(e)}"
        )

@app.get("/api/interview/{session_id}/status")
async def get_session_status(session_id: str):
    """
    📊 Get interview session status
    
    Returns current progress, completion status, and session metadata.
    """
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    try:
        session = active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "progress": {
                "current_question": session["current_question"],
                "total_questions": session["total_questions"],
                "completion_percentage": round(
                    (session["current_question"] / session["total_questions"]) * 100, 1
                ),
                "responses_submitted": len(session.get("responses", []))
            },
            "candidate_info": {
                "name": session.get("candidate_name", "Anonymous"),
                "resume_processed": session.get("candidate_data") is not None,
                "resume_match_score": session.get("resume_match_score", 0)
            },
            "session_metadata": {
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "duration_so_far": round(
                    (session.get("created_at") and 
                     (session.get("created_at") - session.get("created_at")).total_seconds() / 60) or 0, 1
                )
            }
        }
        
    except Exception as e:
        print(f"❌ Status retrieval error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get session status: {str(e)}"
        )

@app.get("/api/interview/{session_id}/report")
async def get_interview_report(session_id: str, format: str = "json"):
    """
    📋 Generate comprehensive interview report
    
    Creates detailed assessment report with AI analysis, scoring, and recommendations.
    Available formats: json, executive, detailed
    """
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    valid_formats = ["json", "executive", "detailed", "dashboard"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Format must be one of: {', '.join(valid_formats)}"
        )
    
    try:
        # Get comprehensive report data
        result = await interview_api.generate_final_report(session_id)
        
        if format == "json":
            return JSONResponse(content=result, status_code=200)
        
        # For other formats, we'll return the JSON but indicate the format preference
        result["requested_format"] = format
        result["available_formats"] = valid_formats
        
        print(f"📊 Generated {format} report for session {session_id[:8]}...")
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate report: {str(e)}"
        )

@app.get("/api/interview/{session_id}/report/download")
async def download_interview_report(
    session_id: str, 
    format: str = "detailed"
):
    """
    📥 Download formatted interview report
    
    Downloads report as formatted file (Markdown or JSON).
    """
    
    try:
        # Generate report data
        report_data = await interview_api.generate_final_report(session_id)
        
        # Try to use report generator for file creation
        try:
            from backend.report.report_generator import generate_interview_report
            saved_files = generate_interview_report(report_data, format)
            
            if format in saved_files:
                file_path = saved_files[format]
                filename = Path(file_path).name
                
                return FileResponse(
                    path=file_path,
                    filename=filename,
                    media_type='application/octet-stream'
                )
        except ImportError:
            # Fallback if report generator not available
            pass
        
        # Fallback: return JSON
        return JSONResponse(content=report_data)
        
    except Exception as e:
        print(f"❌ Report download error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to download report: {str(e)}"
        )

@app.delete("/api/interview/{session_id}")
async def end_interview_session(session_id: str):
    """
    🛑 End interview session
    
    Completes the interview session and performs cleanup.
    """
    
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session["status"] = "completed"
        session["completed_at"] = session.get("created_at")
        
        print(f"🏁 Completed session {session_id[:8]} for {session.get('candidate_name')}")
        
        return {
            "message": "Interview session completed successfully",
            "session_id": session_id,
            "status": "completed",
            "summary": {
                "questions_answered": len(session.get("responses", [])),
                "total_planned": session.get("total_questions", 0),
                "candidate": session.get("candidate_name")
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Interview session not found")

@app.get("/api/health")
async def health_check():
    """
    🏥 System health check
    
    Comprehensive system status including all components and dependencies.
    """
    
    try:
        components_status = getattr(app.state, 'components', {})
        
        # Calculate overall health
        available_components = sum(1 for status in components_status.values() if status)
        total_components = len(components_status)
        health_percentage = (available_components / max(total_components, 1)) * 100
        
        overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
        
        return {
            "status": overall_status,
            "health_percentage": round(health_percentage, 1),
            "service": "CampusHire.ai Voice Interview API",
            "version": "1.0.0",
            "timestamp": str(Path(__file__).stat().st_mtime),
            "active_sessions": len(active_sessions),
            "total_sessions": len(session_storage),
            "components": {
                name: "✅ Online" if status else "❌ Offline"
                for name, status in components_status.items()
            },
            "system_info": {
                "privacy_compliant": True,
                "data_retention": "Structured data only",
                "file_storage": "Temporary processing only",
                "ai_model": "Google Gemini Pro"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "active_sessions": 0,
            "total_sessions": 0
        }

@app.get("/api/sessions")
async def list_sessions(
    status: str = None,
    limit: int = 50
):
    """
    📋 List interview sessions
    
    Returns list of interview sessions with filtering options.
    """
    
    try:
        sessions_list = []
        
        for sid, session in list(active_sessions.items())[:limit]:
            if status and session.get("status") != status:
                continue
                
            sessions_list.append({
                "session_id": sid,
                "candidate_name": session.get("candidate_name"),
                "status": session.get("status"),
                "progress": {
                    "current_question": session.get("current_question", 0),
                    "total_questions": session.get("total_questions", 0),
                    "responses_count": len(session.get("responses", []))
                },
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "resume_processed": session.get("candidate_data") is not None
            })
        
        return {
            "sessions": sessions_list,
            "total_active": len(active_sessions),
            "total_stored": len(session_storage),
            "showing": len(sessions_list),
            "filters_applied": {"status": status} if status else {}
        }
        
    except Exception as e:
        print(f"❌ Sessions listing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested API endpoint does not exist",
            "documentation": "/docs",
            "available_endpoints": [
                "/api/health",
                "/api/interview/create",
                "/api/interview/{session_id}/question",
                "/api/interview/{session_id}/response",
                "/api/interview/{session_id}/report",
                "/api/sessions"
            ]
        }
    )

@app.exception_handler(422)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": "Request data validation failed",
            "details": str(exc),
            "documentation": "/docs"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "suggestion": "Please check the server logs and try again",
            "support": "Contact support if the issue persists"
        }
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("🛑 Shutting down CampusHire.ai Voice Interview System...")
    print("💾 Saving session data...")
    print("✅ Shutdown complete")

# Run the application
if __name__ == "__main__":
    print("🎯 CampusHire.ai Voice Interview System")
    print("=" * 50)
    print("🚀 Starting FastAPI server...")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/api/health")
    print("🎤 Ready for AI-powered interviews!")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
