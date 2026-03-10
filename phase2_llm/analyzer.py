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

class ReviewAnalyzer:
    def __init__(self):
        Config.validate()
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.db_path = Config.DB_NAME
        self.themes = []

    def get_reviews_from_db(self):
        """Fetches all reviews from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT reviewId, content, score FROM reviews")
        rows = cursor.fetchall()
        conn.close()
        return [{"reviewId": r[0], "content": r[1], "score": r[2]} for r in rows]

    def discover_themes(self, sample_reviews):
        """Uses a subset of reviews to discover 3-5 high-level themes."""
        print("Discovering themes from sample...")
        
        reviews_text = "\n".join([f"- {r['content']}" for r in sample_reviews])
        
        prompt = f"""
        Analyze the following user reviews for the INDmoney app and identify 3-5 high-level recurring themes (e.g., 'UI/UX', 'Customer Support', 'Payment Issues', 'Feature Requests').
        
        Return ONLY a JSON list of strings.
        Example: ["Theme 1", "Theme 2", "Theme 3"]
        
        Reviews:
        {reviews_text}
        """
        
        completion = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        response = json.loads(completion.choices[0].message.content)
        self.themes = response.get("themes", []) # Assuming the LLM wraps it in a "themes" key due to json_object mode
        # Fallback if it's just a list or differently keyed
        if not self.themes and isinstance(response, list):
            self.themes = response
        elif not self.themes and isinstance(response, dict):
            # Take the first list found
            for val in response.values():
                if isinstance(val, list):
                    self.themes = val
                    break
        
        print(f"Themes discovered: {self.themes}")
        return self.themes

    def categorize_reviews(self, all_reviews):
        """Categorizes all reviews into the discovered themes in batches."""
        print(f"Categorizing {len(all_reviews)} reviews into themes...")
        categorized_data = {theme: [] for theme in self.themes}
        categorized_data["Other"] = []
        
        batch_size = 50
        for i in range(0, len(all_reviews), batch_size):
            batch = all_reviews[i:i+batch_size]
            reviews_input = "\n".join([f"ID: {r['reviewId']} | {r['content']}" for r in batch])
            
            prompt = f"""
            Categorize each of the following reviews into one of these themes: {', '.join(self.themes)}.
            If it doesn't fit any, use 'Other'.
            
            Return a JSON object where keys are review IDs and values are the theme names.
            Example: {{"id1": "Theme A", "id2": "Theme B"}}
            
            Reviews:
            {reviews_input}
            """
            
            completion = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=4096
            )
            
            mapping = json.loads(completion.choices[0].message.content)
            
            for review in batch:
                theme = mapping.get(review['reviewId'], "Other")
                if theme not in categorized_data:
                    theme = "Other"
                categorized_data[theme].append(review)
            
            print(f"Processed batch {i//batch_size + 1}")
            time.sleep(2) # Small delay to respect rate limits
            
        return categorized_data

    def extract_top_quotes(self, all_reviews):
        """Extracts the top 3 most impactful user quotes along with their ratings."""
        print("Extracting top 3 user quotes with ratings...")
        # Sort by impact (length) and sample top 50
        sample = sorted(all_reviews, key=lambda x: len(x['content']), reverse=True)[:50]
        # Create a mapping for easy lookup later
        sample_map = {r['content'][:100]: r for r in sample} 
        reviews_text = "\n".join([f"- {r['content']}" for r in sample])
        
        prompt = f"""
        From the following set of user reviews, select the TOP 3 most impactful and representative "real user quotes".
        These should highlight major praises or critical pain points.
        
        Return ONLY a JSON list of strings (the exact quotes found in the text).
        Example: ["Quote 1", "Quote 2", "Quote 3"]
        
        Reviews:
        {reviews_text}
        """
        
        completion = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        response = json.loads(completion.choices[0].message.content)
        quote_texts = []
        for val in response.values():
            if isinstance(val, list):
                quote_texts = val[:3]
                break
        
        # Match back to original reviews to get scores
        final_quotes = []
        for text in quote_texts:
            # Find the closest match in sample_map
            match = None
            for s_text, r_obj in sample_map.items():
                if text.strip() in r_obj['content']:
                    match = r_obj
                    break
            
            if match:
                final_quotes.append({
                    "content": match['content'],
                    "score": match['score']
                })
            else:
                # Fallback if text drifted slightly
                final_quotes.append({"content": text, "score": 5})
        
        return final_quotes

    def run_analysis(self):
        """Main execution flow for Phase 2."""
        all_reviews = self.get_reviews_from_db()
        if not all_reviews:
            print("No reviews found in database. Run Phase 1 first.")
            return

        # Step 1: Discover Themes (using a sample of 100)
        sample = all_reviews[:100]
        self.discover_themes(sample)
        
        # Step 2: Categorize all
        categorized = self.categorize_reviews(all_reviews)
        
        # Step 3: Extract Quotes
        quotes = self.extract_top_quotes(all_reviews)
        
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
    from datetime import datetime
    analyzer = ReviewAnalyzer()
    analyzer.run_analysis()
