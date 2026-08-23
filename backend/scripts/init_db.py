"""
Database initialization script for Deadlock.
Creates all SQLAlchemy tables defined in the application models.
"""
import sys
import os

# Add backend directory to Python path if executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all models are registered with Base metadata


def init_db():
    print(f"[*] Initializing database connection...")
    try:
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), version();"))
            row = result.fetchone()
            db_name = row[0] if row else "unknown"
            db_version = row[1] if row else "unknown"
            print(f"[+] Connected successfully to PostgreSQL database: '{db_name}'")
            print(f"[i] PostgreSQL Version: {db_version}")

        # Create all tables
        print("[*] Creating database tables if they do not exist...")
        Base.metadata.create_all(bind=engine)
        
        table_names = list(Base.metadata.tables.keys())
        print(f"[+] Successfully initialized tables ({len(table_names)}): {', '.join(table_names)}")
        print("[+] Deadlock database layer is ready.")

    except Exception as exc:
        print(f"[-] Database initialization failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    init_db()
