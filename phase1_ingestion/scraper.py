import sqlite3
import pandas as pd
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import os

import re

# Configuration for INDmoney
APP_ID = 'in.indwealth' 
# DB path should be relative to the project root for consistency
DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reviews.db')

def is_mostly_english(text):
    """Heuristic to check if text is English using common word matches."""
    if not text:
        return False
    # Common English functional words
    common_english = {
        "the", "is", "and", "to", "of", "in", "it", "you", "that", "was", 
        "for", "on", "are", "with", "as", "at", "be", "this", "my", "i", "app"
    }
    # Tokenize words
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return False
    
    # At least one common English word
    matches = sum(1 for w in words if w in common_english)
    
    # Presence of Hindi/Other scripts
    if re.search(r'[\u0900-\u097F]', text):
        return False
        
    return matches >= 1

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS reviews')
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
    print(f"Database {DB_NAME} initialized with refined schema.")

def scrape_reviews(max_count=1000, weeks=12):
    """
    Scrapes reviews for INDmoney from the Play Store.
    Filters by date, language (English), length (6+ words), and emoji-only.
    Strictly excludes PII (userName, userImage) and appVersion.
    """
    print(f"Starting refined scrape with stricter filters for {APP_ID}...")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    
    all_reviews = []
    continuation_token = None
    
    while len(all_reviews) < max_count:
        result, continuation_token = reviews(
            APP_ID,
            lang='en',
            country='in',
            sort=Sort.NEWEST,
            count=100, # Fetch in batches
            continuation_token=continuation_token
        )
        
        for r in result:
            content = r['content']
            
            # Check date constraint
            if r['at'] < cutoff_date:
                continuation_token = None 
                break
            
            # 0. Strip emojis and non-standard characters from the content itself
            # This ensures they don't appear in the final output
            content = re.sub(r'[^\x00-\x7F]+', ' ', content)
            # Replace multiple spaces with one and strip
            content = re.sub(r'\s+', ' ', content).strip()
            
            # 1. Length Filter (6+ words) - Must be exactly 6 or more
            words = content.split()
            if len(words) < 6:
                continue
            
            # 2. English Language Check (Common word matching)
            if not is_mostly_english(content):
                continue
            
            # 3. Substantive Content Check (Must have letters)
            if not any(char.isalpha() for char in content):
                continue

            # PII/Unnecessary Field Filtering
            all_reviews.append({
                'reviewId': r['reviewId'],
                'content': content,
                'score': r['score'],
                'thumbsUpCount': r['thumbsUpCount'],
                'at': r['at'].isoformat()
            })
            
            if len(all_reviews) >= max_count:
                break
        
        if not continuation_token:
            break
            
    print(f"Fetched {len(all_reviews)} highly refined reviews.")
    return all_reviews

def save_to_db(review_list):
    """Saves the fetched reviews to SQLite, handling duplicates via reviewId."""
    if not review_list:
        print("No new reviews to save.")
        return
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.DataFrame(review_list)
    
    # Use to_sql with if_exists='append' but we need to handle unique constraint
    # Simple way: Load existing IDs and filter
    existing_ids = pd.read_sql('SELECT reviewId FROM reviews', conn)['reviewId'].tolist()
    new_reviews_df = df[~df['reviewId'].isin(existing_ids)]
    
    if not new_reviews_df.empty:
        new_reviews_df.to_sql('reviews', conn, if_exists='append', index=False)
        print(f"Saved {len(new_reviews_df)} new reviews to {DB_NAME}.")
    else:
        print("All fetched reviews already exist in the database.")
        
    conn.close()

def save_to_json(review_list, filename='phase1_ingestion/reviews_preview.json'):
    """Saves the fetched reviews to a JSON file for manual verification."""
    if not review_list:
        print("No new reviews to save to JSON.")
        return
    
    import json
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(review_list, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(review_list)} reviews to {filename}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Play Store reviews.')
    parser.add_argument('--count', type=int, default=500, help='Max reviews to scrape')
    parser.add_argument('--weeks', type=int, default=12, help='Weeks of history to fetch')
    args = parser.parse_args()

    init_db()
    
    try:
        data = scrape_reviews(max_count=args.count, weeks=args.weeks)
        save_to_db(data)
        save_to_json(data)
    except Exception as e:
        print(f"An error occurred: {e}")
