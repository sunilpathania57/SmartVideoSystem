import cv2
import numpy as np


# ------------------------------------------------------------
# VIDEO SETTINGS
# ------------------------------------------------------------

WIDTH = 640
HEIGHT = 360
FPS = 25
DURATION_SECONDS = 10

OUTPUT_FILE = "test_video.mp4"


# ------------------------------------------------------------
# CREATE VIDEO WRITER
# ------------------------------------------------------------

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

video = cv2.VideoWriter(
    OUTPUT_FILE,
    fourcc,
    FPS,
    (WIDTH, HEIGHT)
)


# ------------------------------------------------------------
# CREATE FRAMES
# ------------------------------------------------------------

total_frames = FPS * DURATION_SECONDS


for frame_number in range(total_frames):

    # Create a black frame
    frame = np.zeros(
        (HEIGHT, WIDTH, 3),
        dtype=np.uint8
    )


    # Moving square position
    x = (frame_number * 5) % (WIDTH - 100)
    y = 130


    # Draw moving square
    cv2.rectangle(
        frame,
        (x, y),
        (x + 100, y + 100),
        (0, 255, 0),
        -1
    )


    # Add project title
    cv2.putText(
        frame,
        "SMART VIDEO MANAGEMENT SYSTEM",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )


    # Add frame number
    cv2.putText(
        frame,
        f"Frame: {frame_number}",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # Write frame
    video.write(frame)


# ------------------------------------------------------------
# CLOSE VIDEO
# ------------------------------------------------------------

video.release()

print(f"Test video created: {OUTPUT_FILE}")