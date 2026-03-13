from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

app = FastAPI(title="INDmoney Review Analytics API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "INDmoney Review Analytics API is running", "endpoints": ["/api/reviews", "/api/analysis"]}

from db import get_db_connection, init_db
from config import Config

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("Database initialized on startup.")
    except Exception as e:
        print(f"Error initializing database on startup: {e}")

DB_PATH = Config.DB_NAME
ANALYSIS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "phase2_llm", "analysis_results.json"))

@app.get("/api/reviews")
async def get_reviews(limit: int = 100):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine column name for 'at'
        at_col = "at" 
        
        cursor.execute(f"SELECT * FROM reviews ORDER BY {at_col} DESC LIMIT {limit}")
        
        # Standardize rows
        if Config.DATABASE_URL:
            # Postgres returns tuples/named tuples depending on driver
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            result = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                result.append({
                    "reviewId": row_dict.get("review_id"),
                    "content": row_dict.get("content"),
                    "score": row_dict.get("score"),
                    "thumbsUpCount": row_dict.get("thumbs_up_count"),
                    "at": row_dict.get("at")
                })
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM reviews ORDER BY at DESC LIMIT {limit}")
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis")
async def get_analysis():
    if not os.path.exists(ANALYSIS_PATH):
        return {"error": "Analysis results not found. Please trigger analysis first."}
    try:
        with open(ANALYSIS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preview")
async def get_preview():
    preview_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "weekly_pulse.md"))
    if not os.path.exists(preview_path):
        return {"content": "Preview not available. Please run analysis first."}
    try:
        with open(preview_path, "r") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trigger/{phase}")
async def trigger_phase(phase: str, email: str = None, weeks: int = 12, limit: int = 500):
    scripts = {
        "scrape": ["python3", "phase1_ingestion/scraper.py"],
        "analyze": ["python3", "phase2_llm/analyzer.py"],
        "pulsar": ["python3", "phase3_insights/pulsar.py"],
        "email": ["python3", "phase4_delivery/mailer.py"]
    }
    
    if phase not in scripts:
        raise HTTPException(status_code=400, detail="Invalid phase")
    
    command = list(scripts[phase]) # Ensure it's a list to append
    
    if phase == "scrape":
        command.extend(["--count", str(limit), "--weeks", str(weeks)])
    elif phase == "email" and email:
        command.append(email)
    
    try:
        # Run the script in the background and redirect output to a log file in /tmp
        log_file = f"/tmp/{phase}.log"
        with open(log_file, "w") as f:
            process = subprocess.Popen(
                command,
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                stdout=f,
                stderr=subprocess.STDOUT
            )
        return {"status": "started", "phase": phase, "pid": process.pid, "log": f"/api/logs/{phase}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/{phase}")
async def get_logs(phase: str):
    log_file = f"/tmp/{phase}.log"
    if not os.path.exists(log_file):
        return {"error": "Log file not found"}
    with open(log_file, "r") as f:
        return {"logs": f.read()}

@app.get("/api/ping")
async def ping():
    return {"status": "pong", "version": "pii_redact_v1", "timestamp": datetime.now().isoformat()}

@app.get("/api/admin/cleanup-pii")
def cleanup_pii_db():
    from cleanup_pii import run_cleanup
    count = run_cleanup()
    return {"status": "success", "updated_count": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
