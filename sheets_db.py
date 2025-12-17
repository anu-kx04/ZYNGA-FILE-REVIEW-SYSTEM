import gspread
import pandas as pd
from gspread.utils import rowcol_to_a1
from auth import authenticate_google_apis
import json

CONFIG_FILE = 'config.json'

def get_db_connection():
    """Connects to Google Sheets using our existing auth system."""
    creds = authenticate_google_apis()
    client = gspread.authorize(creds)
    
    with open(CONFIG_FILE) as f:
        config = json.load(f)
        
    sheet_id = config['google']['sheet_id']
    return client.open_by_key(sheet_id)

def initialize_sheet(worksheet):
    """
    Sets up headers, validation, and conditional formatting using raw API requests.
    """
    # 1. Define Headers
    headers = [
        "Document Name", "Owner", "Created Date", "Last Modified", 
        "Status", "Days Old", "Days Since Update", "Priority Score", 
        "Google Doc Link", "Notes"
    ]
    
    # Check if headers exist; if not, create them
    current_headers = worksheet.row_values(1)
    if not current_headers or current_headers[0] != "Document Name":
        print("Initializing headers...")
        worksheet.clear() # Force clear to avoid mismatch
        worksheet.append_row(headers)
        # Bold the header row
        worksheet.format('A1:J1', {'textFormat': {'bold': True}})

    # 2. Data Validation & Formatting
    # We must use the SPREADSHEET object for batch_update, not the WORKSHEET
    spreadsheet = worksheet.spreadsheet
    
    # Validation Rule for 'Status' (Column E)
    validation_rule = {
        'setDataValidation': {
            'range': {
                'sheetId': worksheet.id,
                'startRowIndex': 1, 'endRowIndex': 1000, 
                'startColumnIndex': 4, 'endColumnIndex': 5 # Column E (0-index: 4)
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_LIST',
                    'values': [
                        {'userEnteredValue': 'Pending'},
                        {'userEnteredValue': 'In Review'},
                        {'userEnteredValue': 'Approved'},
                        {'userEnteredValue': 'Needs Changes'},
                        {'userEnteredValue': 'Completed'},
                        {'userEnteredValue': 'Archived'}  # Added Archived to dropdown
                    ]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    }

    # Conditional Formatting for 'Priority Score' (Column H)
    grid_range = {
        'sheetId': worksheet.id,
        'startRowIndex': 1, 'endRowIndex': 1000,
        'startColumnIndex': 7, 'endColumnIndex': 8
    }

    # Rules for Red, Yellow, Green
    cf_rules = [
        # Red >= 10
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [grid_range],
                    'booleanRule': {
                        'condition': {'type': 'NUMBER_GREATER_THAN_EQ', 'values': [{'userEnteredValue': '10'}]},
                        'format': {'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}}
                    }
                },
                'index': 0
            }
        },
        # Yellow 5-10
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [grid_range],
                    'booleanRule': {
                        'condition': {
                            'type': 'NUMBER_BETWEEN', 
                            'values': [{'userEnteredValue': '5'}, {'userEnteredValue': '10'}]
                        },
                        'format': {'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}}
                    }
                },
                'index': 1
            }
        },
        # Green < 5
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [grid_range],
                    'booleanRule': {
                        'condition': {'type': 'NUMBER_LESS_THAN', 'values': [{'userEnteredValue': '5'}]},
                        'format': {'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}}
                    }
                },
                'index': 2
            }
        }
    ]

    # Execute formatting
    try:
        # Note: We use spreadsheet.batch_update, NOT worksheet.batch_update
        requests = [validation_rule] + cf_rules
        spreadsheet.batch_update({'requests': requests})
    except Exception as e:
        # It's common for this to fail if rules overlap, safe to ignore in dev
        pass 

def upsert_documents(documents):
    """
    Syncs Scan Data with Sheet Data.
    - Adds new docs found in Drive.
    - Updates metadata for existing docs.
    - PRESERVES 'Status' and 'Notes' unless forced to Archive.
    """
    sh = get_db_connection()
    
    # Ensure 'Active Reviews' tab exists
    try:
        ws = sh.worksheet("Active Reviews")
    except:
        ws = sh.add_worksheet(title="Active Reviews", rows=1000, cols=10)
    
    initialize_sheet(ws)
    
    # 1. Read existing data
    existing_records = ws.get_all_records()
    
    # Create lookup map (Safe check for empty sheet)
    existing_map = {}
    if existing_records:
        # This key MUST match the header in the sheet
        existing_map = {r.get('Google Doc Link', ''): r for r in existing_records}
    
    # 2. Prepare new rows
    rows_to_write = []
    
    for i, doc in enumerate(documents):
        row_num = i + 2  # Row 1 is header
        link = doc['link']
        
        # Default values
        status = "Pending"
        notes = ""
        
        # --- LOGIC UPDATE START ---
        
        # 1. Check for Archive Override (from sync_daemon)
        if doc.get('status_override') == 'Archived':
            status = 'Archived'
            # Optional: preserve notes even if archived
            if link in existing_map:
                notes = existing_map[link].get('Notes', '')

        # 2. Preserve existing Status/Notes (if not forcing Archive)
        elif link in existing_map:
            status = existing_map[link].get('Status', 'Pending')
            notes = existing_map[link].get('Notes', '')
            
        # --- LOGIC UPDATE END ---

        # Formulas
        f_days = f'=IF(C{row_num}<>"", TODAY()-C{row_num}, "")'
        f_update = f'=IF(D{row_num}<>"", TODAY()-D{row_num}, "")'
        f_score = f'=IF(AND(F{row_num}<>"", G{row_num}<>""), F{row_num}+G{row_num}, "")'

        # Row Data
        row = [
            doc['topic'],                   # A
            doc['architect'],               # B
            str(doc.get('created_time', '')).split('+')[0], # C
            str(doc['modified_time']).split('+')[0],        # D
            status,                         # E
            f_days,                         # F
            f_update,                       # G
            f_score,                        # H
            link,                           # I
            notes                           # J
        ]
        rows_to_write.append(row)

    # 3. Batch Write
    if rows_to_write:
        print(f"Upserting {len(rows_to_write)} documents...")
        ws.batch_clear(['A2:J1000'])
        ws.update('A2', rows_to_write, value_input_option='USER_ENTERED')
        print("Database sync complete.")

def get_all_documents():
    sh = get_db_connection()
    ws = sh.worksheet("Active Reviews")
    return pd.DataFrame(ws.get_all_records())