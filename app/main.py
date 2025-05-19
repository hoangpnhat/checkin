import os
from datetime import datetime
from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import numpy as np
import cv2
from sqlalchemy.orm import Session
import base64

from . import database, face_utils, google_sheets, save_image

# Add near the top of your file, before importing TensorFlow/face_utils
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU-only mode
# Create directories if they don't exist
os.makedirs("face_database", exist_ok=True)
os.makedirs("app/static/uploads", exist_ok=True)

app = FastAPI(title="Competition Check-in System")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize database
database.init_db()

# Initialize Google Sheets
google_sheets.init_sheets()

@app.on_event("startup")
async def startup_event():
    face_utils.load_known_faces()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("checkin.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    image_data: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # Process the base64 image
    try:
        # Remove the prefix and decode
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Detect face in the image
        face_locations = face_utils.detect_faces(image)
        if not face_locations:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "No face detected. Please try again."}
            )
            
        # Check if face already exists
        face_encoding = face_utils.encode_face(image, face_locations[0])
        if face_utils.is_face_registered(face_encoding):
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "This person is already registered."}
            )
            
        # Save face encoding and create user
        face_utils.save_face_encoding(name, face_encoding)
        database.create_user(db, name, datetime.now())
        
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "success": f"Registration successful for {name}!"}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": f"Error: {str(e)}"}
        )

@app.get("/checkin", response_class=HTMLResponse)
async def checkin_page(request: Request):
    return templates.TemplateResponse("checkin.html", {"request": request})

@app.post("/checkin")
async def checkin(
    request: Request,
    image_data: str = Form(...),
    name: str = Form(None),  # Make name optional, needed for registration
    db: Session = Depends(database.get_db)
):
    try:
        # Process the base64 image
        image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data_clean)
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Detect face
        face_locations = face_utils.detect_faces(image)
        if not face_locations:
            return templates.TemplateResponse(
                "checkin.html", 
                {"request": request, "error": "No face detected. Please try again."}
            )
            
        # Encode the face
        face_encoding = face_utils.encode_face(image, face_locations[0])
        
        # If name is provided, this is a registration submission
        if name:
            # Check if face already exists
            if face_utils.is_face_registered(face_encoding):
                return templates.TemplateResponse(
                    "checkin.html", 
                    {"request": request, "error": "This person is already registered."}
                )
                
            # Register the new face
            face_utils.save_face_encoding(name, face_encoding)
            database.create_user(db, name, datetime.now())
            
            # Continue with check-in process for the newly registered user
            recognized_name = name
        else:
            # Try to recognize the face
            recognized_name = face_utils.recognize_face(face_encoding)
            
            if not recognized_name:
                # Face not recognized, show registration form
                return templates.TemplateResponse(
                    "checkin.html", 
                    {
                        "request": request,
                        "show_registration": True,
                        "captured_image": image_data,
                        "info": "Face not recognized. Please enter your name to register."
                    }
                )
        
        # Check if already checked in today
        today = datetime.now().date()
        if database.has_checked_in_today(db, recognized_name, today):
            return templates.TemplateResponse(
                "checkin.html", 
                {"request": request, "error": f"{recognized_name} has already checked in today."}
            )
            
        # Save the image and get the URL
        image_url = save_image.save_image_from_data_url(image_data_clean, recognized_name)
            
        # Record check-in time and prepare data for confirmation
        check_in_time = datetime.now()
        check_in_data = {
            "name": recognized_name,
            "time": check_in_time.strftime("%Y-%m-%d %H:%M:%S"),
            "image": image_data,
            "image_url": image_url,
            "show_timer": True  # Flag to show the timer
        }
        
        return templates.TemplateResponse(
            "confirm.html", 
            {"request": request, "data": check_in_data}
        )
        
    except Exception as e:
        print(f"Error in checkin: {str(e)}")
        return templates.TemplateResponse(
            "checkin.html", 
            {"request": request, "error": f"Error: {str(e)}"}
        )
    
@app.post("/confirm")
async def confirm_checkin(
    request: Request,
    name: str = Form(...),
    time: str = Form(...),
    score: float = Form(0.0),
    image_url: str = Form(""),
    completion_time: int = Form(0),  # New parameter for the timer
    db: Session = Depends(database.get_db)
):
    """Confirm the check-in and record it in the database and Google Sheets"""
    try:
        # Record check-in in database
        check_in_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        database.record_checkin(db, name, check_in_time, score)
        
        # Format the completion time (seconds to MM:SS)
        minutes = completion_time // 60
        seconds = completion_time % 60
        formatted_completion_time = f"{minutes:02d}:{seconds:02d}"
        
        # Get the server's base URL for the absolute URL
        base_url = "https://checkin.tainangphuyen.com"
        full_image_url = f"{base_url}{image_url}" if image_url else ""
        
        # Send to Google Sheets with image URL and completion time
        google_sheets.add_checkin_record(name, time, score, full_image_url, formatted_completion_time)
        
        return templates.TemplateResponse(
            "success.html", 
            {
                "request": request, 
                "message": f"Check-in confirmed for {name}!",
                "details": f"Time: {time}, Score: {score}, Completion time: {formatted_completion_time}",
                "image_url": image_url
            }
        )
    except Exception as e:
        print(f"Error confirming check-in: {str(e)}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": f"Error confirming check-in: {str(e)}"}
        )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=5015, reload=True)