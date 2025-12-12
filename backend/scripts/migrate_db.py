#!/usr/bin/env python3
"""
Database migration script.

This script adds missing columns to the database schema without losing data.
Run this if you encounter "no such column" errors.
"""

import sqlite3
from pathlib import Path
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


def migrate_database():
    """Add missing columns to database tables."""
    db_path = settings.data_dir / "cybersec.db"

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("   Run the application first to create the database.")
        return False

    print(f"🔍 Checking database at {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrations_applied = 0

    try:
        # Check if devices table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='devices'
        """)

        if not cursor.fetchone():
            print("ℹ️  Devices table doesn't exist yet - will be created on next run")
            return True

        # Get current columns in devices table
        cursor.execute("PRAGMA table_info(devices)")
        columns = {row[1] for row in cursor.fetchall()}

        print(f"   Found {len(columns)} columns in devices table")

        # Check for vulnerability_count column
        if 'vulnerability_count' not in columns:
            print("   Adding vulnerability_count column...")
            cursor.execute("""
                ALTER TABLE devices
                ADD COLUMN vulnerability_count INTEGER DEFAULT 0
            """)
            migrations_applied += 1
            print("   ✅ Added vulnerability_count column")
        else:
            print("   ✓ vulnerability_count column exists")

        # Commit changes
        if migrations_applied > 0:
            conn.commit()
            print(f"\n✅ Applied {migrations_applied} migration(s)")
        else:
            print("\n✅ Database schema is up to date")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def recreate_database():
    """
    Recreate the database from scratch.

    WARNING: This will delete all existing data!
    """
    db_path = settings.data_dir / "cybersec.db"

    if db_path.exists():
        print(f"⚠️  This will delete the existing database at {db_path}")
        response = input("   Are you sure? Type 'yes' to confirm: ")

        if response.lower() != 'yes':
            print("   Cancelled.")
            return False

        print("   Deleting old database...")
        db_path.unlink()
        print("   ✅ Old database deleted")

    print("   Creating new database with latest schema...")
    from app.db.init_db import init_db
    init_db()
    print("   ✅ Database created")

    print("\n   Loading seed data...")
    from app.db.seed_data import seed_database
    seed_database()
    print("   ✅ Seed data loaded")

    print("\n✅ Database recreated successfully")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the database from scratch (WARNING: deletes all data)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Database Migration Tool")
    print("=" * 60)
    print()

    if args.recreate:
        success = recreate_database()
    else:
        success = migrate_database()

    print()
    print("=" * 60)

    sys.exit(0 if success else 1)
