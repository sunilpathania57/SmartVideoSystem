from time import sleep

import cv2


# ============================================================
# GENERATE CAMERA FRAMES
# ============================================================

def generate_camera_frames(
    camera_type: str,
    device_index: int | None = None,
    rtsp_url: str | None = None
):

    # --------------------------------------------------------
    # SELECT VIDEO SOURCE
    # --------------------------------------------------------

    if camera_type.upper() == "USB":

        if device_index is None:
            raise RuntimeError(
                "USB camera does not have a device index."
            )

        source = device_index

    elif camera_type.upper() == "IP":

        if not rtsp_url:
            raise RuntimeError(
                "IP camera does not have an RTSP URL."
            )

        source = rtsp_url

    else:

        raise RuntimeError(
            f"Unsupported camera type: {camera_type}"
        )


    # --------------------------------------------------------
    # OPEN CAMERA
    # --------------------------------------------------------

    camera = cv2.VideoCapture(source)

    if not camera.isOpened():

        raise RuntimeError(
            f"Could not open video source: {source}"
        )


    # --------------------------------------------------------
    # FRAME RATE
    # --------------------------------------------------------

    fps = camera.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 25

    frame_delay = 1 / fps


    try:

        while True:

            success, frame = camera.read()

            if not success:

                break


            # ------------------------------------------------
            # Add application information
            # ------------------------------------------------

            cv2.putText(
                frame,
                "SMART VIDEO MANAGEMENT SYSTEM",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                "LIVE",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


            # ------------------------------------------------
            # Convert to JPEG
            # ------------------------------------------------

            success, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            if not success:
                continue


            frame_bytes = buffer.tobytes()


            # ------------------------------------------------
            # Send MJPEG frame
            # ------------------------------------------------

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )


            sleep(frame_delay)


    finally:

        camera.release()