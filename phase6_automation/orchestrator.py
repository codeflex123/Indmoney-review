import time
import subprocess
import os
import sys
from datetime import datetime
import pytz
import logging

# Add the project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Setup logging to a separate file
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scheduler.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def run_pipeline():
    logging.info("🚀 Starting Automated Review Audit Pipeline...")
    
    steps = [
        ["python3", "phase1_ingestion/scraper.py", "--count", "500", "--weeks", "12"],
        ["python3", "phase2_llm/analyzer.py"],
        ["python3", "phase3_insights/pulsar.py"],
        ["python3", "phase4_delivery/mailer.py", Config.RECIPIENT_EMAIL]
    ]
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for cmd in steps:
        logging.info(f"Running: {' '.join(cmd)}")
        try:
            # Run the command and capture output line by line
            process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output to logging
            if process.stdout:
                for line in process.stdout:
                    logging.info(f"[{cmd[1].split('/')[1] if '/' in cmd[1] else cmd[1]}] {line.strip()}")
            
            process.wait()
            if process.returncode != 0:
                logging.error(f"❌ Step Failed: {cmd[1]} with return code {process.returncode}")
                return False
            
            logging.info(f"✅ Step Success: {cmd[1]}")
        except Exception as e:
            logging.error(f"❌ Unexpected Error in {cmd[1]}: {str(e)}")
            return False
            
    logging.info("✨ Full Pipeline Completed Successfully!")
    return True

def main():
    if "--now" in sys.argv:
        run_pipeline()
        return

    logging.info("🕰 Orchestrator started. Mode: Weekly (Tuesday 15:50 IST)")
    
    ist = pytz.timezone('Asia/Kolkata')
    last_trigger_minute = -1
    
    while True:
        now_ist = datetime.now(ist)
        current_minute = now_ist.minute
        
        # Trigger every Tuesday at 15:50 IST
        # Weekday 1 is Tuesday (0=Monday, 1=Tuesday...)
        if now_ist.weekday() == 1 and now_ist.hour == 15 and now_ist.minute == 50 and current_minute != last_trigger_minute:
            logging.info(f"⚡ Weekly Schedule triggered at {now_ist.strftime('%H:%M')} IST")
            success = run_pipeline()
            if not success:
                logging.error("Pipeline failed during scheduled run.")
            last_trigger_minute = current_minute
            
        time.sleep(10) # Check every 10 seconds for higher precision

if __name__ == "__main__":
    main()
