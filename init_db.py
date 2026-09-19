"""
Standalone database initializer for Prepify AI.
Run this once before starting the app for the first time:

    python init_db.py
"""
from app import init_db, DB_PATH

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
