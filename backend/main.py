from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import CameraModel
from backend.video import generate_camera_frames


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Smart Video Management System",
    version="1.0.0"
)


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ============================================================
# CAMERA API MODEL
# ============================================================

class Camera(BaseModel):

    name: str

    ip_address: str

    status: str

    camera_type: str = "IP"

    location: str = "Unknown"

    rtsp_url: str | None = None

    username: str | None = None

    device_index: int | None = None


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", include_in_schema=False)
def home():

    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# ============================================================
# VIDEO FEED
# ============================================================

@app.get(
    "/video-feed/{camera_id}",
    include_in_schema=False
)
def video_feed(camera_id: int):

    db: Session = SessionLocal()

    try:

        camera = (
            db.query(CameraModel)
            .filter(CameraModel.id == camera_id)
            .first()
        )

        if camera is None:

            raise HTTPException(
                status_code=404,
                detail="Camera not found"
            )


        return StreamingResponse(

            generate_camera_frames(
                camera_type=camera.camera_type,
                device_index=camera.device_index,
                rtsp_url=camera.rtsp_url
            ),

            media_type=(
                "multipart/x-mixed-replace; "
                "boundary=frame"
            )
        )

    finally:

        db.close()

# ============================================================
# GET ALL CAMERAS
# ============================================================

@app.get("/cameras")
def get_cameras():

    db: Session = SessionLocal()

    try:

        cameras = (
            db.query(CameraModel)
            .all()
        )

        return cameras

    finally:

        db.close()


# ============================================================
# ADD CAMERA
# ============================================================

@app.post("/cameras")
def add_camera(camera: Camera):

    db: Session = SessionLocal()

    try:

        new_camera = CameraModel(

            name=camera.name,

            ip_address=camera.ip_address,

            status=camera.status,

            camera_type=camera.camera_type,

            location=camera.location,

            rtsp_url=camera.rtsp_url,

            username=camera.username,

            device_index=camera.device_index

        )

        db.add(new_camera)

        db.commit()

        db.refresh(new_camera)

        return new_camera

    finally:

        db.close()


# ============================================================
# GET ONE CAMERA
# ============================================================

@app.get("/cameras/{camera_id}")
def get_camera(camera_id: int):

    db: Session = SessionLocal()

    try:

        camera = (
            db.query(CameraModel)
            .filter(
                CameraModel.id == camera_id
            )
            .first()
        )

        if camera is None:

            raise HTTPException(
                status_code=404,
                detail="Camera not found"
            )

        return camera

    finally:

        db.close()


# ============================================================
# UPDATE CAMERA
# ============================================================

@app.put("/cameras/{camera_id}")
def update_camera(
    camera_id: int,
    camera: Camera
):

    db: Session = SessionLocal()

    try:

        existing_camera = (
            db.query(CameraModel)
            .filter(
                CameraModel.id == camera_id
            )
            .first()
        )

        if existing_camera is None:

            raise HTTPException(
                status_code=404,
                detail="Camera not found"
            )


        existing_camera.name = camera.name

        existing_camera.ip_address = camera.ip_address

        existing_camera.status = camera.status

        existing_camera.camera_type = camera.camera_type

        existing_camera.location = camera.location

        existing_camera.rtsp_url = camera.rtsp_url

        existing_camera.username = camera.username

        existing_camera.device_index = camera.device_index


        db.commit()

        db.refresh(existing_camera)

        return existing_camera

    finally:

        db.close()


# ============================================================
# DELETE CAMERA
# ============================================================

@app.delete("/cameras/{camera_id}")
def delete_camera(camera_id: int):

    db: Session = SessionLocal()

    try:

        existing_camera = (
            db.query(CameraModel)
            .filter(
                CameraModel.id == camera_id
            )
            .first()
        )

        if existing_camera is None:

            raise HTTPException(
                status_code=404,
                detail="Camera not found"
            )


        db.delete(existing_camera)

        db.commit()


        return {

            "message":
                "Camera deleted successfully",

            "camera_id":
                camera_id
        }

    finally:

        db.close()