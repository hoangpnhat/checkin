import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Global variables
sheet = None
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def init_sheets():
    """Initialize Google Sheets connection"""
    print("Initializing Google Sheets...")
    global sheet
    
    try:
        # Create a credentials file from environment variable if it doesn't exist
        # Use the file for authentication
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
        client = gspread.authorize(creds)
        
        # Open the Google Sheet
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet = client.open_by_key(sheet_id).sheet1
        print(sheet)
        print("Google Sheets connection established")
    except Exception as e:
        print(f"Error initializing Google Sheets: {str(e)}")
    return sheet

def add_checkin_record(name: str, time: str, score: float = 0.0, image_url: str = "", 
                      completion_time: str = "", school_name: str = "", phone_number: str = ""):
    """Add a new check-in record to Google Sheets"""
    global sheet
    
    if not sheet:
        raise Exception("Google Sheets connection not initialized")
    
    # Append row to the sheet
    row = [name, time, str(score), image_url, completion_time, school_name, phone_number]
    sheet.append_row(row)
    print(f"Added check-in record for {name} to Google Sheets")
    
    # Get all data (including headers)
    all_data = sheet.get_all_values()
    
    # Separate headers and data
    headers = all_data[0]
    data = all_data[1:]
    
    # Find the indices for score and completion_time columns
    score_idx = headers.index("Score") if "Score" in headers else 2  # Default to column C (index 2)
    time_idx = headers.index("Completion Time") if "Completion Time" in headers else 4  # Default to column E (index 4)
    
    # Sort the data rows: first by score (descending), then by completion time (ascending)
    sorted_data = sorted(
        data, 
        key=lambda x: (
            -float(x[score_idx] or 0),  # Convert score to float, use 0 if empty
            x[time_idx] or "99:99"      # Sort by completion time (ascending), use a large value if empty
        )
    )
    
    # Update the sheet with the sorted data (keep the headers)
    sheet.update([headers] + sorted_data)
    
    print("Google Sheet data sorted by score (descending) and completion time (ascending)")