from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import CameraModel


# ============================================================
# PATHS
# ============================================================

# backend/main.py
#        ↓
# backend folder
#        ↓
# project root
#        ↓
# frontend folder

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(title="Smart Video Management System")


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ============================================================
# PYDANTIC MODEL
# ============================================================

class Camera(BaseModel):
    name: str
    ip_address: str
    status: str


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# ============================================================
# GET ALL CAMERAS
# ============================================================

@app.get("/cameras")
def get_cameras():

    db: Session = SessionLocal()

    try:
        cameras = db.query(CameraModel).all()

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
            status=camera.status
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
            .filter(CameraModel.id == camera_id)
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
def update_camera(camera_id: int, camera: Camera):

    db: Session = SessionLocal()

    try:

        existing_camera = (
            db.query(CameraModel)
            .filter(CameraModel.id == camera_id)
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
            .filter(CameraModel.id == camera_id)
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
            "message": "Camera deleted successfully",
            "camera_id": camera_id
        }

    finally:
        db.close()