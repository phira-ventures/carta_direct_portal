#!/usr/bin/env python3
"""
WSGI configuration for production deployment.
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment variables
os.environ['FLASK_ENV'] = 'production'

# Import the Flask application
from app import app

# Configure logging for production
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configure file handler
    file_handler = RotatingFileHandler('logs/stockholder_portal.log', 
                                     maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Stockholder Portal startup')

if __name__ == "__main__":
    app.run()
else:
    # For WSGI servers like gunicorn
    application = app