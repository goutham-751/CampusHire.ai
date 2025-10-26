from pathlib import Path
from typing import Dict, Any
from pydantic import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    try:
        load_dotenv(dotenv_path=env_path, encoding='utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try with a different encoding
        with open(env_path, 'r', encoding='utf-16') as f:
            content = f.read()
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        load_dotenv(dotenv_path=env_path, encoding='utf-8')

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CampusHire.AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # API
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "*")
    
    # File Uploads
    UPLOAD_FOLDER: str = str(Path(__file__).parent.parent / "uploads")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS: set[str] = {"pdf", "doc", "docx"}
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # External APIs
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")

# Create instance of settings
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)