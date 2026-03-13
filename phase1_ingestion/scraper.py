import sqlite3
import pandas as pd
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import os
import re

# Add sys path to import config and db
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from db import get_db_connection, init_db

def scrape_reviews(max_count=1000, weeks=12, stop_at_existing=True):
    """Scrapes reviews for INDmoney from the Play Store."""
    print(f"Starting refined scrape for {APP_ID}...")
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    
    existing_ids = set()
    if stop_at_existing:
        try:
            conn = get_db_connection()
            col = "review_id" if Config.DATABASE_URL else "reviewId"
            existing_ids = set(pd.read_sql(f"SELECT {col} FROM reviews", conn)[col].tolist())
            conn.close()
        except Exception as e:
            print(f"Note: Could not fetch existing IDs: {e}")
    """Heuristic to check if text is English using common word matches."""
    if not text:
        return False
    common_english = {
        "the", "is", "and", "to", "of", "in", "it", "you", "that", "was", 
        "for", "on", "are", "with", "as", "at", "be", "this", "my", "i", "app"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return False
    matches = sum(1 for w in words if w in common_english)
    if re.search(r'[\u0900-\u097F]', text): # Check for common Indian language Unicode range
        return False
    return matches >= 1

def init_db():
    """Initializes the SQLite database."""
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
    print(f"Database {DB_NAME} initialized.")

def scrape_reviews(max_count=1000, weeks=12, stop_at_existing=True):
    """Scrapes reviews for INDmoney from the Play Store."""
    print(f"Starting refined scrape for {APP_ID}...")
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    
    existing_ids = set()
    if stop_at_existing:
        try:
            conn = sqlite3.connect(DB_NAME)
            existing_ids = set(pd.read_sql('SELECT reviewId FROM reviews', conn)['reviewId'].tolist())
            conn.close()
        except Exception as e:
            print(f"Note: Could not fetch existing IDs: {e}")

    all_reviews = []
    continuation_token = None
    
    while len(all_reviews) < max_count:
        result, continuation_token = reviews(
            APP_ID, lang='en', country='in', sort=Sort.NEWEST, count=100, continuation_token=continuation_token
        )
        
        stop_signal = False
        for r in result:
            if stop_at_existing and r['reviewId'] in existing_ids:
                print(f"Reached existing review. Stopping scrape.")
                stop_signal = True
                break
            if r['at'] < cutoff_date:
                stop_signal = True
                break
            
            content = re.sub(r'[^\x00-\x7F]+', ' ', r['content'])
            content = re.sub(r'\s+', ' ', content).strip()
            
            if len(content.split()) < 6 or not is_mostly_english(content):
                continue

            all_reviews.append({
                'reviewId': r['reviewId'],
                'content': content,
                'score': r['score'],
                'thumbsUpCount': r['thumbsUpCount'],
                'at': r['at'].isoformat()
            })
            if len(all_reviews) >= max_count:
                stop_signal = True
                break
        if stop_signal or not continuation_token:
            break
            
    print(f"Fetched {len(all_reviews)} refined reviews.")
    return all_reviews

def save_to_db(review_list):
    """Saves the fetched reviews to the database."""
    if not review_list: return
    conn = get_db_connection()
    df = pd.DataFrame(review_list)
    
    col = "review_id" if Config.DATABASE_URL else "reviewId"
    try:
        existing_ids = pd.read_sql(f"SELECT {col} FROM reviews", conn)[col].tolist()
    except:
        existing_ids = []
        
    new_reviews_df = df[~df['reviewId'].isin(existing_ids)]
    if not new_reviews_df.empty:
        if Config.DATABASE_URL:
            pg_df = new_reviews_df.rename(columns={
                'reviewId': 'review_id',
                'thumbsUpCount': 'thumbs_up_count'
            })
            pg_df.to_sql('reviews', conn, if_exists='append', index=False)
        else:
            sl_df = new_reviews_df.copy()
            sl_df['at'] = sl_df['at'].map(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
            sl_df.to_sql('reviews', conn, if_exists='append', index=False)
        print(f"Saved {len(new_reviews_df)} new reviews.")
    conn.close()

def save_to_json(review_list, filename='phase1_ingestion/reviews_preview.json'):
    """Saves the fetched reviews to a JSON file."""
    if not review_list: return
    import json
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(review_list, f, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=500)
    parser.add_argument('--weeks', type=int, default=12)
    args = parser.parse_args()
    init_db()
    data = scrape_reviews(max_count=args.count, weeks=args.weeks)
    save_to_db(data)
    save_to_json(data)
