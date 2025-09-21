"""
Configuration settings for CampusHire.ai API
"""
import os
from pathlib import Path

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True
API_LOG_LEVEL = "info"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
RESUMES_DIR = DATA_DIR / "resumes"
JOBS_DIR = DATA_DIR / "job_descriptions"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
RESUMES_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# AI Configuration
GEMINI_MODEL = "gemini-pro"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# Interview Configuration
DEFAULT_QUESTIONS = 5
MAX_QUESTIONS = 10
MIN_QUESTIONS = 3

# Privacy & Security
SECURE_DELETE = True
AUDIT_LOGGING = True
SESSION_TIMEOUT_MINUTES = 120

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:8501",  # Streamlit default
    "http://127.0.0.1:8501",
    "http://localhost:3000",  # React default
]

print(f"📁 Project root: {PROJECT_ROOT}")
print(f"💾 Data directory: {DATA_DIR}")
