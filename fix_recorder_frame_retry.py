from pathlib import Path
import shutil

BASE = Path(r"D:\SmartVideoSystem")
REC = BASE / "backend" / "recorder.py"

if not REC.exists():
    raise SystemExit(f"Recorder file not found: {REC}")

backup = BASE / "backend" / "recorder.py.before_frame_retry"
shutil.copy2(REC, backup)

text = REC.read_text(encoding="utf-8")

old_settings = '''THREAD_JOIN_TIMEOUT_SECONDS = 10
'''

new_settings = '''THREAD_JOIN_TIMEOUT_SECONDS = 10

# A camera can occasionally return a temporary failed frame.
# Do not stop a long recording because of one bad frame.
MAX_CONSECUTIVE_FRAME_FAILURES = 30

# Small delay between frame-read retries.
FRAME_RETRY_DELAY_SECONDS = 0.10
'''

if old_settings not in text:
    raise SystemExit(
        "Could not find THREAD_JOIN_TIMEOUT_SECONDS in recorder.py. "
        "No changes were made."
    )

if "MAX_CONSECUTIVE_FRAME_FAILURES" not in text:
    text = text.replace(old_settings, new_settings, 1)

old_block = '''            success, frame = (
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
'''

new_block = '''            success, frame = (
                camera.read()
            )

            # ------------------------------------------------
            # TEMPORARY FRAME-READ FAILURE RECOVERY
            # ------------------------------------------------
            #
            # A camera may occasionally fail to deliver one
            # frame. The old code stopped recording immediately.
            # Retry temporary failures instead.
            # ------------------------------------------------

            if (
                not success
                or frame is None
            ):

                consecutive_failures = recording.get(
                    "consecutive_frame_failures",
                    0
                ) + 1

                recording[
                    "consecutive_frame_failures"
                ] = consecutive_failures

                if (
                    consecutive_failures == 1
                    or
                    consecutive_failures % 5 == 0
                ):

                    print(
                        f"Camera {camera_id}: "
                        f"temporary frame read failure "
                        f"{consecutive_failures}/"
                        f"{MAX_CONSECUTIVE_FRAME_FAILURES}"
                    )

                if (
                    consecutive_failures
                    >= MAX_CONSECUTIVE_FRAME_FAILURES
                ):

                    print(
                        f"Camera {camera_id}: "
                        "camera frame read failed too many "
                        "times. Stopping recording."
                    )

                    break

                time.sleep(
                    FRAME_RETRY_DELAY_SECONDS
                )

                continue

            # A good frame was received. Reset the counter.
            if recording.get(
                "consecutive_frame_failures",
                0
            ) > 0:

                print(
                    f"Camera {camera_id}: "
                    "frame read recovered."
                )

            recording[
                "consecutive_frame_failures"
            ] = 0
'''

if old_block not in text:
    raise SystemExit(
        "Could not find the camera.read() failure block in recorder.py. "
        "No changes were made."
    )

text = text.replace(old_block, new_block, 1)

REC.write_text(text, encoding="utf-8")

print("SUCCESS")
print(f"Updated: {REC}")
print(f"Backup : {backup}")
print()
print("The recorder now retries temporary frame-read failures.")
print("It stops only after 30 consecutive failed reads.")
print("No database schema or frontend files were changed.")
