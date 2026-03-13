import sqlite3
import os
from config import Config

def get_db_connection():
    """Returns a connection to the database (Postgres or SQLite)."""
    if Config.DATABASE_URL:
        # For Postgres, we use psycopg2
        import psycopg2
        return psycopg2.connect(Config.DATABASE_URL)
    
    # Fallback to local SQLite
    return sqlite3.connect(Config.DB_NAME)

def init_db():
    """Initializes the database schema for both SQLite and Postgres."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if Config.DATABASE_URL:
        # Postgres Schema (Snake Case)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT PRIMARY KEY,
                content TEXT,
                score INTEGER,
                thumbs_up_count INTEGER,
                at TIMESTAMP
            )
        ''')
    else:
        # SQLite Schema (Camel Case)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                reviewId TEXT PRIMARY KEY,
                content TEXT,
                score INTEGER,
                thumbsUpCount INTEGER,
                at DATETIME
            )
        ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
