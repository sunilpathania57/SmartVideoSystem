from datetime import datetime
from pathlib import Path

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
# CAMERA SETTINGS
# ============================================================

CAMERA_INDEX = 0

WIDTH = 640
HEIGHT = 480

FPS = 20

RECORDING_SECONDS = 10


# ============================================================
# OPEN CAMERA
# ============================================================

print("Opening laptop camera...")

camera = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)


if not camera.isOpened():

    print("ERROR: Could not open laptop camera.")

    exit(1)


# ============================================================
# SET CAMERA RESOLUTION
# ============================================================

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    WIDTH
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    HEIGHT
)


# ============================================================
# CREATE RECORDING FILE NAME
# ============================================================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)


filename = (
    f"camera_{CAMERA_INDEX}_{timestamp}.mp4"
)


output_file = (
    RECORDINGS_DIR / filename
)


print(
    f"Recording file: {output_file}"
)


# ============================================================
# CREATE VIDEO WRITER
# ============================================================

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)


video_writer = cv2.VideoWriter(

    str(output_file),

    fourcc,

    FPS,

    (WIDTH, HEIGHT)

)


if not video_writer.isOpened():

    print("ERROR: Could not create MP4 file.")

    camera.release()

    exit(1)


# ============================================================
# RECORDING
# ============================================================

print()
print(
    f"Recording for {RECORDING_SECONDS} seconds..."
)


total_frames = (
    FPS * RECORDING_SECONDS
)


frames_written = 0


for frame_number in range(
    total_frames
):

    success, frame = camera.read()


    # --------------------------------------------------------
    # CHECK FRAME
    # --------------------------------------------------------

    if not success:

        print(
            f"ERROR: Could not read frame "
            f"{frame_number}."
        )

        break


    # --------------------------------------------------------
    # ADD TEXT
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # WRITE FRAME
    # --------------------------------------------------------

    video_writer.write(
        frame
    )


    frames_written += 1


# ============================================================
# RELEASE
# ============================================================

camera.release()

video_writer.release()


# ============================================================
# FINAL RESULT
# ============================================================

print()


if frames_written == 0:

    print(
        "Recording FAILED: no frames were written."
    )

    # Delete empty/broken file
    if output_file.exists():

        output_file.unlink()

else:

    print(
        "Recording completed successfully!"
    )

    print(
        f"Frames written: {frames_written}"
    )

    print(
        f"Saved file: {output_file}"
    )