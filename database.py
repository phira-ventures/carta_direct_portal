import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from config import Config


def init_database():
    """Initialize the database with required tables."""
    db_path = Config.DATABASE_PATH

    # Ensure the instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Stocks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_count INTEGER NOT NULL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
    )

    # Company info table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS company_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_stocks INTEGER NOT NULL DEFAULT 0,
            company_name TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Login attempts table for rate limiting
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            attempt_time REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Failed login attempts table for account lockout
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS failed_login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            attempt_time REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_email_time ON failed_login_attempts (email, attempt_time)"
    )

    # Session revocations table for invalidating sessions after password change
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS session_revocations (
            user_id INTEGER NOT NULL,
            revoked_at REAL NOT NULL,
            reason TEXT,
            PRIMARY KEY (user_id)
        )
    """
    )

    # Create index for faster lookups
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time
        ON login_attempts(ip_address, attempt_time)
    """
    )

    # Check if admin user exists, if not create one
    cursor.execute("SELECT id FROM users WHERE is_admin = 1")
    admin_exists = cursor.fetchone()

    if not admin_exists:
        # Create default admin user with password from environment variable
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not admin_password:
            # Generate a secure random password if not provided
            import secrets
            import string

            admin_password = "".join(
                secrets.choice(
                    string.ascii_letters + string.digits + string.punctuation
                )
                for _ in range(16)
            )
            print("\n" + "=" * 60)
            print("IMPORTANT: Default admin account created!")
            print(f"Email: admin")
            print(f"Password: {admin_password}")
            print("Please change this password immediately after first login!")
            print("=" * 60 + "\n")

        admin_password_hash = generate_password_hash(admin_password)
        cursor.execute(
            """
            INSERT INTO users (username, name, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        """,
            ("admin", "Administrator", "admin", admin_password_hash, True),
        )

        admin_id = cursor.lastrowid

        # Create stocks record for admin
        cursor.execute(
            """
            INSERT INTO stocks (user_id, stock_count, notes)
            VALUES (?, ?, ?)
        """,
            (admin_id, 0, "Administrator account"),
        )

    # Check if company info exists, if not create default
    cursor.execute("SELECT id FROM company_info")
    company_exists = cursor.fetchone()

    if not company_exists:
        cursor.execute(
            """
            INSERT INTO company_info (total_stocks, company_name)
            VALUES (?, ?)
        """,
            (1000000, Config.COMPANY_NAME),
        )

    conn.commit()
    conn.close()


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class User:
    def __init__(self, id, name, email, is_admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.is_admin = is_admin
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user_data = conn.execute(
            "SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        conn.close()

        if user_data:
            return User(
                user_data["id"],
                user_data["name"],
                user_data["email"],
                user_data["is_admin"],
            )
        return None

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        user_data = conn.execute(
            "SELECT id, name, email, password_hash, is_admin FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

        if user_data:
            user = User(
                user_data["id"],
                user_data["name"],
                user_data["email"],
                user_data["is_admin"],
            )
            user.password_hash = user_data["password_hash"]
            return user
        return None

    def get_stocks(self):
        """Get user's stock information."""
        conn = get_db_connection()
        stocks_data = conn.execute(
            "SELECT stock_count, last_updated, notes FROM stocks WHERE user_id = ?",
            (self.id,),
        ).fetchone()
        conn.close()

        if stocks_data:
            return {
                "count": stocks_data["stock_count"],
                "last_updated": stocks_data["last_updated"],
                "notes": stocks_data["notes"],
            }
        return {"count": 0, "last_updated": None, "notes": None}

    def get_ownership_percentage(self):
        """Calculate user's ownership percentage."""
        stocks = self.get_stocks()
        total_stocks = get_total_stocks()

        if total_stocks > 0:
            return (stocks["count"] / total_stocks) * 100
        return 0


def get_total_stocks():
    """Get total company stocks."""
    conn = get_db_connection()
    result = conn.execute("SELECT total_stocks FROM company_info LIMIT 1").fetchone()
    conn.close()

    return result["total_stocks"] if result else 0


def get_all_stockholders():
    """Get all stockholders with their stock information (admin only)."""
    conn = get_db_connection()
    result = conn.execute(
        """
        SELECT u.id, u.name, u.email, s.stock_count
        FROM users u
        LEFT JOIN stocks s ON u.id = s.user_id
        WHERE u.is_admin = 0
        ORDER BY u.name
    """
    ).fetchall()
    conn.close()

    return result


def update_user_stocks(user_id, stock_count, notes=None):
    """Update a user's stock count."""
    conn = get_db_connection()

    # Check if stocks record exists
    existing = conn.execute(
        "SELECT id FROM stocks WHERE user_id = ?", (user_id,)
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE stocks
            SET stock_count = ?, notes = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """,
            (stock_count, notes, user_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO stocks (user_id, stock_count, notes)
            VALUES (?, ?, ?)
        """,
            (user_id, stock_count, notes),
        )

    conn.commit()
    conn.close()


def update_user_info(user_id, name, email, stock_count):
    """Update user's complete information including name, email, and stocks."""
    conn = get_db_connection()
    try:
        # Begin transaction to ensure atomic updates
        conn.execute("BEGIN")

        # Update user information
        conn.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ? AND is_admin = 0
        """,
            (name, email, user_id),
        )

        # Update stocks information
        existing = conn.execute(
            "SELECT id FROM stocks WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE stocks
                SET stock_count = ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (stock_count, user_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO stocks (user_id, stock_count)
                VALUES (?, ?)
            """,
                (user_id, stock_count),
            )

        # Commit transaction - both updates succeed together
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username or email already exists - rollback all changes
        conn.rollback()
        return False
    except Exception:
        # Any other error - rollback all changes
        conn.rollback()
        return False
    finally:
        conn.close()


def update_total_stocks(total_stocks):
    """Update total company stocks."""
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE company_info
        SET total_stocks = ?, last_updated = CURRENT_TIMESTAMP
    """,
        (total_stocks,),
    )
    conn.commit()
    conn.close()


def create_user(name, email, password_hash, initial_stocks=0):
    """Create a new user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO users (username, name, email, password_hash)
            VALUES (?, ?, ?, ?)
        """,
            (email, name, email, password_hash),
        )
        user_id = cursor.lastrowid

        # Create stocks record
        conn.execute(
            """
            INSERT INTO stocks (user_id, stock_count)
            VALUES (?, ?)
        """,
            (user_id, initial_stocks),
        )

        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def update_user_password(user_id, new_password_hash):
    """Update a user's password."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
        """,
            (new_password_hash, user_id),
        )

        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()


def delete_user(user_id):
    """Delete a user and their stocks (admin only function)."""
    conn = get_db_connection()
    try:
        # Check if user is admin
        user = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user and user["is_admin"]:
            return False  # Cannot delete admin users

        # Delete stocks first (foreign key)
        conn.execute("DELETE FROM stocks WHERE user_id = ?", (user_id,))

        # Delete user
        cursor = conn.execute(
            "DELETE FROM users WHERE id = ? AND is_admin = 0", (user_id,)
        )

        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()


def record_login_attempt(ip_address):
    """Record a login attempt for rate limiting."""
    import time

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO login_attempts (ip_address, attempt_time)
            VALUES (?, ?)
        """,
            (ip_address, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def check_rate_limit(ip_address, max_attempts=99, window_minutes=5):
    """Check if IP address has exceeded rate limit.

    Returns (is_limited, attempts_count)
    """
    import time

    conn = get_db_connection()
    try:
        window_start = time.time() - (window_minutes * 60)

        # Count recent attempts
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM login_attempts
            WHERE ip_address = ? AND attempt_time > ?
        """,
            (ip_address, window_start),
        )

        count = cursor.fetchone()[0]
        return (count >= max_attempts, count)
    finally:
        conn.close()


def cleanup_old_login_attempts(hours=24):
    """Remove login attempts older than specified hours."""
    import time

    conn = get_db_connection()
    try:
        cutoff_time = time.time() - (hours * 3600)
        conn.execute(
            """
            DELETE FROM login_attempts
            WHERE attempt_time < ?
        """,
            (cutoff_time,),
        )
        conn.commit()
    finally:
        conn.close()


def record_failed_login_attempt(email, ip_address):
    """Record a failed login attempt for a specific email address."""
    import time

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO failed_login_attempts (email, ip_address, attempt_time)
            VALUES (?, ?, ?)
        """,
            (email.lower(), ip_address, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def check_account_lockout(email, max_attempts=5, lockout_minutes=30):
    """Check if account is locked due to too many failed login attempts.

    Returns (is_locked, attempts_remaining, lockout_minutes)
    """
    import time

    conn = get_db_connection()
    try:
        window_start = time.time() - (lockout_minutes * 60)
        cursor = conn.execute(
            """
            SELECT COUNT(*) as attempts
            FROM failed_login_attempts
            WHERE email = ? AND attempt_time > ?
        """,
            (email.lower(), window_start),
        )

        result = cursor.fetchone()
        attempt_count = result[0] if result else 0

        is_locked = attempt_count >= max_attempts
        attempts_remaining = max(0, max_attempts - attempt_count)

        return is_locked, attempts_remaining, lockout_minutes
    finally:
        conn.close()


def clear_failed_login_attempts(email):
    """Clear failed login attempts after successful login."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            DELETE FROM failed_login_attempts
            WHERE email = ?
        """,
            (email.lower(),),
        )
        conn.commit()
    finally:
        conn.close()


def revoke_user_sessions(user_id, reason="password_reset"):
    """Mark all sessions for a user as revoked."""
    import time

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO session_revocations (user_id, revoked_at, reason)
            VALUES (?, ?, ?)
        """,
            (user_id, time.time(), reason),
        )
        conn.commit()
    finally:
        conn.close()


def is_session_revoked(user_id, session_created_at):
    """Check if user's session was revoked after session was created."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT revoked_at FROM session_revocations
            WHERE user_id = ?
        """,
            (user_id,),
        )
        result = cursor.fetchone()

        if result and result[0] > session_created_at:
            return True
        return False
    finally:
        conn.close()
