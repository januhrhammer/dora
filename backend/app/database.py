"""
Database configuration and session management for the medicine tracking app.

This module sets up the SQLite database connection using SQLAlchemy.
It provides the database engine, session maker, and base class for models.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Determine database path based on environment
# In Docker, use /app/data (mounted volume for persistence)
# In local dev, use current directory
data_dir = Path("data")
if data_dir.exists() and data_dir.is_dir():
    # Docker environment with mounted volume
    db_path = "data/medicine.db"
else:
    # Local development
    db_path = "medicine.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_path}"

# Create the SQLite engine
# connect_args={"check_same_thread": False} is needed for SQLite to work with FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal class will be used to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a database session.

    Yields:
        Session: A SQLAlchemy database session.

    The session is automatically closed after the request is complete.
    This is used as a FastAPI dependency to inject database sessions into routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
