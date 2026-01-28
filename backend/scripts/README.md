# Backend Maintenance Scripts

This directory contains utility scripts for database maintenance and other backend tasks.

## Database Migration (`migrate_db.py`)

Script to check and update the database schema without losing data.

### Usage

**Check and migrate database:**
```bash
cd backend
source .venv/bin/activate
python scripts/migrate_db.py
```

This will:
- Check if all required columns exist
- Add any missing columns with safe defaults
- Preserve all existing data
- Report what changes were made

**Recreate database from scratch:**
```bash
python scripts/migrate_db.py --recreate
```

⚠️ **WARNING**: This deletes all existing data and creates a fresh database with seed data.

### When to Use

Run the migration script if you encounter errors like:
- `no such column: devices.vulnerability_count`
- `no such table: <table_name>`
- Other SQLAlchemy schema errors

This typically happens when:
- You pulled code with new database columns
- The database schema is out of sync with the models
- You're setting up the project for the first time

### What It Does

The script safely adds missing columns to existing tables:
- `devices.vulnerability_count` - Count of vulnerabilities per device

Future migrations will be added here as the schema evolves.

## Other Scripts

Additional maintenance scripts will be added to this directory as needed.
