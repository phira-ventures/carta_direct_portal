#!/bin/bash

# Production Deployment Script for Stockholder Portal

echo "=== Stockholder Portal Production Deployment ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure production values"
    exit 1
fi

# Check if SECRET_KEY is set
if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your-very-long-random-secret-key" .env; then
    echo "❌ Error: SECRET_KEY not properly configured!"
    echo "Please set a secure SECRET_KEY in .env file"
    echo "Generate one with: python3 -c 'import secrets; print(secrets.token_hex(32))'"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Verify required environment variables
if [ "$FLASK_ENV" != "production" ]; then
    echo "❌ Error: FLASK_ENV must be set to 'production'"
    exit 1
fi

echo "✓ Environment configuration verified"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set database permissions
echo "🔒 Setting database permissions..."
chmod 600 instance/database.db 2>/dev/null || echo "Database file not found (will be created on first run)"

# Create logs directory
mkdir -p logs
chmod 755 logs

# Run database initialization (if needed)
echo "🗄️ Initializing database..."
python3 -c "from database import init_database; init_database()"

echo "✓ Database initialized"

# Test configuration
echo "🧪 Testing configuration..."
python3 -c "
from config import Config
print('✓ Configuration loaded successfully')
print(f'✓ Debug mode: {Config.DEBUG}')
print(f'✓ Company: {Config.COMPANY_NAME}')
"

echo ""
echo "🚀 Deployment complete!"
echo ""
echo "To start the application:"
echo "  Production: gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application"
echo "  Development: python3 app.py"
echo ""
echo "⚠️  Important reminders:"
echo "  - Use HTTPS in production"
echo "  - Set up reverse proxy (nginx/Apache)"
echo "  - Configure firewall rules"
echo "  - Set up database backups"
echo "  - Monitor logs in logs/ directory"