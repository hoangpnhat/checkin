import os
import uuid
import base64
from datetime import datetime
from PIL import Image
import io

def save_image_from_data_url(data_url, name):
    """
    Save an image from a data URL to disk.
    """
    # Create directory if it doesn't exist
    upload_dir = os.path.join('app', 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Extract the base64 encoded image
    if ',' in data_url:
        _, encoded = data_url.split(",", 1)
    else:
        encoded = data_url
    
    try:
        # Decode the image data
        image_data = base64.b64decode(encoded)
        
        # Generate a unique filename
        safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        file_path = os.path.join(upload_dir, filename)
        
        # Save the image directly - it should already be mirrored by canvas
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # Debugging output
        print(f"Saved image to {file_path}")
        
        # Return URL path
        return f"/static/uploads/{filename}"
        
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        raise ValueError(f"Invalid base64 data: {str(e)}")