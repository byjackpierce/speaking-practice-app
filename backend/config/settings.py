"""
Application Configuration
========================

Centralized configuration management for the Portuguese Gap-Capture API.
Loads environment variables and provides application-wide settings.
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Application settings loaded from environment variables.
    
    Provides centralized configuration for:
    - OpenAI API credentials
    - CORS settings
    - Static file paths
    - Logging configuration
    """
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # App Configuration
    APP_TITLE = "Portuguese Gap-Capture API"
    APP_VERSION = "1.0.0"
    
    # CORS Configuration
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Static Files Configuration
    STATIC_FILES_DIR = "../frontend"
    
    # Logging Configuration
    LOG_LEVEL = "INFO"

# Create a global settings instance
settings = Settings()
