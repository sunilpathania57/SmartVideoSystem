import threading
import time

import cv2


# ============================================================
# SHARED CAMERA MANAGER
# ============================================================

class CameraStream:

    def __init__(
        self,
        camera_type: str,
        device_index: int | None = None,
        rtsp_url: str | None = None,
    ):

        self.camera_type = (
            str(camera_type or "USB")
            .strip()
            .upper()
        )

        self.device_index = device_index
        self.rtsp_url = rtsp_url

        self.capture = None

        self.running = False

        self.thread = None

        self.lock = threading.Lock()

        self.latest_frame = None

        self.width = 0
        self.height = 0
        self.fps = 20.0

        self.error = None

    # --------------------------------------------------------
    # OPEN CAMERA
    # --------------------------------------------------------

    def open(self):

        if self.capture is not None:
            return True

        if self.camera_type == "USB":

            if self.device_index is None:
                self.error = (
                    "USB camera does not have "
                    "a device index."
                )
                return False

            print(
                f"CameraManager: opening USB "
                f"camera device {self.device_index}"
            )

            self.capture = cv2.VideoCapture(
                int(self.device_index),
                cv2.CAP_DSHOW,
            )

        elif self.camera_type == "IP":

            if not self.rtsp_url:
                self.error = (
                    "IP camera does not have "
                    "an RTSP URL."
                )
                return False

            print(
                "CameraManager: opening IP "
                "camera stream"
            )

            self.capture = cv2.VideoCapture(
                self.rtsp_url,
                cv2.CAP_FFMPEG,
            )

            if not self.capture.isOpened():

                self.capture.release()

                self.capture = cv2.VideoCapture(
                    self.rtsp_url
                )

        else:

            self.error = (
                f"Unsupported camera type: "
                f"{self.camera_type}"
            )

            return False

        if self.capture is None:
            self.error = "Could not create camera."
            return False

        if not self.capture.isOpened():

            self.capture.release()
            self.capture = None

            self.error = (
                "Could not open camera."
            )

            return False

        # ----------------------------------------------------
        # CAMERA SETTINGS
        # ----------------------------------------------------

        self.width = int(
            self.capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        self.height = int(
            self.capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        detected_fps = self.capture.get(
            cv2.CAP_PROP_FPS
        )

        if detected_fps > 0:
            self.fps = detected_fps

        print(
            "CameraManager: "
            f"{self.width}x{self.height} "
            f"@ {self.fps:.2f} FPS"
        )

        return True

    # --------------------------------------------------------
    # START CAPTURE THREAD
    # --------------------------------------------------------

    def start(self):

        if self.running:
            return True

        if not self.open():
            return False

        self.running = True

        self.thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
        )

        self.thread.start()

        print(
            "CameraManager: capture thread "
            "started."
        )

        return True

    # --------------------------------------------------------
    # CAPTURE LOOP
    # --------------------------------------------------------

    def _capture_loop(self):

        consecutive_failures = 0

        while self.running:

            success, frame = (
                self.capture.read()
            )

            if not success or frame is None:

                consecutive_failures += 1

                if (
                    consecutive_failures == 1
                    or
                    consecutive_failures % 10 == 0
                ):

                    print(
                        "CameraManager: "
                        f"frame read failure "
                        f"{consecutive_failures}"
                    )

                time.sleep(0.05)

                continue

            consecutive_failures = 0

            with self.lock:

                self.latest_frame = (
                    frame.copy()
                )

        print(
            "CameraManager: capture loop "
            "stopped."
        )

    # --------------------------------------------------------
    # GET LATEST FRAME
    # --------------------------------------------------------

    def get_frame(self):

        with self.lock:

            if self.latest_frame is None:
                return None

            return self.latest_frame.copy()

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    def stop(self):

        self.running = False

        if (
            self.thread is not None
            and self.thread.is_alive()
        ):

            self.thread.join(
                timeout=2
            )

        self.thread = None

        if self.capture is not None:

            self.capture.release()

            self.capture = None

        with self.lock:

            self.latest_frame = None

        print(
            "CameraManager: camera stopped."
        )


# ============================================================
# CAMERA REGISTRY
# ============================================================

_camera_streams = {}

_registry_lock = threading.Lock()


def get_camera_stream(
    camera_id: int,
    camera_type: str,
    device_index: int | None = None,
    rtsp_url: str | None = None,
):

    with _registry_lock:

        stream = _camera_streams.get(
            camera_id
        )

        if stream is None:

            stream = CameraStream(
                camera_type=camera_type,
                device_index=device_index,
                rtsp_url=rtsp_url,
            )

            _camera_streams[
                camera_id
            ] = stream

        return stream


def remove_camera_stream(
    camera_id: int
):

    with _registry_lock:

        stream = _camera_streams.pop(
            camera_id,
            None
        )

    if stream is not None:
        stream.stop()