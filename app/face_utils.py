import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU

import pickle
import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional
from deepface import DeepFace

# Global variables
known_faces_encodings = []
known_faces_names = []
FACE_DATABASE_DIR = "face_database"
ENCODINGS_FILE = os.path.join(FACE_DATABASE_DIR, "encodings.pickle")
TOLERANCE = 0.4  # Threshold for similarity (higher means more similar)
MODEL_NAME = "Facenet512"  # Using Facenet512 for better accuracy
DISTANCE_METRIC = "cosine"  # Options: cosine, euclidean, euclidean_l2, angular

def load_known_faces():
    """Load known face encodings from disk"""
    global known_faces_encodings, known_faces_names
    
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
            known_faces_encodings = data["encodings"]
            known_faces_names = data["names"]
        print(f"Loaded {len(known_faces_names)} face encodings")
    else:
        print("No face encodings found")
        
def save_face_encoding(name: str, encoding: np.ndarray):
    """Save a new face encoding to disk"""
    global known_faces_encodings, known_faces_names
    
    known_faces_encodings.append(encoding)
    known_faces_names.append(name)
    
    # Save to disk
    data = {"encodings": known_faces_encodings, "names": known_faces_names}
    os.makedirs(FACE_DATABASE_DIR, exist_ok=True)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)
    
    print(f"Saved encoding for {name}")

def detect_faces(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Detect faces in an image and return their locations"""
    try:
        # DeepFace uses MTCNN for face detection
        face_objs = DeepFace.extract_faces(
            img_path=image,
            detector_backend="mtcnn",
            enforce_detection=True,
            align=True
        )
        
        # Convert DeepFace format to (top, right, bottom, left) format
        face_locations = []
        for face_obj in face_objs:
            facial_area = face_obj["facial_area"]
            x = facial_area["x"]
            y = facial_area["y"]
            w = facial_area["w"]
            h = facial_area["h"]
            # Convert to (top, right, bottom, left) format
            face_locations.append((y, x + w, y + h, x))
            
        return face_locations
    except Exception as e:
        print(f"Error detecting faces: {str(e)}")
        return []

def encode_face(image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
    """Generate face encoding for a detected face"""
    top, right, bottom, left = face_location
    face_img = image[top:bottom, left:right]
    
    # Get the face embedding using DeepFace
    embedding_obj = DeepFace.represent(
        img_path=face_img,
        model_name=MODEL_NAME,
        enforce_detection=False  # We already detected the face
    )
    
    # Return the embedding array
    return embedding_obj[0]["embedding"]

def find_cosine_distance(source_representation, test_representation):
    """Calculate cosine distance between two vectors"""
    a = np.matmul(np.transpose(source_representation), test_representation)
    b = np.sum(np.multiply(source_representation, source_representation))
    c = np.sum(np.multiply(test_representation, test_representation))
    return 1 - (a / (np.sqrt(b) * np.sqrt(c)))

def is_face_registered(face_encoding: np.ndarray) -> bool:
    """Check if a face encoding matches any registered face"""
    if not known_faces_encodings:
        return False
    
    for known_encoding in known_faces_encodings:
        # Calculate cosine similarity
        distance = find_cosine_distance(face_encoding, known_encoding)
        # For cosine: lower distance means more similar
        if distance < TOLERANCE:
            return True
    
    return False

def recognize_face(face_encoding: np.ndarray) -> Optional[str]:
    """Recognize a face and return the name if found"""
    if not known_faces_encodings:
        return None
    
    best_match_index = -1
    best_distance = float('inf')
    
    # Find the most similar face
    for i, known_encoding in enumerate(known_faces_encodings):
        # Calculate distance (lower is better)
        distance = find_cosine_distance(face_encoding, known_encoding)
        if distance < best_distance:
            best_distance = distance
            best_match_index = i
    
    # Check if the distance is below the threshold
    if best_distance < TOLERANCE and best_match_index >= 0:
        return known_faces_names[best_match_index]
    
    return None