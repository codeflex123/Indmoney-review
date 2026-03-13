import os
import re
import sys
import pandas as pd
from db import get_db_engine, get_db_connection
from config import Config

def clean_pii(text):
    """Redacts PII (Emails, Phones, specific headers) from text."""
    if not text:
        return text
    
    # 1. Redact Emails
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
    
    # 2. Redact Phone Numbers
    text = re.sub(r'\+?\d{2,3}[\s-]?\d{4,5}[\s-]?\d{4,5}', '[PHONE]', text)
    
    # 3. Strip "Name Date Time" headers
    text = re.sub(r'^[A-Za-z\s]{3,}\d{2} [A-Za-z]{3} \d{4},? \d{2}:\d{2} [AP]M:?', '', text).strip()
    
    return text

def run_cleanup():
    print("Starting database PII cleanup...")
    engine = get_db_engine()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    col_id = "review_id" if Config.DATABASE_URL else "reviewId"
    
    try:
        # Fetch all reviews
        cursor.execute(f"SELECT {col_id}, content FROM reviews")
        rows = cursor.fetchall()
        
        count = 0
        for rid, content in rows:
            cleaned = clean_pii(content)
            if cleaned != content:
                cursor.execute(f"UPDATE reviews SET content = %s WHERE {col_id} = %s" if Config.DATABASE_URL else f"UPDATE reviews SET content = ? WHERE {col_id} = ?", (cleaned, rid))
                count += 1
        
        conn.commit()
        print(f"Cleanup finished. Updated {count} reviews.")
        return count
    except Exception as e:
        print(f"Cleanup error: {e}")
        return 0
    finally:
        conn.close()

if __name__ == "__main__":
    run_cleanup()
