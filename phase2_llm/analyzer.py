import sys
import os

# Add the project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
import re
import time
from groq import Groq
from config import Config
from datetime import datetime

import logging

class ReviewAnalyzer:
    def __init__(self):
        Config.validate()
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.db_path = Config.DB_NAME
        self.themes = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    def get_reviews_from_db(self):
        """Fetches all reviews from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT reviewId, content, score FROM reviews")
        rows = cursor.fetchall()
        conn.close()
        return [{"reviewId": r[0], "content": r[1], "score": r[2]} for r in rows]

    def master_analysis(self, sample_reviews):
        """Discovers themes and extracts top quotes in a single request."""
        logging.info("Running Master Analysis (Themes + Quotes)...")
        
        reviews_text = "\n".join([f"- {r['content']}" for r in sample_reviews])
        
        prompt = f"""
        Analyze the following user reviews for the INDmoney app.
        1. Identify 3-5 high-level recurring themes.
        2. Select the TOP 3 most impactful and representative "real user quotes" from the text.
        
        Return a JSON object with:
        - "themes": a list of strings
        - "quotes": a list of strings (exact text from the reviews)
        
        Reviews:
        {reviews_text}
        """
        
        completion = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=45
        )
        
        data = json.loads(completion.choices[0].message.content)
        self.themes = data.get("themes", [])
        quote_texts = data.get("quotes", [])
        
        logging.info(f"Themes discovered: {self.themes}")
        logging.info(f"Quotes extracted: {len(quote_texts)}")
        
        # Match quotes back to original reviews to get scores
        final_quotes = []
        sample_map = {r['content'][:100]: r for r in sample_reviews}
        for text in quote_texts:
            match = None
            for s_text, r_obj in sample_map.items():
                if text.strip() in r_obj['content']:
                    match = r_obj
                    break
            
            if match:
                final_quotes.append({"content": match['content'], "score": match['score']})
            else:
                final_quotes.append({"content": text, "score": 5})
                
        return self.themes, final_quotes

    def categorize_reviews(self, all_reviews):
        """Categorizes all reviews into the discovered themes in batches."""
        print(f"Categorizing {len(all_reviews)} reviews into themes...")
        categorized_data = {theme: [] for theme in self.themes}
        categorized_data["Other"] = []
        
        batch_size = 50
        for i in range(0, len(all_reviews), batch_size):
            batch = all_reviews[i:i+batch_size]
            reviews_input = "\n".join([f"ID: {r['reviewId']} | {r['content']}" for r in batch])
            
            logging.info(f"Categorizing batch {i//batch_size + 1} (Size: {len(batch)})...")
            
            prompt = f"""
            Categorize each review into one of the following themes: {', '.join(self.themes)} or 'Other'.
            You must return a valid JSON object where keys are the review IDs and values are the theme names.
            
            Format:
            {{
                "id_1": "Theme A",
                "id_2": "Other"
            }}
            
            Reviews:
            {reviews_input}
            """
            
            max_retries = 3
            mapping = {}
            for attempt in range(max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=Config.MODEL_NAME,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        max_tokens=4096,
                        timeout=60
                    )
                    mapping = json.loads(completion.choices[0].message.content)
                    break 
                except Exception as e:
                    logging.warning(f"Attempt {attempt + 1} failed for batch categorization: {str(e)}")
                    if attempt == max_retries - 1:
                        logging.error("Max retries reached for batch categorization. Skipping batch.")
                    else:
                        time.sleep(10) # Wait before retry
            
            for review in batch:
                theme = mapping.get(review['reviewId'], "Other")
                if theme not in categorized_data:
                    theme = "Other"
                categorized_data[theme].append(review)
            
            time.sleep(2) # Reduced delay as retries handle 429s eventually
            
        return categorized_data


    def run_analysis(self):
        """Main execution flow for Phase 2."""
        all_reviews = self.get_reviews_from_db()
        if not all_reviews:
            print("No reviews found in database. Run Phase 1 first.")
            return

        # Step 1: Master Analysis (Themes + Quotes)
        sample = sorted(all_reviews, key=lambda x: len(x['content']), reverse=True)[:50]
        themes, quotes = self.master_analysis(sample)
        
        # Step 2: Categorize all
        categorized = self.categorize_reviews(all_reviews)
        
        # Save results
        results = {
            "themes": self.themes,
            "categorized_reviews": {t: len(reviews) for t, reviews in categorized.items()},
            "top_quotes": quotes,
            "timestamp": datetime.now().isoformat()
        }
        
        output_file = "phase2_llm/analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"Analysis complete. Results saved to {output_file}")
        return results

if __name__ == "__main__":
    analyzer = ReviewAnalyzer()
    analyzer.run_analysis()
