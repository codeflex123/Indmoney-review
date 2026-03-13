from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import os
import subprocess
import sys
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

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reviews.db"))
ANALYSIS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "phase2_llm", "analysis_results.json"))

@app.get("/api/reviews")
async def get_reviews(limit: int = 100):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews ORDER BY at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
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
        # Run the script in the background
        process = subprocess.Popen(
            command,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return {"status": "started", "phase": phase, "pid": process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
