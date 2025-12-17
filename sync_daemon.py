import time
import json
import logging
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# Project Modules
from drive_scanner import scan_review_folder
from sheets_db import upsert_documents, get_all_documents

# --- Configuration & Logging ---
CONFIG_FILE = 'config.json'

# Configure Logging (Timestamped logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sync.log"), # Save to file
        logging.StreamHandler(sys.stdout) # Print to terminal
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def map_sheet_row_to_doc_dict(row):
    """
    Helper: Converts a Google Sheet row (DataFrame dict) back 
    to the format expected by upsert_documents.
    """
    return {
        'topic': row.get('Document Name', 'Unknown'),
        'architect': row.get('Owner', 'Unknown'),
        'link': row.get('Google Doc Link', ''),
        'modified_time': row.get('Last Modified', ''),
        'created_time': row.get('Created Date', ''),
        'last_editor': 'Unknown', # Metadata lost if file deleted
        'status_override': 'Archived' # Flag to force status update
    }

def sync_job():
    """
    Main Logic: Scans Drive, checks Sheets, merges data, and updates DB.
    """
    logger.info("--- Starting Sync Job ---")
    
    try:
        # 1. Scan Google Drive (Source of Truth)
        drive_docs = scan_review_folder()
        drive_links = {d['link'] for d in drive_docs} # Set for fast lookup
        
        logger.info(f"Scanned Drive: Found {len(drive_docs)} active documents.")

        # 2. Fetch Existing Sheets Data (To catch deletions)
        existing_df = get_all_documents()
        
        archived_docs = []
        
        if not existing_df.empty:
            # Convert DF to list of dicts
            existing_rows = existing_df.to_dict('records')
            
            # Check for files in Sheet but NOT in Drive
            for row in existing_rows:
                link = row.get('Google Doc Link')
                status = row.get('Status')
                
                # If valid link exists, it's not in Drive anymore, and not already archived
                if link and link not in drive_links and status != 'Archived':
                    logger.warning(f"File missing from Drive, marking as Archived: {row.get('Document Name')}")
                    
                    # Convert row back to document format
                    archived_doc = map_sheet_row_to_doc_dict(row)
                    archived_docs.append(archived_doc)

        # 3. Merge Active + Archived
        # We process current docs (updates/adds) AND archived docs (status changes)
        final_list = drive_docs + archived_docs
        
        if archived_docs:
            logger.info(f"Processing {len(archived_docs)} archived items.")

        # 4. Push to Database
        if final_list:
            upsert_documents(final_list)
            logger.info("Sync Complete: Database updated successfully.")
        else:
            logger.info("Sync Complete: No data to process.")

    except Exception as e:
        logger.error(f"Sync Failed: {e}", exc_info=True)

def main():
    """
    Initializes the scheduler and keeps the script running.
    """
    config = load_config()
    
    # Get interval from config (default to 15 mins if missing)
    interval_minutes = config.get('sync', {}).get('interval_minutes', 15)
    
    logger.info(f"Initializing Sync Daemon (Interval: {interval_minutes} minutes)...")
    
    # Run once immediately on startup
    sync_job()
    
    # Schedule future runs
    scheduler = BlockingScheduler()
    scheduler.add_job(sync_job, 'interval', minutes=interval_minutes)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Sync Daemon stopped by user.")

if __name__ == "__main__":
    main()