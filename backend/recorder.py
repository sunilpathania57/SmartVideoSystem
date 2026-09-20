from datetime import datetime
from pathlib import Path
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

        str(output_file)

    ]


    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )


    if result.returncode != 0:

        print(
            "FFmpeg conversion failed."
        )

        print(
            result.stderr
        )

        return False


    if not output_file.exists():

        print(
            "FFmpeg finished, but output "
            "file was not found."
        )

        return False


    print(
        "H.264 conversion successful."
    )

    return True


# ============================================================
# START RECORDING
# ============================================================

def start_recording(
    camera_id: int,
    device_index: int
):

    # --------------------------------------------------------
    # CHECK IF ALREADY RECORDING
    # --------------------------------------------------------

    if camera_id in active_recordings:

        return (
            False,
            "Camera is already recording."
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
    # OPEN CAMERA
    # --------------------------------------------------------

    print(
        f"Opening camera {device_index}..."
    )


    camera = cv2.VideoCapture(
        device_index,
        cv2.CAP_DSHOW
    )


    if not camera.isOpened():

        return (
            False,
            "Could not open camera."
        )


    # --------------------------------------------------------
    # CAMERA SETTINGS
    # --------------------------------------------------------

    width = 640
    height = 480
    fps = 20


    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        width
    )


    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        height
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

        (width, height)

    )


    if not writer.isOpened():

        camera.release()

        return (
            False,
            "Could not create recording file."
        )


    # --------------------------------------------------------
    # RECORDING INFORMATION
    # --------------------------------------------------------

    recording_info = {

        "camera_id":
            camera_id,

        "camera":
            camera,

        "writer":
            writer,

        "filename":
            filename,

        "output_file":
            output_file,

        "start_time":
            datetime.now(),

        "running":
            True

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

        daemon=True

    )


    recording_info[
        "thread"
    ] = recording_thread


    recording_thread.start()


    return (
        True,
        recording_info
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


    try:

        while recording[
            "running"
        ]:

            success, frame = (
                camera.read()
            )


            if not success:

                print(
                    f"Camera {camera_id}: "
                    "Could not read frame."
                )

                break


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

                2

            )


            cv2.putText(

                frame,

                "RECORDING",

                (20, 70),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 0, 255),

                2

            )


            # ------------------------------------------------
            # WRITE FRAME
            # ------------------------------------------------

            writer.write(
                frame
            )


    finally:

        camera.release()

        writer.release()


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
            "Camera is not recording."
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
            timeout=5
        )


    # --------------------------------------------------------
    # END TIME
    # --------------------------------------------------------

    end_time = datetime.now()


    start_time = recording[
        "start_time"
    ]


    duration = int(
        (
            end_time - start_time
        ).total_seconds()
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

    conversion_success = (
        convert_to_h264(
            original_file,
            h264_file
        )
    )


    # --------------------------------------------------------
    # SELECT FINAL FILE
    # --------------------------------------------------------

    if conversion_success:

        final_filename = (
            h264_filename
        )


        # Remove original mp4
        # because browser-ready copy exists.

        if original_file.exists():

            original_file.unlink()


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
        None
    )


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return (
        True,
        {

            "camera_id":
                camera_id,

            "filename":
                final_filename,

            "start_time":
                start_time,

            "end_time":
                end_time,

            "duration_seconds":
                duration,

            "format":
                (
                    "H.264"
                    if conversion_success
                    else "mp4v"
                )

        }
    )