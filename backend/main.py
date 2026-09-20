from datetime import datetime
from pathlib import Path

import cv2

from fastapi import FastAPI, HTTPException
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    CameraModel,
    RecordingModel,
)
from backend.video import generate_camera_frames
from backend.recorder import (
    start_recording,
    stop_recording,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"

RECORDINGS_DIR = BASE_DIR / "recordings"


# Make sure recordings directory exists
RECORDINGS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Smart Video Management System",
    version="1.0.0"
)


# ============================================================
# STATIC FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(
        directory=str(FRONTEND_DIR)
    ),
    name="static"
)


# ============================================================
# PYDANTIC CAMERA MODEL
# ============================================================

class Camera(BaseModel):

    name: str

    ip_address: str

    status: str

    camera_type: str = "IP"

    location: str = "Unknown"

    rtsp_url: str | None = None

    username: str | None = None

    password: str | None = None

    device_index: int | None = None


# ============================================================
# HOME PAGE
# ============================================================

@app.get(
    "/",
    include_in_schema=False
)
def home():

    return FileResponse(
        str(
            FRONTEND_DIR / "index.html"
        )
    )


# ============================================================
# LIVE VIDEO
# ============================================================

@app.get(
    "/video-feed/{camera_id}",
    include_in_schema=False
)
def video_feed(
    camera_id: int
):

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


        return StreamingResponse(

            generate_camera_frames(

                camera_type=
                    camera.camera_type,

                device_index=
                    camera.device_index,

                rtsp_url=
                    camera.rtsp_url

            ),

            media_type=(
                "multipart/x-mixed-replace;"
                " boundary=frame"
            )

        )

    finally:

        db.close()



# ============================================================
# TEST CAMERA
# ============================================================

@app.post("/cameras/{camera_id}/test")
def test_camera(
    camera_id: int
):
    """
    Test whether the configured camera source can be opened
    and a video frame can be read.

    USB cameras use DirectShow on Windows.
    IP cameras use the configured RTSP URL.
    """

    db: Session = SessionLocal()

    capture = None

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

        camera_type = (
            str(camera.camera_type or "IP")
            .strip()
            .upper()
        )

        # --------------------------------------------------------
        # SELECT VIDEO SOURCE
        # --------------------------------------------------------

        if camera_type == "USB":

            if camera.device_index is None:
                camera.status = "offline"
                db.commit()

                raise HTTPException(
                    status_code=400,
                    detail="USB camera does not have a device index."
                )

            capture = cv2.VideoCapture(
                camera.device_index,
                cv2.CAP_DSHOW
            )

        elif camera_type == "IP":

            if not camera.rtsp_url:
                camera.status = "offline"
                db.commit()

                raise HTTPException(
                    status_code=400,
                    detail="IP camera does not have an RTSP URL."
                )

            capture = cv2.VideoCapture(
                camera.rtsp_url
            )

        else:

            camera.status = "offline"
            db.commit()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Camera type '{camera_type}' "
                    "is not supported for testing."
                )
            )

        # --------------------------------------------------------
        # OPEN CAMERA
        # --------------------------------------------------------

        if capture is None or not capture.isOpened():

            camera.status = "offline"
            db.commit()

            return {
                "success": False,
                "camera_id": camera.id,
                "status": "offline",
                "message": "Camera could not be opened."
            }

        # --------------------------------------------------------
        # READ ONE FRAME
        # --------------------------------------------------------

        success, frame = capture.read()

        if not success or frame is None:

            camera.status = "offline"
            db.commit()

            return {
                "success": False,
                "camera_id": camera.id,
                "status": "offline",
                "message": "Camera opened, but no video frame was received."
            }

        # --------------------------------------------------------
        # CAMERA IS WORKING
        # --------------------------------------------------------

        camera.status = "online"
        db.commit()

        height, width = frame.shape[:2]

        return {
            "success": True,
            "camera_id": camera.id,
            "status": "online",
            "message": "Camera is working.",
            "resolution": f"{width}x{height}"
        }

    finally:

        if capture is not None:
            capture.release()

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
def add_camera(
    camera: Camera
):

    db: Session = SessionLocal()

    try:

        new_camera = CameraModel(

            name=
                camera.name,

            ip_address=
                camera.ip_address,

            status=
                camera.status,

            camera_type=
                camera.camera_type,

            location=
                camera.location,

            rtsp_url=
                camera.rtsp_url,

            username=
                camera.username,

            device_index=
                camera.device_index

        )


        db.add(
            new_camera
        )

        db.commit()

        db.refresh(
            new_camera
        )


        return new_camera

    finally:

        db.close()


# ============================================================
# GET ONE CAMERA
# ============================================================

@app.get(
    "/cameras/{camera_id}"
)
def get_camera(
    camera_id: int
):

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

@app.put(
    "/cameras/{camera_id}"
)
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


        existing_camera.name = (
            camera.name
        )

        existing_camera.ip_address = (
            camera.ip_address
        )

        existing_camera.status = (
            camera.status
        )

        existing_camera.camera_type = (
            camera.camera_type
        )

        existing_camera.location = (
            camera.location
        )

        existing_camera.rtsp_url = (
            camera.rtsp_url
        )

        existing_camera.username = (
            camera.username
        )

        existing_camera.password = (
            camera.password
        )

        existing_camera.device_index = (
            camera.device_index
        )


        db.commit()

        db.refresh(
            existing_camera
        )


        return existing_camera

    finally:

        db.close()


# ============================================================
# DELETE CAMERA
# ============================================================

@app.delete(
    "/cameras/{camera_id}"
)
def delete_camera(
    camera_id: int
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


        db.delete(
            existing_camera
        )

        db.commit()


        return {

            "message":
                "Camera deleted successfully",

            "camera_id":
                camera_id

        }

    finally:

        db.close()


# ============================================================
# START RECORDING
# ============================================================

@app.post(
    "/record/start/{camera_id}"
)
def start_camera_recording(
    camera_id: int
):

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


        if (
            camera.camera_type.upper()
            != "USB"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Recording currently "
                    "supports USB cameras only."
                )
            )


        if camera.device_index is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "USB camera does not "
                    "have a device index."
                )
            )


        success, result = (
            start_recording(

                camera_id=
                    camera.id,

                device_index=
                    camera.device_index

            )
        )


        if not success:

            raise HTTPException(
                status_code=400,
                detail=result
            )


        return {

            "message":
                "Recording started successfully",

            "camera_id":
                camera.id,

            "filename":
                result["filename"],

            "start_time":
                result["start_time"]

        }

    finally:

        db.close()


# ============================================================
# STOP RECORDING
# ============================================================

@app.post(
    "/record/stop/{camera_id}"
)
def stop_camera_recording(
    camera_id: int
):

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


        success, result = (
            stop_recording(
                camera_id
            )
        )


        if not success:

            raise HTTPException(
                status_code=400,
                detail=result
            )


        new_recording = RecordingModel(

            camera_id=
                result["camera_id"],

            filename=
                result["filename"],

            start_time=
                result["start_time"],

            end_time=
                result["end_time"],

            duration_seconds=
                result[
                    "duration_seconds"
                ],

            status=
                "completed"

        )


        db.add(
            new_recording
        )

        db.commit()

        db.refresh(
            new_recording
        )


        return {

            "message":
                "Recording stopped successfully",

            "recording_id":
                new_recording.id,

            "camera_id":
                new_recording.camera_id,

            "filename":
                new_recording.filename,

            "start_time":
                new_recording.start_time,

            "end_time":
                new_recording.end_time,

            "duration_seconds":
                new_recording.duration_seconds,

            "status":
                new_recording.status

        }

    finally:

        db.close()


# ============================================================
# GET ALL RECORDINGS
# ============================================================

@app.get("/recordings")
def get_recordings():

    db: Session = SessionLocal()

    try:

        recordings = (
            db.query(RecordingModel)
            .order_by(
                RecordingModel.id.desc()
            )
            .all()
        )


        return recordings

    finally:

        db.close()

# ============================================================
# FIND RECORDING FILE
# ============================================================

def find_recording_file(filename: str):

    # Only use the filename stored in the database
    safe_filename = Path(filename).name

    original_file = (
        RECORDINGS_DIR / safe_filename
    ).resolve()

    recordings_root = (
        RECORDINGS_DIR.resolve()
    )

    # Security check
    if original_file.parent != recordings_root:

        raise HTTPException(
            status_code=400,
            detail="Invalid recording path"
        )

    # Browser-compatible H.264 version
    web_file = (
        original_file.with_name(
            original_file.stem + "_web.mp4"
        )
    )

    # Prefer H.264 version
    if web_file.is_file():

        return web_file

    # Otherwise use original
    if original_file.is_file():

        return original_file

    raise HTTPException(
        status_code=404,
        detail="Recording file not found"
    )


# ============================================================
# PLAY RECORDING
# ============================================================

@app.get(
    "/recordings/{recording_id}/video"
)
def play_recording(
    recording_id: int
):

    db: Session = SessionLocal()

    try:

        recording = (
            db.query(RecordingModel)
            .filter(
                RecordingModel.id == recording_id
            )
            .first()
        )

        if recording is None:

            raise HTTPException(
                status_code=404,
                detail="Recording not found"
            )

        recording_file = find_recording_file(
            recording.filename
        )

        return FileResponse(

            path=str(recording_file),

            media_type="video/mp4",

            headers={
                "Content-Disposition":
                    f'inline; filename="{recording_file.name}"'
            }
        )

    finally:

        db.close()


# ============================================================
# DOWNLOAD RECORDING
# ============================================================

@app.get(
    "/recordings/{recording_id}/download"
)
def download_recording(
    recording_id: int
):

    db: Session = SessionLocal()

    try:

        recording = (
            db.query(RecordingModel)
            .filter(
                RecordingModel.id == recording_id
            )
            .first()
        )

        if recording is None:

            raise HTTPException(
                status_code=404,
                detail="Recording not found"
            )

        recording_file = find_recording_file(
            recording.filename
        )

        return FileResponse(

            path=str(recording_file),

            media_type="video/mp4",

            headers={
                "Content-Disposition":
                    f'attachment; filename="{recording_file.name}"'
            }
        )

    finally:

        db.close()
