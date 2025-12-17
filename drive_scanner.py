import json
import os
from dateutil import parser
from googleapiclient.discovery import build
from auth import authenticate_google_apis

# --- Configuration ---
CONFIG_FILE = 'config.json'

def load_config():
    """Loads configuration settings from the JSON file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file {CONFIG_FILE} not found. Please create it.")
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def parse_filename(filename):
    """
    Extracts 'Topic' and 'Architect' from the filename.
    Expected format: "System Design - [Architect Name]"
    """
    # Remove file extension if present (though Google Docs usually don't have one in the name)
    name = os.path.splitext(filename)[0]
    
    parts = name.split(' - ')
    
    if len(parts) >= 2:
        topic = parts[0].strip()
        architect = parts[-1].strip().replace('[', '').replace(']', '')
    else:
        topic = name
        architect = "Unknown"
        
    return topic, architect

def get_drive_service(creds):
    """Builds the Drive API service object."""
    return build('drive', 'v3', credentials=creds)

def scan_review_folder():
    """
    Main function to scan the configured Drive folder.
    Returns:
        List of dictionaries containing document metadata.
    """
    # 1. Setup
    config = load_config()
    folder_id = config['google']['drive_folder_id']
    
    print(f"--- Scanning Folder ID: {folder_id} ---")
    
    # 2. Authenticate
    creds = authenticate_google_apis()
    service = get_drive_service(creds)
    
    # 3. Query Drive API
    # q parameter filters for:
    # - Is inside our specific folder
    # - Is a Google Doc (ignores subfolders/images)
    # - Is not in the trash
    query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false"
    
    # fields parameter restricts the response to only what we need (saves bandwidth)
    # ADDED: 'createdTime' to the fields list
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink, lastModifyingUser)"
    ).execute()
    
    items = results.get('files', [])
    
    # 4. Process Results
    processed_docs = []
    
    if not items:
        print("No documents found in the folder.")
    else:
        print(f"Found {len(items)} documents.")
        for item in items:
            # Parse the filename
            topic, architect = parse_filename(item['name'])
            
            # Parse dates (convert ISO strings to readable datetime objects)
            mod_time = parser.parse(item['modifiedTime'])
            # ADDED: Parse createdTime
            created_time = parser.parse(item['createdTime'])
            
            # Extract last editor name safely
            last_editor = "Unknown"
            if 'lastModifyingUser' in item:
                last_editor = item['lastModifyingUser'].get('displayName', 'Unknown')

            doc_data = {
                'id': item['id'],
                'filename': item['name'],
                'topic': topic,
                'architect': architect,
                'link': item['webViewLink'],
                'modified_time': mod_time,
                'created_time': created_time,  # ADDED: Included in dictionary
                'last_editor': last_editor
            }
            processed_docs.append(doc_data)
            
            # Print preview
            print(f"  [+] Found: {topic} (by {architect})")

    return processed_docs

if __name__ == '__main__':
    # When run directly, print the raw data for verification
    try:
        data = scan_review_folder()
        print("\n--- Data Preview (First Item) ---")
        if data:
            print(data[0])
    except Exception as e:
        print(f"Error: {e}")