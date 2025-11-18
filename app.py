from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError, generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import time
import hashlib
from config import Config
from database import (init_database, User, get_total_stocks, get_all_stockholders,
                     update_user_stocks, update_total_stocks, create_user, delete_user, update_user_info, update_user_password,
                     record_login_attempt, check_rate_limit, cleanup_old_login_attempts,
                     record_failed_login_attempt, check_account_lockout, clear_failed_login_attempts,
                     revoke_user_sessions, is_session_revoked)
from forms import LoginForm, UpdateStocksForm, UpdateTotalStocksForm, CreateStockholderForm, ChangePasswordForm, ResetPasswordForm

app = Flask(__name__)
app.config.from_object(Config)

def hash_for_logging(sensitive_value):
    """
    Hash sensitive values for safe logging.
    Uses SHA256 and returns first 8 chars of hash for correlation without revealing actual values.
    """
    if not sensitive_value:
        return 'NONE'
    hash_object = hashlib.sha256(str(sensitive_value).encode())
    return hash_object.hexdigest()[:8]

def rate_limit(max_attempts=5, window_minutes=15):
    """Rate limiting decorator for login attempts using database."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use direct connection IP to prevent spoofing attacks
            client_ip = request.remote_addr

            # Check if rate limit exceeded
            is_limited, attempt_count = check_rate_limit(client_ip, max_attempts, window_minutes)

            if is_limited:
                flash(f'Too many login attempts. Please try again in {window_minutes} minutes.', 'error')
                app.logger.warning(f'Rate limit exceeded for IP {client_ip} ({attempt_count} attempts)')
                return render_template('login.html', form=LoginForm())

            # Record this attempt
            record_login_attempt(client_ip)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def check_session_validity():
    """Check if current user's session has been revoked."""
    if current_user.is_authenticated:
        session_created = session.get('created_at', 0)

        if is_session_revoked(current_user.id, session_created):
            logout_user()
            flash('Your session has been invalidated. Please log in again.', 'info')
            return redirect(url_for('login'))

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; img-src 'self' data:;"
    return response

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# Initialize database on first run
init_database()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_attempts=10, window_minutes=30)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Check if account is locked due to failed attempts
        is_locked, attempts_left, lockout_time = check_account_lockout(email)
        if is_locked:
            flash(f'Account locked due to too many failed attempts. Try again in {lockout_time} minutes.', 'error')
            app.logger.warning(f'Account lockout triggered for {hash_for_logging(email)} from IP {request.remote_addr}')
            return render_template('login.html', form=form)

        user = User.get_by_email(email)

        if user and check_password_hash(user.password_hash, form.password.data):
            # Successful login - clear failed attempts
            clear_failed_login_attempts(email)
            login_user(user, remember=True)

            # Store session creation time for session revocation checks
            session['created_at'] = time.time()

            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            # Failed login - record attempt
            record_failed_login_attempt(email, request.remote_addr)

            # Check how many attempts remaining
            is_locked, attempts_left, lockout_time = check_account_lockout(email)

            if is_locked:
                flash(f'Too many failed attempts. Account locked for {lockout_time} minutes.', 'error')
            elif attempts_left <= 2:
                flash(f'Invalid email or password. {attempts_left} attempts remaining before lockout.', 'error')
            else:
                flash('Invalid email or password.', 'error')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    stocks_info = current_user.get_stocks()
    ownership_percentage = current_user.get_ownership_percentage()
    total_stocks = get_total_stocks()
    
    return render_template('dashboard.html', 
                         stocks_info=stocks_info,
                         ownership_percentage=ownership_percentage,
                         total_stocks=total_stocks)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    stockholders = get_all_stockholders()
    total_stocks = get_total_stocks()
    
    # Calculate percentages and total allocated stocks
    total_allocated = 0
    stockholders_data = []
    
    for stockholder in stockholders:
        stock_count = stockholder['stock_count'] or 0
        percentage = (stock_count / total_stocks * 100) if total_stocks > 0 else 0
        total_allocated += stock_count
        
        stockholders_data.append({
            'id': stockholder['id'],
            'name': stockholder['name'],
            'email': stockholder['email'],
            'stock_count': stock_count,
            'percentage': percentage
        })
    
    # Sort stockholders by ownership percentage (descending), then by last name (ascending)
    stockholders_data.sort(key=lambda x: (-x['percentage'], x['name'].split()[-1].lower()))
    
    unallocated_stocks = total_stocks - total_allocated
    
    # Create forms
    total_stocks_form = UpdateTotalStocksForm()
    total_stocks_form.total_stocks.data = total_stocks
    
    return render_template('admin.html',
                         stockholders=stockholders_data,
                         total_stocks=total_stocks,
                         total_allocated=total_allocated,
                         unallocated_stocks=unallocated_stocks,
                         total_stocks_form=total_stocks_form,
                         csrf_token=generate_csrf)

@app.route('/admin/update_stocks', methods=['POST'])
@login_required
@rate_limit(max_attempts=50, window_minutes=1)
def update_stocks():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    form = UpdateStocksForm()

    if form.validate_on_submit():
        try:
            user_id = form.user_id.data
            name = form.name.data.strip()
            email = form.email.data.strip().lower()
            stock_count = form.stock_count.data

            # Prevent updating admin users through this endpoint
            user_to_update = User.get(user_id)
            if user_to_update and user_to_update.is_admin:
                flash('Cannot update admin users through this interface.', 'error')
                return redirect(url_for('admin_dashboard'))

            success = update_user_info(user_id, name, email, stock_count)
            if success:
                flash('Stockholder updated successfully.', 'success')
                app.logger.info(
                    f'Admin ID {current_user.id} updated user ID {user_id} '
                    f'(email_hash: {hash_for_logging(email)})'
                )
            else:
                flash('Update failed. Email might already be in use.', 'error')

        except Exception as e:
            flash('An unexpected error occurred.', 'error')
            app.logger.error(f'Error updating stockholder: {str(e)}')
    else:
        # Display validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_total_stocks', methods=['POST'])
@login_required
@rate_limit(max_attempts=3, window_minutes=5)
def update_total_stocks_route():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    form = UpdateTotalStocksForm()
    if form.validate_on_submit():
        try:
            update_total_stocks(form.total_stocks.data)
            flash('Total stocks updated successfully.', 'success')
        except Exception as e:
            flash(f'Error updating total stocks: {str(e)}', 'error')
    else:
        flash('Invalid form data.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_stockholder', methods=['GET', 'POST'])
@login_required
@rate_limit(max_attempts=10, window_minutes=5)
def create_stockholder():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    form = CreateStockholderForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user_by_email = User.get_by_email(form.email.data.strip().lower())

        if existing_user_by_email:
            flash('Email already exists. Please choose a different one.', 'error')
            return render_template('create_stockholder.html', form=form)

        # Create new stockholder
        password_hash = generate_password_hash(form.password.data)
        user_id = create_user(
            form.name.data,
            form.email.data.strip().lower(),
            password_hash,
            form.stock_count.data
        )
        
        if user_id:
            flash(f'Stockholder "{form.name.data}" created successfully with {form.stock_count.data} stocks.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Failed to create stockholder. Email might already be in use.', 'error')
    
    return render_template('create_stockholder.html', form=form)

@app.route('/admin/delete_stockholder/<int:user_id>', methods=['POST'])
@login_required
@rate_limit(max_attempts=5, window_minutes=1)
def delete_stockholder(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user info for confirmation message
    user = User.get(user_id)
    if not user:
        flash('Stockholder not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if user.is_admin:
        flash('Cannot delete admin users.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if delete_user(user_id):
        flash(f'Stockholder "{user.name}" has been deleted successfully.', 'success')
    else:
        flash('Failed to delete stockholder.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Verify current password
        user = User.get_by_email(current_user.email)
        if user and check_password_hash(user.password_hash, form.current_password.data):
            # Update password
            new_password_hash = generate_password_hash(form.new_password.data)
            if update_user_password(current_user.id, new_password_hash):
                # Logout user to force re-authentication with new password
                logout_user()
                flash('Your password has been changed successfully. Please log in again.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Failed to update password. Please try again.', 'error')
        else:
            flash('Current password is incorrect.', 'error')
    
    return render_template('change_password.html', form=form)

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
@rate_limit(max_attempts=10, window_minutes=5)
def reset_user_password(user_id):
    """Admin endpoint to reset a user's password."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    # Get user to reset
    user = User.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Prevent resetting admin passwords
    if user.is_admin:
        flash('Cannot reset admin user passwords through this interface.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Use form validation for CSRF protection and strong password enforcement
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            # Hash and update password
            new_password_hash = generate_password_hash(form.new_password.data)
            if update_user_password(user_id, new_password_hash):
                # Revoke all sessions for this user
                revoke_user_sessions(user_id, reason='admin_password_reset')

                flash(f'Password reset successful for {user.email}. User will be logged out.', 'success')
                app.logger.info(
                    f'Admin ID {current_user.id} reset password for user ID {user_id} '
                    f'(email_hash: {hash_for_logging(user.email)})'
                )
            else:
                flash('Failed to reset password. Please try again.', 'error')
        except Exception as e:
            flash('An error occurred while resetting password.', 'error')
            app.logger.error(f'Error resetting password for user {user_id}: {str(e)}')
    else:
        # Display validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500

@app.errorhandler(CSRFError)
def csrf_error(error):
    flash('CSRF token expired. Please try again.', 'error')
    return redirect(url_for('login'))

def startup_cleanup():
    """Cleanup old login attempts when app starts."""
    try:
        cleanup_old_login_attempts(hours=24)
        app.logger.info('Cleaned up old login attempts')
    except Exception as e:
        app.logger.error(f'Error during startup cleanup: {e}')

# Perform cleanup on startup
with app.app_context():
    startup_cleanup()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='127.0.0.1', port=5002)