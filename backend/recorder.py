from datetime import datetime
from pathlib import Path
import math
import subprocess
import threading
import time

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
# RECORDING SETTINGS
# ============================================================

# Create a new recording file every 5 minutes.
SEGMENT_DURATION_SECONDS = 5 * 60

# Maximum time to wait for the recording thread to stop.
THREAD_JOIN_TIMEOUT_SECONDS = 10


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
        Uses the RTSP URL. FFmpeg backend is tried first,
        followed by OpenCV's default backend.
    """

    normalized_type = (
        str(camera_type or "USB").strip().upper()
    )

    if normalized_type == "USB":

        if device_index is None:
            return (
                None,
                "USB camera does not have a device index.",
            )

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
            return (
                None,
                "IP camera does not have an RTSP URL.",
            )

        print(
            f"Opening IP camera RTSP stream: {rtsp_url}"
        )

        # Prefer FFmpeg for RTSP.
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
                "FFmpeg backend could not open RTSP "
                f"stream: {exc}"
            )

        # Fallback.
        camera = cv2.VideoCapture(rtsp_url)

        return camera, None

    return (
        None,
        (
            f"Unsupported camera type "
            f"'{normalized_type}'. Use USB or IP."
        ),
    )


# ============================================================
# GET VIDEO SETTINGS
# ============================================================

def _get_video_settings(
    camera,
    first_frame=None,
):
    """
    Determine a usable frame size and FPS.

    RTSP cameras may report an invalid FPS, so a safe
    default is used.
    """

    if first_frame is not None:

        frame_height, frame_width = (
            first_frame.shape[:2]
        )

    else:

        frame_width = int(
            camera.get(
                cv2.CAP_PROP_FRAME_WIDTH
            ) or 0
        )

        frame_height = int(
            camera.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            ) or 0
        )

    if frame_width <= 0:
        frame_width = 640

    if frame_height <= 0:
        frame_height = 480

    fps_value = camera.get(
        cv2.CAP_PROP_FPS
    )

    try:
        fps = float(fps_value)
    except (TypeError, ValueError):
        fps = 20.0

    if (
        not math.isfinite(fps)
        or fps <= 1
        or fps > 120
    ):
        fps = 20.0

    return (
        frame_width,
        frame_height,
        fps,
    )


# ============================================================
# CREATE SEGMENT WRITER
# ============================================================

def _create_segment(
    recording,
    segment_number: int,
    start_time: datetime,
):
    """
    Create a new raw MP4 file for one recording segment.
    """

    camera_id = recording["camera_id"]

    filename = (
        f"camera_{camera_id}_"
        f"{recording['session_timestamp']}_"
        f"part{segment_number:02d}.mp4"
    )

    output_file = RECORDINGS_DIR / filename

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(output_file),
        fourcc,
        recording["fps"],
        (
            recording["width"],
            recording["height"],
        ),
    )

    if not writer.isOpened():

        return (
            None,
            None,
            (
                "Could not create recording "
                f"segment file: {filename}"
            ),
        )

    segment = {
        "segment_number": segment_number,
        "filename": filename,
        "output_file": output_file,
        "start_time": start_time,
        "end_time": None,
        "duration_seconds": 0,
        "frame_count": 0,
    }

    print()
    print(
        f"Started segment {segment_number} "
        f"for camera {camera_id}: {filename}"
    )

    return (
        writer,
        segment,
        None,
    )


# ============================================================
# FINALIZE SEGMENT FILE
# ============================================================

def _finalize_segment_file(segment):
    """
    Convert one completed raw segment to browser-compatible H.264.

    The returned segment contains the FINAL filename that should be
    stored in PostgreSQL.
    """

    raw_file = Path(segment["output_file"])

    h264_filename = (
        raw_file.stem
        + "_web.mp4"
    )

    h264_file = (
        RECORDINGS_DIR
        / h264_filename
    )

    conversion_success = False

    if (
        raw_file.exists()
        and raw_file.stat().st_size > 0
    ):

        conversion_success = (
            convert_to_h264(
                raw_file,
                h264_file,
            )
        )

    else:

        print(
            "Segment file is missing or empty: "
            f"{raw_file}"
        )

    if conversion_success:

        final_filename = h264_filename
        final_file = h264_file
        final_format = "H.264"

        try:

            if raw_file.exists():
                raw_file.unlink()

        except OSError as exc:

            print(
                "Could not remove raw segment: "
                f"{exc}"
            )

    else:

        final_filename = raw_file.name
        final_file = raw_file
        final_format = "mp4v"

        print(
            "Keeping raw segment because H.264 "
            "conversion failed."
        )

    finalized = dict(segment)

    finalized["filename"] = final_filename
    finalized["final_filename"] = final_filename
    finalized["final_file"] = final_file
    finalized["format"] = final_format

    return finalized


# ============================================================
# CLOSE CURRENT SEGMENT
# ============================================================

def _close_current_segment(
    recording,
    end_time: datetime | None = None,
):
    """
    Close the current segment, finalize the file, and then
    notify the application/database callback with the FINAL
    filename.
    """

    writer = recording.get(
        "writer"
    )

    segment = recording.get(
        "current_segment"
    )

    if writer is not None:

        try:

            writer.release()

        except Exception as exc:

            print(
                "Error releasing segment writer: "
                f"{exc}"
            )

    recording["writer"] = None

    if segment is None:

        recording["current_segment"] = None
        return None

    if segment["end_time"] is None:

        segment["end_time"] = (
            end_time or datetime.now()
        )

    segment["duration_seconds"] = max(
        0,
        int(
            (
                segment["end_time"]
                - segment["start_time"]
            ).total_seconds()
        ),
    )

    print(
        f"Closed segment "
        f"{segment['segment_number']} "
        f"for camera "
        f"{recording['camera_id']} "
        f"({segment['duration_seconds']} sec, "
        f"{segment['frame_count']} frames)"
    )

    # Finalize the file BEFORE database callback.
    finalized_segment = _finalize_segment_file(
        segment
    )

    recording["segments"].append(
        finalized_segment
    )

    # Save the FINAL filename to PostgreSQL.
    if finalized_segment["frame_count"] > 0:

        callback = recording.get(
            "on_segment_ready"
        )

        if callback is not None:

            try:

                callback(
                    dict(finalized_segment)
                )

            except Exception as exc:

                print(
                    "Segment database callback failed: "
                    f"{exc}"
                )

    recording["current_segment"] = None

    return finalized_segment


# ============================================================
# START RECORDING
# ============================================================

def start_recording(
    camera_id: int,
    device_index: int | None = None,
    camera_type: str = "USB",
    rtsp_url: str | None = None,
    on_segment_ready=None,
):
    """
    Start background recording.

    Backwards compatible with:
        start_recording(camera_id, device_index)

    IP camera:
        start_recording(
            camera_id,
            camera_type="IP",
            rtsp_url="rtsp://..."
        )

    Recordings are automatically split into 5-minute
    segments.
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
    # CREATE SESSION TIMESTAMP
    # --------------------------------------------------------

    session_timestamp = (
        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
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
            open_error
            or "Could not create camera object.",
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
            (
                "Camera opened, but no video frame "
                "was received."
            ),
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
    # RECORDING INFORMATION
    # --------------------------------------------------------

    recording_info = {
        "camera_id": camera_id,
        "camera_type": normalized_type,
        "device_index": device_index,
        "rtsp_url": rtsp_url,
        "camera": camera,
        "writer": None,
        "current_segment": None,
        "segments": [],
        "session_timestamp": session_timestamp,
        "start_time": datetime.now(),
        "running": True,
        "first_frame": first_frame,
        "width": width,
        "height": height,
        "fps": fps,
        "segment_number": 1,
        "on_segment_ready": on_segment_ready,
    }

    # --------------------------------------------------------
    # CREATE FIRST SEGMENT
    # --------------------------------------------------------

    writer, segment, segment_error = (
        _create_segment(
            recording_info,
            segment_number=1,
            start_time=recording_info["start_time"],
        )
    )

    if writer is None:

        camera.release()

        return (
            False,
            segment_error
            or "Could not create recording segment.",
        )

    recording_info["writer"] = writer

    recording_info["current_segment"] = (
        segment
    )

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
        f"Recording started for camera "
        f"{camera_id} ({normalized_type})."
    )

    return (
        True,
        recording_info,
    )


# ============================================================
# WRITE FRAME OVERLAY
# ============================================================

def _add_recording_overlay(frame):

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

    return frame


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

    first_frame = recording.get(
        "first_frame"
    )

    frame_count = 0

    # Monotonic clock is used for reliable segment timing.
    segment_started_monotonic = (
        time.monotonic()
    )

    try:

        # ----------------------------------------------------
        # WRITE FIRST FRAME
        # ----------------------------------------------------

        if first_frame is not None:

            frame = first_frame.copy()

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

            frame = _add_recording_overlay(
                frame
            )

            writer = recording.get(
                "writer"
            )

            if writer is not None:

                writer.write(frame)

                frame_count += 1

                current_segment = (
                    recording.get(
                        "current_segment"
                    )
                )

                if current_segment:
                    current_segment[
                        "frame_count"
                    ] += 1

        recording["first_frame"] = None

        # ----------------------------------------------------
        # RECORD LOOP
        # ----------------------------------------------------

        while recording[
            "running"
        ]:

            # ------------------------------------------------
            # SEGMENT CHECK
            # ------------------------------------------------

            elapsed = (
                time.monotonic()
                - segment_started_monotonic
            )

            if (
                elapsed >=
                SEGMENT_DURATION_SECONDS
            ):

                now = datetime.now()

                _close_current_segment(
                    recording,
                    end_time=now,
                )

                if not recording[
                    "running"
                ]:
                    break

                recording[
                    "segment_number"
                ] += 1

                writer, segment, segment_error = (
                    _create_segment(
                        recording,
                        segment_number=
                            recording[
                                "segment_number"
                            ],
                        start_time=now,
                    )
                )

                if writer is None:

                    print(
                        f"Camera {camera_id}: "
                        f"Could not start next "
                        f"segment: {segment_error}"
                    )

                    recording[
                        "running"
                    ] = False

                    break

                recording[
                    "writer"
                ] = writer

                recording[
                    "current_segment"
                ] = segment

                segment_started_monotonic = (
                    time.monotonic()
                )

            # ------------------------------------------------
            # READ FRAME
            # ------------------------------------------------

            success, frame = (
                camera.read()
            )

            if (
                not success
                or frame is None
            ):

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
            # ADD OVERLAY
            # ------------------------------------------------

            frame = _add_recording_overlay(
                frame
            )

            # ------------------------------------------------
            # WRITE FRAME
            # ------------------------------------------------

            writer = recording.get(
                "writer"
            )

            if writer is None:
                break

            writer.write(frame)

            frame_count += 1

            current_segment = (
                recording.get(
                    "current_segment"
                )
            )

            if current_segment:

                current_segment[
                    "frame_count"
                ] += 1

    except Exception as exc:

        print(
            f"Camera {camera_id}: "
            f"recording thread error: {exc}"
        )

    finally:

        # Close the currently open segment.
        _close_current_segment(
            recording,
            end_time=datetime.now(),
        )

        recording[
            "running"
        ] = False

        camera.release()

        print(
            f"Camera {camera_id}: "
            "recording thread stopped. "
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
            timeout=THREAD_JOIN_TIMEOUT_SECONDS
        )

    # --------------------------------------------------------
    # ENSURE CURRENT SEGMENT IS CLOSED
    # --------------------------------------------------------

    if recording.get(
        "current_segment"
    ) is not None:

        _close_current_segment(
            recording,
            end_time=datetime.now(),
        )

    # --------------------------------------------------------
    # ENSURE CAMERA/WRITER ARE RELEASED
    # --------------------------------------------------------

    writer = recording.get(
        "writer"
    )

    if writer is not None:

        try:

            writer.release()

        except Exception:
            pass

        recording["writer"] = None

    camera = recording.get(
        "camera"
    )

    if camera is not None:

        try:

            camera.release()

        except Exception:
            pass

    # --------------------------------------------------------
    # END TIME / TOTAL DURATION
    # --------------------------------------------------------

    end_time = datetime.now()

    start_time = recording[
        "start_time"
    ]

    duration = max(
        0,
        int(
            (
                end_time
                - start_time
            ).total_seconds()
        ),
    )

    # --------------------------------------------------------
    # ALL SEGMENTS HAVE ALREADY BEEN FINALIZED
    # --------------------------------------------------------

    final_segments = []

    for segment in recording.get(
        "segments",
        [],
    ):

        final_segments.append(
            {
                "segment_number":
                    segment["segment_number"],

                "filename":
                    segment["filename"],

                "start_time":
                    segment["start_time"],

                "end_time":
                    segment["end_time"],

                "duration_seconds":
                    segment["duration_seconds"],

                "frame_count":
                    segment["frame_count"],

                "format":
                    segment.get(
                        "format",
                        "mp4v",
                    ),
            }
        )

    # --------------------------------------------------------
    # REMOVE ACTIVE RECORDING
    # --------------------------------------------------------

    active_recordings.pop(
        camera_id,
        None,
    )

    # --------------------------------------------------------
    # BACKWARD-COMPATIBLE RESULT
    # --------------------------------------------------------

    last_segment = (
        final_segments[-1]
        if final_segments
        else None
    )

    if last_segment:

        final_filename = (
            last_segment["filename"]
        )

        final_format = (
            last_segment["format"]
        )

    else:

        final_filename = None
        final_format = "unknown"

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

            "format": final_format,

            "camera_type": recording.get(
                "camera_type",
                "USB",
            ),

            "segments": final_segments,

            "segment_duration_seconds":
                SEGMENT_DURATION_SECONDS,
        },
    )
