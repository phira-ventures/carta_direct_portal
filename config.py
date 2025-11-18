import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable must be set for production")
    
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'database.db')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    WTF_CSRF_ENABLED = True
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Company settings
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Your Company'
    
    # Environment detection
    DEBUG = os.environ.get('FLASK_ENV') != 'production'