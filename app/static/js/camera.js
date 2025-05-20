let video;
let canvas;
let capturedImage;
let imageData;
let stream;
let isCameraActive = false;
let facingMode = "user"; // Default to front camera
let cameraDevices = [];
let selectedCameraId = null;

/**
 * Initialize the camera and video stream
 */
function initCamera(deviceId = null) {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    capturedImage = document.getElementById('captured-image');
    
    // Apply mirror effect to video preview
    video.style.transform = 'scaleX(-1)';

    showCameraLoading();
    
    // Get access to the camera with optimal settings
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Configure video constraints
        const constraints = { 
            video: { 
                width: { ideal: 840 },
                height: { ideal: 680 }
            }
        };
        
        // If a specific device ID is provided, use it
        if (deviceId) {
            constraints.video.deviceId = { exact: deviceId };
        } else if (selectedCameraId) {
            constraints.video.deviceId = { exact: selectedCameraId };
        } else {
            constraints.video.facingMode = facingMode;
        }
        
        navigator.mediaDevices.getUserMedia(constraints)
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = mediaStream;
            video.play();
            isCameraActive = true;
            hideCameraLoading();
            
            // Make sure video is visible and properly mirrored
            video.style.display = 'inline-block';
            video.style.transform = facingMode === "user" ? 'scaleX(-1)' : 'none';
            
            // Hide captured image if visible
            if (capturedImage) {
                capturedImage.style.display = 'none';
            }
        })
        .catch(function(error) {
            console.error("Error accessing camera: ", error);
            hideCameraLoading();
            
            // Show specific error message based on error type
            if (error.name === 'NotAllowedError') {
                alert("Camera access denied. Please allow camera access in your browser settings.");
            } else if (error.name === 'NotFoundError') {
                alert("No camera found. Please make sure your device has a camera.");
            } else {
                alert("Error accessing camera: " + error.message);
            }
        });
    } else {
        hideCameraLoading();
        alert("Sorry, your browser does not support camera access.");
    }
}

/**
 * Populate camera selection dropdown
 */
async function populateCameraOptions() {
    const select = document.getElementById('camera-select');
    if (!select) return;

    // Clear existing options except the first one
    while (select.options.length > 1) {
        select.remove(1);
    }

    try {
        // Get camera permission first to display labels
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop());

        // Get list of devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        cameraDevices = devices.filter(device => device.kind === 'videoinput');

        if (cameraDevices.length === 0) {
            select.options[0].text = "No cameras found";
            return;
        }

        select.options[0].text = "Select camera...";

        cameraDevices.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Camera ${index + 1}`;
            select.appendChild(option);
        });

    } catch (error) {
        console.error('Error enumerating devices:', error);
        select.options[0].text = "Error loading cameras";
    }
}

/**
 * Capture image from video stream
 */function captureImage() {
    if (!video || !canvas) {
        console.error("Video or canvas element not found");
        return;
    }
    
    const context = canvas.getContext('2d');
    
    // Ensure canvas dimensions match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // First clear the canvas
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    // Always mirror the front-facing camera images
    if (facingMode === "user") {
        // Save the current context state
        context.save();
        
        // Set up for mirroring: translate and scale
        context.translate(canvas.width, 0);
        context.scale(-1, 1);
        
        // Draw the video mirrored
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Restore the context state
        context.restore();
    } else {
        // For back camera, draw normally
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
    }
    
    // Convert canvas to data URL (base64)
    imageData = canvas.toDataURL('image/jpeg', 0.9);
    
    // Display captured image 
    if (capturedImage) {
        capturedImage.src = imageData;
        capturedImage.style.display = 'inline-block';
        capturedImage.style.transform = 'none'; // No additional transform needed
    }
    
    // Hide video element
    if (video) {
        video.style.display = 'none';
    }
    
    // Show photo preview container if it exists
    const photoPreview = document.getElementById('photo-preview');
    if (photoPreview) {
        photoPreview.style.display = 'inline-block';
    }
    
    // Hide capture button if it exists
    const captureBtn = document.getElementById('capture-btn');
    if (captureBtn) {
        captureBtn.style.display = 'none';
    }
    
    // Set image data in the form hidden input
    const imageDataInput = document.getElementById('image-data');
    if (imageDataInput) {
        imageDataInput.value = imageData;
    }
    
    // Add debug output
    console.log("Image captured with facingMode:", facingMode);
    return imageData;
}

/**
 * Stop the camera stream
 */
function stopCamera() {
    if (!stream) return;
    
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    
    if (video) {
        video.srcObject = null;
    }
    
    isCameraActive = false;
    console.log("Camera stopped");
}

/**
 * Toggle between front and back camera
 */
function switchCamera() {
    if (isCameraActive) {
        stopCamera();
    }
    
    // Toggle facing mode
    facingMode = facingMode === "user" ? "environment" : "user";
    
    // Reinitialize camera with new facing mode
    setTimeout(initCamera, 300);
}

/**
 * Check if the device has multiple cameras
 * @returns {Promise<boolean>}
 */
async function hasMultipleCameras() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        return false;
    }
    
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        return videoDevices.length > 1;
    } catch (error) {
        console.error('Error checking cameras:', error);
        return false;
    }
}

/**
 * Show a loading indicator while the camera initializes
 */
function showCameraLoading() {
    const cameraContainer = document.querySelector('.camera-container');
    
    // Only create if it doesn't exist already
    if (cameraContainer && !document.querySelector('.camera-loading')) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'camera-loading';
        loadingDiv.innerHTML = '<div class="spinner"></div><p>Initializing camera...</p>';
        cameraContainer.prepend(loadingDiv);
    }
}

/**
 * Hide the camera loading indicator
 */
function hideCameraLoading() {
    const loadingElement = document.querySelector('.camera-loading');
    if (loadingElement) {
        loadingElement.remove();
    }
}

/**
 * Take a new photo (reset to camera view)
 */
function retakePhoto() {
    // Hide captured image
    if (capturedImage) {
        capturedImage.src = '';
        capturedImage.style.display = 'none';
    }
    
    // Show video with proper mirroring
    if (video) {
        video.style.display = 'inline-block';
        video.style.transform = facingMode === "user" ? 'scaleX(-1)' : 'none';
    }
    
    // Hide photo preview if it exists
    const photoPreview = document.getElementById('photo-preview');
    if (photoPreview) {
        photoPreview.style.display = 'none';
    }
    
    // Show capture button if it exists
    const captureBtn = document.getElementById('capture-btn');
    if (captureBtn) {
        captureBtn.style.display = 'inline-block';
    }
    
    // Clear the image data field
    const imageDataInput = document.getElementById('image-data');
    if (imageDataInput) {
        imageDataInput.value = '';
    }
}

/**
 * Check if the camera is available and has permission
 */
async function checkCameraAvailability() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        return true;
    } catch (error) {
        console.error('Camera not available:', error);
        return false;
    }
}

// Stop camera when navigating away from the page
window.addEventListener('beforeunload', stopCamera);

// Stop camera when the tab becomes inactive
document.addEventListener('visibilitychange', () => {
    if (document.hidden && isCameraActive) {
        stopCamera();
    } else if (!document.hidden && !isCameraActive && video) {
        initCamera();
    }
});

// Initialize camera selection when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Populate dropdown
    await populateCameraOptions();

    const cameraSelect = document.getElementById('camera-select');
    if (cameraSelect) {
        cameraSelect.addEventListener('change', function () {
            selectedCameraId = this.value;
            if (selectedCameraId) {
                if (isCameraActive) stopCamera();
                initCamera(selectedCameraId);
            }
        });
    }

    // Show "Switch camera" button if multiple cameras exist
    const hasMultiple = cameraDevices.length > 1;
    const switchBtn = document.getElementById('switch-camera');

    if (switchBtn && hasMultiple) {
        switchBtn.style.display = 'inline-block';
        switchBtn.addEventListener('click', switchCamera);
    }
});