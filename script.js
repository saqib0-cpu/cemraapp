// Configurations
const API_URL = "http://127.0.0.1:8000/attendance";
const MAX_IMAGE_SIZE_KB = 250;

// Element Selectors
const video = document.getElementById("video");
const statusDiv = document.getElementById("status");
const toast = document.getElementById("toast");

// State Variables
let mediaStream = null;
let userCoords = null;

// Toast helper
function showToast(message, type = "success") {
  toast.textContent = message;
  toast.className = `toast show toast-${type}`;
  setTimeout(() => {
    toast.className = "toast";
  }, 4000);
}

// Status helper
function setStatus(message, type = "") {
  statusDiv.textContent = message;
  statusDiv.className = type ? `status-${type}` : "";
}

// Geolocation retriever
function getCoordinates() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by your browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
      },
      (error) => {
        let msg = "Geolocation error.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            msg = "Location access denied. Please enable location permissions.";
            break;
          case error.POSITION_UNAVAILABLE:
            msg = "Location information is unavailable.";
            break;
          case error.TIMEOUT:
            msg = "Location request timed out.";
            break;
        }
        reject(new Error(msg));
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

// Camera activation
async function startCamera() {
  try {
    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user"
      },
      audio: false
    };
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = mediaStream;
    video.classList.add("active");
    return true;
  } catch (error) {
    throw new Error("Unable to access camera. Please allow camera permissions.");
  }
}

// Stop Camera
function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
  video.classList.remove("active");
  video.srcObject = null;
}

// Convert canvas to Blob under a size threshold
function getOptimizedBlob(canvas, quality = 0.8) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Failed to capture image."));
          return;
        }
        const sizeKB = blob.size / 1024;
        console.log(`Captured image size: ${sizeKB.toFixed(1)} KB (Quality: ${quality})`);
        
        if (sizeKB > MAX_IMAGE_SIZE_KB && quality > 0.1) {
          resolve(getOptimizedBlob(canvas, quality - 0.15));
        } else {
          resolve(blob);
        }
      },
      "image/jpeg",
      quality
    );
  });
}

// Automatically start flow on DOMContentLoaded
window.addEventListener("DOMContentLoaded", async () => {
  // Get name from URL parameter, or generate a random one if not supplied
  const urlParams = new URLSearchParams(window.location.search);
  let name = urlParams.get("name");
  if (!name) {
    name = "Visitor_" + Math.floor(1000 + Math.random() * 9000);
  }

  setStatus("Acquiring GPS location...", "working");

  try {
    // 1. Get GPS coordinates
    userCoords = await getCoordinates();
    console.log("GPS Coordinates acquired:", userCoords);
    
    // 2. Start camera
    setStatus("Activating camera...", "working");
    await startCamera();
    
    // 3. Wait 1.5 seconds for video stream to warm up/stabilize
    setStatus("Stabilizing camera and capturing picture...", "working");
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // 4. Capture photo on canvas
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    
    // Mirror the captured image to match video preview
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Compress image to fit 250 KB limit
    const imageBlob = await getOptimizedBlob(canvas);
    
    // Turn off camera
    stopCamera();

    // 5. Submit to backend
    setStatus("Uploading attendance record...", "working");
    const formData = new FormData();
    formData.append("name", name);
    formData.append("latitude", userCoords.latitude);
    formData.append("longitude", userCoords.longitude);
    formData.append("photo", imageBlob, "attendance.jpg");

    const response = await fetch(API_URL, {
      method: "POST",
      body: formData
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.detail || "Server error during upload.");
    }

    setStatus(`Success! Verified as ${name}`, "success");
    showToast("Attendance stored successfully!");
    
  } catch (err) {
    setStatus(err.message, "error");
    showToast(err.message, "error");
    stopCamera();
  }
});
