import cv2


# ============================================================
# ENTER YOUR CAMERA RTSP URL HERE
# ============================================================

RTSP_URL = input("Enter RTSP URL: ").strip()


print()
print("Connecting to camera...")
print("RTSP URL:", RTSP_URL)


# ============================================================
# OPEN RTSP STREAM
# ============================================================

cap = cv2.VideoCapture(RTSP_URL)


# ============================================================
# CHECK CONNECTION
# ============================================================

if not cap.isOpened():

    print()
    print("ERROR: Could not open RTSP stream.")
    print("Check the RTSP URL, camera network, username/password,")
    print("and whether RTSP is enabled on the camera.")

    cap.release()

    exit()


print()
print("SUCCESS: RTSP stream opened!")


# ============================================================
# READ FIRST FRAME
# ============================================================

success, frame = cap.read()


if not success:

    print("ERROR: Connected to RTSP, but could not read a frame.")

    cap.release()

    exit()


print("SUCCESS: Video frame received!")

print("Frame width :", frame.shape[1])
print("Frame height:", frame.shape[0])


# ============================================================
# SAVE ONE TEST FRAME
# ============================================================

cv2.imwrite(
    "rtsp_test.jpg",
    frame
)

print()
print("Test frame saved as: rtsp_test.jpg")


# ============================================================
# CLOSE CAMERA
# ============================================================

cap.release()

print("Camera connection closed.")