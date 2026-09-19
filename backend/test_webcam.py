import cv2


# ============================================================
# OPEN LAPTOP CAMERA
# ============================================================

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("ERROR: Could not open laptop camera.")

    exit()


print("Laptop camera opened successfully!")
print("Press Q to quit.")


# ============================================================
# READ CAMERA FRAMES
# ============================================================

while True:

    success, frame = camera.read()

    if not success:

        print("ERROR: Could not read camera frame.")

        break


    # Show video
    cv2.imshow(
        "Smart Video System - Laptop Camera",
        frame
    )


    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLOSE CAMERA
# ============================================================

camera.release()

cv2.destroyAllWindows()

print("Camera closed.")