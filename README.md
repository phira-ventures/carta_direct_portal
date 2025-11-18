# Carta Direct Portal

A secure web portal for managing company shareholdings with enterprise-grade security and Carta-inspired design.

## Features

### For Shareholders
- 🔐 Secure login for admin-created accounts
- 📊 Personal dashboard showing share count and ownership percentage  
- 🔒 Privacy protection - users can only see their own data
- 📱 Responsive design for mobile and desktop

### For Administrators
- 👥 Complete shareholder management
- ✏️ Update individual share counts and notes
- 🏢 Manage total company shares
- 📈 Real-time allocation tracking and statistics
- 💾 SQLite database for easy management

## Technology Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** Bootstrap 5, HTML/CSS/JavaScript
- **Authentication:** Flask-Login with password hashing
- **Forms:** Flask-WTF with CSRF protection

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd carta_direct_portal
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:
   - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `COMPANY_NAME`: Your company name
   - `ADMIN_PASSWORD`: (Optional) Set initial admin password, or it will be auto-generated

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the portal:**
   Open your browser to `http://localhost:5002`

## First Time Setup

### Default Admin Account
On first run, an admin account is automatically created:
- **Email:** `admin@company.com`
- **Password:** If `ADMIN_PASSWORD` is not set in `.env`, a random password will be generated and displayed in the terminal

**⚠️ IMPORTANT:** Change the admin password immediately after first login!

### Sample Test Data (Optional)
For development/testing, create sample shareholders:
```bash
python test_data.py
```

This creates 5 test shareholders with varying share allocations for demo purposes.

## Security Features

- **Strong Password Enforcement:** 12+ characters with complexity requirements
- **Password Hashing:** Werkzeug's secure password hashing
- **CSRF Protection:** All forms protected against Cross-Site Request Forgery
- **Rate Limiting:** IP-based rate limiting on login attempts (10 attempts per 30 minutes)
- **Account Lockout:** Email-based lockout after 5 failed login attempts (30 minute lockout)
- **Session Management:** Secure session handling with automatic revocation on password change
- **Security Headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS, CSP
- **Role-Based Access Control:** Admin vs. regular user permissions
- **Input Validation:** WTForms validation and sanitization on all inputs
- **Email Normalization:** Lowercase email storage to prevent duplicate accounts
- **Database Transactions:** Atomic updates to prevent data inconsistency
- **Secure Logging:** Sensitive data hashed in logs (SHA256)

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Username (currently set to email)
- `name`: Full name of stockholder
- `email`: Email address (unique, normalized to lowercase)
- `password_hash`: Hashed password
- `is_admin`: Boolean admin flag
- `created_at`: Account creation timestamp

### Shares Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `share_count`: Number of shares owned
- `last_updated`: Last modification timestamp
- `notes`: Optional notes about shareholding

### Company Info Table
- `id`: Primary key
- `total_shares`: Total shares authorized by company
- `company_name`: Company name
- `last_updated`: Last modification timestamp

### Login Attempts Table (Rate Limiting)
- `id`: Primary key
- `ip_address`: IP address of login attempt
- `attempt_time`: Timestamp of attempt
- `created_at`: Record creation timestamp

### Failed Login Attempts Table (Account Lockout)
- `id`: Primary key
- `email`: Email address of failed login
- `ip_address`: IP address of attempt
- `attempt_time`: Timestamp of attempt
- `created_at`: Record creation timestamp

### Session Revocations Table
- `user_id`: Primary key
- `revoked_at`: Timestamp when sessions were revoked
- `reason`: Reason for revocation (e.g., password_reset)

## Deployment

### Environment Variables
Set these for production:
- `SECRET_KEY`: Strong secret key for sessions
- `COMPANY_NAME`: Your company name

### Production Deployment
This application is compatible with:
- Heroku
- Railway
- DigitalOcean App Platform
- Any platform supporting Python/Flask

### Production Checklist
- [ ] Set strong `SECRET_KEY` in `.env` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Set secure `ADMIN_PASSWORD` in `.env`
- [ ] Change admin password after first login
- [ ] Use production WSGI server (gunicorn, uWSGI)
- [ ] Configure HTTPS/SSL certificate
- [ ] Set up database backups (scheduled sqlite backups or migrate to PostgreSQL)
- [ ] Configure logging and monitoring
- [ ] Review and test security headers
- [ ] Set up fail2ban or similar for additional DDoS protection
- [ ] Regular security audits

## File Structure
```
carta_direct_portal/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── database.py                     # Database models and utilities
├── forms.py                        # WTForms form definitions
├── wsgi.py                         # WSGI entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .env                            # Environment variables (DO NOT COMMIT)
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── LICENSE                         # Proprietary license
├── test_data.py                    # Sample data creation script
├── deploy.sh                       # Deployment script
├── static/
│   ├── css/
│   │   └── style.css              # Custom CSS styling
│   └── js/
│       ├── main.js                # Frontend JavaScript
│       ├── modal-fix.js           # Modal fixes
│       └── simple-modal.js        # Simple modal handler
└── templates/
    ├── base.html                  # Base template
    ├── login.html                 # Login page
    ├── dashboard.html             # Shareholder dashboard
    ├── admin.html                 # Admin panel
    ├── change_password.html       # Password change form
    ├── create_stockholder.html    # Create stockholder form
    ├── 403.html                   # Forbidden error page
    ├── 404.html                   # Not found error page
    └── 500.html                   # Server error page
```

**Note:** The `instance/` directory is auto-generated when you first run the application and contains the SQLite database. It is excluded from git via `.gitignore`.


## License

Private use only. Not for redistribution.

## Support

For questions or issues, please contact the administrator.