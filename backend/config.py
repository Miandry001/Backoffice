import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Application configuration class.
    Loads settings from environment variables with sensible defaults for development.
    
    SECURITY NOTES:
    - SECRET_KEY must be changed in production
    - SESSION_COOKIE_SECURE should be True in production (HTTPS only)
    - SESSION_COOKIE_HTTPONLY prevents XSS from stealing session cookies
    - SESSION_COOKIE_SAMESITE='Lax' prevents CSRF attacks
    """
    
    # Secret key for session encryption - MUST be changed in production
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///backoffice.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Sheets API credentials path
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_PATH') or 'credentials.json'
    
    # Security settings for session cookies
    # In production, set SESSION_COOKIE_SECURE=True when using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies (XSS protection)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # CORS configuration - restrict to specific frontend domain in production
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Rate limiting configuration
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_PASSWORD_UPPERCASE = True
    REQUIRE_PASSWORD_LOWERCASE = True
    REQUIRE_PASSWORD_DIGIT = True
    REQUIRE_PASSWORD_SPECIAL = True
