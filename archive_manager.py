import os
import shutil
import json
from datetime import datetime

HISTORY_DIR = "history"
REPORTS_DIR = "reports"

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def init_dirs():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

def archive_daily_data(file_paths):
    """
    Archive the given list of files to history/YYYY-MM-DD/
    """
    today = get_today_str()
    target_dir = os.path.join(HISTORY_DIR, today)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    for file_path in file_paths:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            shutil.copy2(file_path, os.path.join(target_dir, filename))
            # print(f"📚 Archived {filename} to {target_dir}")

def save_report(category, content):
    """
    Save the strategy report to reports/YYYY-MM-DD/{category}_strategy.md
    Also save a latest copy to reports/{category}_strategy.md for easy frontend access
    """
    today = get_today_str()
    
    # 1. Save to History
    history_report_dir = os.path.join(HISTORY_DIR, today, "reports")
    if not os.path.exists(history_report_dir):
        os.makedirs(history_report_dir)
        
    filename = f"{category}_strategy.md"
    
    with open(os.path.join(history_report_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)
        
    # 2. Save to Latest (Root/reports for frontend)
    # We might want to save it in the root or a static folder for the frontend to read easily.
    # The user's index.html reads analysis_*.json from root. 
    # Let's save the MD files in root/reports/ maybe? 
    # Or just root/strategy_{category}.md to keep it simple for the frontend.
    
    latest_path = f"strategy_{category}.md" # Root directory for easy access
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return latest_path

def get_available_dates():
    """
    Return a list of available dates in history
    """
    if not os.path.exists(HISTORY_DIR):
        return []
    dates = [d for d in os.listdir(HISTORY_DIR) if os.path.isdir(os.path.join(HISTORY_DIR, d))]
    return sorted(dates, reverse=True)

def update_history_index():
    """
    Generate a history_index.json file in the root directory for frontend to consume.
    """
    dates = get_available_dates()
    index_data = {
        "dates": dates,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("history_index.json", "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    # print(f"📅 Updated history_index.json with {len(dates)} dates.")
