# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import base64
import datetime

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
DB_NAME = os.getenv("MONGODB_DB", "attendance_db")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION", "records")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
attendance_collection = db[COLLECTION_NAME]

app = FastAPI(title="Student Attendance API", version="1.0.0")

# Demo configuration – allow any origin. Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttendanceRecord(BaseModel):
    name: str = Field(..., description="Student name or identifier")
    latitude: float = Field(..., description="Latitude from geolocation")
    longitude: float = Field(..., description="Longitude from geolocation")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    photo_base64: str = Field(..., description="Base64‑encoded JPEG image")
    photo_size_kb: int = Field(..., description="Size of the stored image in kilobytes")

@app.post("/attendance")
async def submit_attendance(
    name: str = Form("Anonymous"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(...),
):
    """Accept attendance data via multipart/form‑data, store in MongoDB.

    The photo must be a JPEG and not exceed 250 KB.
    """
    if photo.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only JPEG images are accepted")
    raw_bytes = await photo.read()
    size_kb = len(raw_bytes) // 1024
    if size_kb > 250:
        raise HTTPException(status_code=400, detail="Photo exceeds 250 KB size limit")
    b64_str = base64.b64encode(raw_bytes).decode("utf-8")
    record = AttendanceRecord(
        name=name,
        latitude=latitude,
        longitude=longitude,
        photo_base64=b64_str,
        photo_size_kb=size_kb,
    )
    result = await attendance_collection.insert_one(record.dict())
    if result.inserted_id:
        return {"status": "success", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to store attendance record")

@app.get("/attendance")
async def get_attendance():
    """Retrieve all attendance records from MongoDB, sorted by timestamp descending."""
    records = []
    async for record in attendance_collection.find().sort("timestamp", -1):
        record["_id"] = str(record["_id"])
        if isinstance(record.get("timestamp"), datetime.datetime):
            record["timestamp"] = record["timestamp"].isoformat()
        records.append(record)
    return records


# ── Static file routes (serve HTML pages over HTTP) ──────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect root to the capture page."""
    return HTMLResponse(content='<meta http-equiv="refresh" content="0;url=/capture">')

@app.get("/capture", response_class=HTMLResponse)
async def serve_capture():
    """Serve the student capture page."""
    return FileResponse("capture.html")

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Serve the admin dashboard."""
    return FileResponse("admin.html")

@app.get("/styles.css")
async def serve_css():
    return FileResponse("styles.css", media_type="text/css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("script.js", media_type="application/javascript")
