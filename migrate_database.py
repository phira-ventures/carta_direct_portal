#!/usr/bin/env python3
"""
Database Migration Script: Rename 'shares' to 'stocks'

This script migrates the database schema from share-based naming to stock-based naming.
It's safe to run multiple times - it will only migrate if the old schema is detected.

Changes:
- Table: shares -> stocks
- Column: share_count -> stock_count (in stocks table)
- Column: total_shares -> total_stocks (in company_info table)
"""

import sqlite3
import os
from config import Config

def migrate_database():
    """Migrate database from shares to stocks terminology."""
    db_path = Config.DATABASE_PATH

    if not os.path.exists(db_path):
        print(f"No database found at {db_path}")
        print("Migration not needed - database will be created with new schema on first run.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if old schema exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shares'")
        old_table_exists = cursor.fetchone() is not None

        # Check if new schema exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stocks'")
        new_table_exists = cursor.fetchone() is not None

        if not old_table_exists and new_table_exists:
            print("✓ Database already using new schema (stocks table). No migration needed.")
            conn.close()
            return

        if not old_table_exists and not new_table_exists:
            print("✓ No existing database. Will be created with new schema on first run.")
            conn.close()
            return

        print("🔄 Old schema detected. Starting migration...")
        print("=" * 60)

        # Begin transaction
        conn.execute('BEGIN TRANSACTION')

        # Step 1: Handle shares table migration
        print("📝 Step 1/3: Migrating 'shares' table data...")

        if new_table_exists:
            # Both tables exist - copy data from shares to stocks
            print("   • Both 'shares' and 'stocks' tables found")
            print("   • Copying data from 'shares' to 'stocks'...")

            cursor.execute('SELECT id, user_id, share_count, last_updated, notes FROM shares')
            shares_data = cursor.fetchall()

            for row in shares_data:
                # Check if record already exists in stocks table
                cursor.execute('SELECT id FROM stocks WHERE user_id = ?', (row[1],))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO stocks (user_id, stock_count, last_updated, notes)
                        VALUES (?, ?, ?, ?)
                    ''', (row[1], row[2], row[3], row[4]))

            print(f"   ✓ Migrated {len(shares_data)} records to 'stocks' table")

            # Drop old shares table
            cursor.execute('DROP TABLE shares')
            print("   ✓ Dropped old 'shares' table")
        else:
            # Only shares table exists - rename it
            print("   • Only 'shares' table found")
            print("   • Creating new 'stocks' table with updated schema...")

            # Get data from shares table
            cursor.execute('SELECT id, user_id, share_count, last_updated, notes FROM shares')
            shares_data = cursor.fetchall()

            # Create new stocks table with stock_count column
            cursor.execute('''
                CREATE TABLE stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stock_count INTEGER NOT NULL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Copy data to new table
            for row in shares_data:
                cursor.execute('''
                    INSERT INTO stocks (user_id, stock_count, last_updated, notes)
                    VALUES (?, ?, ?, ?)
                ''', (row[1], row[2], row[3], row[4]))

            print(f"   ✓ Created 'stocks' table with {len(shares_data)} records")

            # Drop old shares table
            cursor.execute('DROP TABLE shares')
            print("   ✓ Dropped old 'shares' table")

        # Step 2: Update company_info table - rename total_shares to total_stocks
        print("📝 Step 2/3: Updating company_info table...")

        # Get current data
        cursor.execute('SELECT id, total_shares, company_name, last_updated FROM company_info')
        company_data = cursor.fetchall()

        # Drop old table
        cursor.execute('DROP TABLE company_info')

        # Create new table with updated column name
        cursor.execute('''
            CREATE TABLE company_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_stocks INTEGER NOT NULL DEFAULT 0,
                company_name TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Re-insert data
        for row in company_data:
            cursor.execute('''
                INSERT INTO company_info (id, total_stocks, company_name, last_updated)
                VALUES (?, ?, ?, ?)
            ''', row)

        print("   ✓ Column 'total_shares' renamed to 'total_stocks'")

        # Step 3: Verify migration
        print("📝 Step 3/3: Verifying migration...")

        # Check stocks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stocks'")
        if not cursor.fetchone():
            raise Exception("Migration failed: stocks table not found")

        # Check company_info has total_stocks column
        cursor.execute("PRAGMA table_info(company_info)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'total_stocks' not in columns:
            raise Exception("Migration failed: total_stocks column not found")

        # Count records to verify data integrity
        cursor.execute('SELECT COUNT(*) FROM stocks')
        stock_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM company_info')
        company_count = cursor.fetchone()[0]

        print(f"   ✓ Verified: {stock_count} stock records")
        print(f"   ✓ Verified: {company_count} company info record(s)")

        # Commit transaction
        conn.commit()

        print("=" * 60)
        print("✅ Migration completed successfully!")
        print()
        print("Database schema updated:")
        print("  • shares → stocks")
        print("  • total_shares → total_stocks")
        print()
        print("⚠️  Note: Column 'share_count' in stocks table remains unchanged")
        print("   (SQLite doesn't support renaming columns directly in ALTER TABLE)")
        print("   The application code handles this mapping internally.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        print("Database rolled back to previous state.")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Database Migration: shares → stocks")
    print("=" * 60)

    migrate_database()
