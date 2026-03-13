import json
import os
import sys
from datetime import datetime

# Add the project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from config import Config

class Pulsar:
    def __init__(self):
        Config.validate()
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)
        self.analysis_file = os.path.join("phase2_llm", "analysis_results.json")
        self.output_file = "weekly_pulse.md"

    def load_analysis(self):
        """Loads the analysis results from Phase 2."""
        if not os.path.exists(self.analysis_file):
            raise FileNotFoundError(f"Analysis file not found: {self.analysis_file}. Run Phase 2 first.")
        
        with open(self.analysis_file, 'r') as f:
            return json.load(f)

    def generate_action_ideas(self, themes, categorization):
        """Uses Groq to generate 3 strategic action ideas based on themes and volume."""
        print("Generating strategic action ideas...")
        
        # Prepare theme context
        theme_context = "\n".join([f"- {theme}: {count} reviews" for theme, count in categorization.items()])
        
        prompt = f"""
        Based on the following themes and review counts for the INDmoney app, suggest 3 high-impact, strategic action ideas for the product and leadership teams.
        
        Themes & Volume:
        {theme_context}
        
        Focus on identifying the most pressing issues or significant opportunities for improvement.
        Return ONLY a JSON list of 3 strings.
        Example: ["Action 1", "Action 2", "Action 3"]
        """
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )
        
        response_text = response.text
        response_json = json.loads(response.text)
        
        # Extract list from potential wrapper or direct list
        actions = []
        if isinstance(response_json, list):
            actions = response_json[:3]
        elif isinstance(response_json, dict):
            for val in response_json.values():
                if isinstance(val, list):
                    actions = val[:3]
                    break
            
        return actions
            
        return actions

    def assemble_report(self, analysis, actions):
        """Assembles the final Markdown report."""
        print(f"Assembling report to {self.output_file}...")
        
        themes = analysis['themes']
        categorization = analysis['categorized_reviews']
        quotes = analysis['top_quotes']
        
        # Sort themes by volume for the report
        sorted_themes = sorted(categorization.items(), key=lambda x: x[1], reverse=True)
        # Exclude 'Other' and take top 3
        top_themes = [t for t in sorted_themes if t[0] != 'Other'][:3]
        
        # Prepare fragments for the report
        themes_md = "\n".join([f"1. **{t[0]}** ({t[1]} reviews)" for t in top_themes])
        
        def get_stars(score):
            return "⭐" * int(score)
            
        quotes_md = "\n".join([f"> {get_stars(q.get('score', 5))}\n> \"{q.get('content')}\"" for q in quotes])
        actions_md = "\n".join([f"- {a}" for a in actions])
        
        report_content = f"""# INDmoney Weekly Pulse ⚡
**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Reviews Analyzed**: {sum(categorization.values())}

---

## 🔝 Top 3 Feedback Themes
{themes_md}

---

## 💬 Voice of the User
{quotes_md}

---

## 🚀 AI-Generated Strategic Actions
{actions_md}

---
*This report was automatically generated using INDmoney Review Analysis System.*
"""
        
        with open(self.output_file, 'w') as f:
            f.write(report_content)
        
        return self.output_file

    def run(self):
        """Main execution flow for Phase 3."""
        try:
            analysis = self.load_analysis()
            actions = self.generate_action_ideas(analysis['themes'], analysis['categorized_reviews'])
            report_path = self.assemble_report(analysis, actions)
            print(f"Phase 3 Complete! Report generated at: {report_path}")
            return report_path
        except Exception as e:
            print(f"An error occurred in Phase 3: {e}")
            return None

if __name__ == "__main__":
    pulsar = Pulsar()
    pulsar.run()
