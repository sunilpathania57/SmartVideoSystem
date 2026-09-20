import time

from backend.recorder import (
    start_recording,
    stop_recording
)


# ============================================================
# TEST SETTINGS
# ============================================================

CAMERA_ID = 7
DEVICE_INDEX = 0
RECORDING_SECONDS = 10


# ============================================================
# START RECORDING
# ============================================================

print("Starting recording...")

success, result = start_recording(
    camera_id=CAMERA_ID,
    device_index=DEVICE_INDEX
)


if not success:

    print("Recording could not be started.")

    print("Reason:", result)

    exit(1)


print("Recording started successfully!")

print("Recording for 10 seconds...")


# ============================================================
# WAIT
# ============================================================

time.sleep(
    RECORDING_SECONDS
)


# ============================================================
# STOP RECORDING
# ============================================================

print("Stopping recording...")


success, result = stop_recording(
    CAMERA_ID
)


if not success:

    print("Recording could not be stopped.")

    print("Reason:", result)

    exit(1)


print()
print("Recording stopped successfully!")


# ============================================================
# DISPLAY RESULT
# ============================================================

print()
print("Recording information:")

print(
    "Camera ID:",
    result["camera_id"]
)

print(
    "Filename:",
    result["filename"]
)

print(
    "Start time:",
    result["start_time"]
)

print(
    "End time:",
    result["end_time"]
)

print(
    "Duration:",
    result["duration_seconds"],
    "seconds"
)