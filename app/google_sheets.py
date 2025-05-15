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

def add_checkin_record(name: str, time: str, score: float = 0.0):
    """Add a new check-in record to Google Sheets"""
    global sheet
    
    if not sheet:
        raise Exception("Google Sheets connection not initialized")
    
    # Append row to the sheet
    row = [name, time, str(score)] #STT,ten,diem,thoi_gian,image
    sheet.insert_row(row)
    print(f"Added check-in record for {name} to Google Sheets")