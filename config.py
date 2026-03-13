import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_NAME = os.path.join(os.path.dirname(__file__), "reviews.db")
    
    # LLM Settings
    MODEL_NAME = "llama-3.1-8b-instant" # Switched to 8B for higher rate limits and speed
    GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"
    
    # Email Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
    
    @staticmethod
    def validate():
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")
        if not Config.SMTP_USER or not Config.SMTP_PASS or not Config.RECIPIENT_EMAIL:
            print("WARNING: Email settings (SMTP_USER/PASS/RECIPIENT_EMAIL) missing. Email delivery will fail.")
