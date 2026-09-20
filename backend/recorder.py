from datetime import datetime
from pathlib import Path
import math
import subprocess
import threading

import cv2


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RECORDINGS_DIR = BASE_DIR / "recordings"

RECORDINGS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# ACTIVE RECORDINGS
# ============================================================

active_recordings = {}


# ============================================================
# CONVERT RECORDING TO H.264
# ============================================================

def convert_to_h264(
    input_file: Path,
    output_file: Path
):
    print()
    print("Converting recording to H.264...")
    print(f"Input : {input_file}")
    print(f"Output: {output_file}")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(output_file),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("FFmpeg was not found in PATH.")
        return False
    except Exception as exc:
        print(f"FFmpeg conversion error: {exc}")
        return False

    if result.returncode != 0:
        print("FFmpeg conversion failed.")
        print(result.stderr)
        return False

    if not output_file.exists():
        print(
            "FFmpeg finished, but output "
            "file was not found."
        )
        return False

    print("H.264 conversion successful.")
    return True


# ============================================================
# OPEN CAMERA SOURCE
# ============================================================

def _open_camera_source(
    camera_type: str,
    device_index: int | None = None,
    rtsp_url: str | None = None,
):
    """
    Open either a USB camera or an IP/RTSP camera.

    USB:
        Uses DirectShow on Windows.

    IP:
        Uses the RTSP URL. We try FFmpeg first and then
        OpenCV's default backend as a fallback.
    """

    normalized_type = (
        str(camera_type or "USB").strip().upper()
    )

    if normalized_type == "USB":
        if device_index is None:
            return None, "USB camera does not have a device index."

        print(
            f"Opening USB camera device {device_index}..."
        )

        camera = cv2.VideoCapture(
            int(device_index),
            cv2.CAP_DSHOW,
        )

        return camera, None

    if normalized_type == "IP":
        if not rtsp_url:
            return None, "IP camera does not have an RTSP URL."

        print(f"Opening IP camera RTSP stream: {rtsp_url}")

        # Prefer FFmpeg for RTSP when available.
        try:
            camera = cv2.VideoCapture(
                rtsp_url,
                cv2.CAP_FFMPEG,
            )

            if camera.isOpened():
                return camera, None

            camera.release()
        except Exception as exc:
            print(
                "FFmpeg backend could not open RTSP stream: "
                f"{exc}"
            )

        # Fallback to OpenCV's default backend.
        camera = cv2.VideoCapture(rtsp_url)

        return camera, None

    return (
        None,
        (
            f"Unsupported camera type '{normalized_type}'. "
            "Use USB or IP."
        ),
    )


# ============================================================
# GET VIDEO SETTINGS
# ============================================================

def _get_video_settings(camera, first_frame=None):
    """
    Determine a usable frame size and FPS.

    RTSP cameras sometimes report 0 or invalid FPS values, so
    a safe default is used when necessary.
    """

    if first_frame is not None:
        frame_height, frame_width = first_frame.shape[:2]
    else:
        frame_width = int(
            camera.get(cv2.CAP_PROP_FRAME_WIDTH) or 0
        )
        frame_height = int(
            camera.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0
        )

    if frame_width <= 0:
        frame_width = 640

    if frame_height <= 0:
        frame_height = 480

    fps_value = camera.get(cv2.CAP_PROP_FPS)

    try:
        fps = float(fps_value)
    except (TypeError, ValueError):
        fps = 20.0

    if not math.isfinite(fps) or fps <= 1 or fps > 120:
        fps = 20.0

    return (
        frame_width,
        frame_height,
        fps,
    )


# ============================================================
# START RECORDING
# ============================================================

def start_recording(
    camera_id: int,
    device_index: int | None = None,
    camera_type: str = "USB",
    rtsp_url: str | None = None,
):
    """
    Start background recording.

    Backwards compatible with the previous call:

        start_recording(camera_id, device_index)

    New IP-camera call:

        start_recording(
            camera_id,
            camera_type="IP",
            rtsp_url="rtsp://..."
        )
    """

    if camera_id in active_recordings:
        return (
            False,
            "Camera is already recording.",
        )

    normalized_type = (
        str(camera_type or "USB").strip().upper()
    )

    # --------------------------------------------------------
    # CREATE FILE NAME
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"camera_{camera_id}_{timestamp}.mp4"
    )

    output_file = (
        RECORDINGS_DIR / filename
    )

    # --------------------------------------------------------
    # OPEN SOURCE
    # --------------------------------------------------------

    camera, open_error = _open_camera_source(
        camera_type=normalized_type,
        device_index=device_index,
        rtsp_url=rtsp_url,
    )

    if camera is None:
        return (
            False,
            open_error or "Could not create camera object.",
        )

    if not camera.isOpened():
        camera.release()
        return (
            False,
            "Could not open camera or RTSP stream.",
        )

    # --------------------------------------------------------
    # READ FIRST FRAME
    # --------------------------------------------------------

    success, first_frame = camera.read()

    if not success or first_frame is None:
        camera.release()
        return (
            False,
            "Camera opened, but no video frame was received.",
        )

    # --------------------------------------------------------
    # CAMERA SETTINGS
    # --------------------------------------------------------

    width, height, fps = _get_video_settings(
        camera,
        first_frame=first_frame,
    )

    print(
        f"Recording settings: "
        f"{width}x{height} @ {fps:.2f} FPS"
    )

    # --------------------------------------------------------
    # CREATE OPENCV VIDEO WRITER
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(output_file),
        fourcc,
        fps,
        (width, height),
    )

    if not writer.isOpened():
        camera.release()
        return (
            False,
            "Could not create recording file.",
        )

    # --------------------------------------------------------
    # RECORDING INFORMATION
    # --------------------------------------------------------

    recording_info = {
        "camera_id": camera_id,
        "camera_type": normalized_type,
        "device_index": device_index,
        "rtsp_url": rtsp_url,
        "camera": camera,
        "writer": writer,
        "filename": filename,
        "output_file": output_file,
        "start_time": datetime.now(),
        "running": True,
        "first_frame": first_frame,
        "width": width,
        "height": height,
        "fps": fps,
    }

    # --------------------------------------------------------
    # STORE ACTIVE RECORDING
    # --------------------------------------------------------

    active_recordings[
        camera_id
    ] = recording_info

    # --------------------------------------------------------
    # START THREAD
    # --------------------------------------------------------

    recording_thread = threading.Thread(
        target=_record_camera,
        args=(camera_id,),
        daemon=True,
    )

    recording_info[
        "thread"
    ] = recording_thread

    recording_thread.start()

    print(
        f"Recording started for camera {camera_id} "
        f"({normalized_type})."
    )

    return (
        True,
        recording_info,
    )


# ============================================================
# RECORD CAMERA
# ============================================================

def _record_camera(
    camera_id: int
):
    recording = (
        active_recordings.get(
            camera_id
        )
    )

    if recording is None:
        return

    camera = recording[
        "camera"
    ]

    writer = recording[
        "writer"
    ]

    first_frame = recording.get(
        "first_frame"
    )

    frame_count = 0

    try:
        # Write the initial frame that was used to validate the
        # source and determine its dimensions.
        if first_frame is not None:
            frame = first_frame

            expected_size = (
                recording["width"],
                recording["height"],
            )

            if (
                frame.shape[1],
                frame.shape[0],
            ) != expected_size:
                frame = cv2.resize(
                    frame,
                    expected_size,
                )

            cv2.putText(
                frame,
                "SMART VIDEO MANAGEMENT SYSTEM",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                "RECORDING",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            writer.write(frame)
            frame_count += 1

        while recording[
            "running"
        ]:
            success, frame = (
                camera.read()
            )

            if not success or frame is None:
                print(
                    f"Camera {camera_id}: "
                    "Could not read frame."
                )
                break

            expected_size = (
                recording["width"],
                recording["height"],
            )

            if (
                frame.shape[1],
                frame.shape[0],
            ) != expected_size:
                frame = cv2.resize(
                    frame,
                    expected_size,
                )

            # ------------------------------------------------
            # ADD RECORDING TEXT
            # ------------------------------------------------

            cv2.putText(
                frame,
                "SMART VIDEO MANAGEMENT SYSTEM",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                "RECORDING",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # ------------------------------------------------
            # WRITE FRAME
            # ------------------------------------------------

            writer.write(frame)
            frame_count += 1

    except Exception as exc:
        print(
            f"Camera {camera_id}: recording thread error: "
            f"{exc}"
        )

    finally:
        camera.release()
        writer.release()

        print(
            f"Camera {camera_id}: recording thread stopped. "
            f"Frames written: {frame_count}"
        )


# ============================================================
# STOP RECORDING
# ============================================================

def stop_recording(
    camera_id: int
):
    recording = (
        active_recordings.get(
            camera_id
        )
    )

    if recording is None:
        return (
            False,
            "Camera is not recording.",
        )

    # --------------------------------------------------------
    # STOP THREAD
    # --------------------------------------------------------

    recording[
        "running"
    ] = False

    thread = recording[
        "thread"
    ]

    if thread.is_alive():
        thread.join(
            timeout=10
        )

    # --------------------------------------------------------
    # END TIME
    # --------------------------------------------------------

    end_time = datetime.now()

    start_time = recording[
        "start_time"
    ]

    duration = max(
        0,
        int(
            (
                end_time - start_time
            ).total_seconds()
        ),
    )

    # --------------------------------------------------------
    # ORIGINAL FILE
    # --------------------------------------------------------

    original_file = (
        recording[
            "output_file"
        ]
    )

    # --------------------------------------------------------
    # H.264 FILE
    # --------------------------------------------------------

    h264_filename = (
        original_file.stem
        + "_web.mp4"
    )

    h264_file = (
        RECORDINGS_DIR
        / h264_filename
    )

    # --------------------------------------------------------
    # CONVERT TO H.264
    # --------------------------------------------------------

    conversion_success = False

    if original_file.exists() and original_file.stat().st_size > 0:
        conversion_success = (
            convert_to_h264(
                original_file,
                h264_file,
            )
        )
    else:
        print(
            "Original recording file is missing or empty."
        )

    # --------------------------------------------------------
    # SELECT FINAL FILE
    # --------------------------------------------------------

    if conversion_success:
        final_filename = h264_filename

        # Remove original mp4 because browser-ready copy exists.
        if original_file.exists():
            try:
                original_file.unlink()
            except OSError as exc:
                print(
                    f"Could not remove original recording: {exc}"
                )

    else:
        print(
            "Keeping original recording "
            "because conversion failed."
        )

        final_filename = (
            original_file.name
        )

    # --------------------------------------------------------
    # REMOVE ACTIVE RECORDING
    # --------------------------------------------------------

    active_recordings.pop(
        camera_id,
        None,
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return (
        True,
        {
            "camera_id": camera_id,
            "filename": final_filename,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "format": (
                "H.264"
                if conversion_success
                else "mp4v"
            ),
            "camera_type": recording.get(
                "camera_type",
                "USB",
            ),
        },
    )
