import time
import subprocess
import os
import sys
from datetime import datetime
import pytz

# Add the project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Configuration
SCHEDULE_TIME = "15:55"
SCHEDULE_DAY = 1 # 0=Monday, 1=Tuesday, ...

def run_pipeline():
    print(f"\n[{datetime.now()}] 🚀 Starting Automated Weekly Review Audit...")
    
    steps = [
        ["python3", "phase1_ingestion/scraper.py", "--count", "500", "--weeks", "12"],
        ["python3", "phase2_llm/analyzer.py"],
        ["python3", "phase3_insights/pulsar.py"],
        ["python3", "phase4_delivery/mailer.py", Config.RECIPIENT_EMAIL]
    ]
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for cmd in steps:
        print(f"[{datetime.now()}] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, 
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"[{datetime.now()}] ✅ Step Success: {cmd[1]}")
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.now()}] ❌ Step Failed: {cmd[1]}")
            print(f"Error: {e.stderr}")
            return False
            
    print(f"[{datetime.now()}] ✨ Full Pipeline Completed Successfully!")
    return True

def main():
    if "--now" in sys.argv:
        run_pipeline()
        return

    print(f"[{datetime.now()}] 🕰 Orchestrator started. Waiting for Tuesday {SCHEDULE_TIME} IST...")
    
    ist = pytz.timezone('Asia/Kolkata')
    
    while True:
        now_ist = datetime.now(ist)
        # check if today is Tuesday (1) and time matches 15:55
        if now_ist.weekday() == SCHEDULE_DAY and now_ist.strftime("%H:%M") == SCHEDULE_TIME:
            print(f"[{now_ist}] ⚡ Schedule triggered!")
            run_pipeline()
            # Wait a minute so we don't trigger multiple times in the same minute
            time.sleep(61)
            
        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    main()
