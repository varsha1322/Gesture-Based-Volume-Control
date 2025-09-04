import cv2
import HandTrackingModule as htm  # Ensure this module exists and is implemented correctly
import time
import numpy as np
from datetime import datetime
import absl.logging
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Suppress TensorFlow Lite logs
absl.logging.set_verbosity(absl.logging.ERROR)

# Camera resolution
wCam, hCam = 640, 480

# Initialize webcam
cap = None
for index in range(0, 5):  # Try indices 0 to 4
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        print(f"Webcam successfully accessed with index {index}.")
        break
else:
    print("Error: No webcam detected. Please check your connections or device settings.")
    exit()

cap.set(3, wCam)  # Set width
cap.set(4, hCam)  # Set height

# Initialize hand detector
try:
    detector = htm.handDetector(detectionCon=0.7, trackCon=0.7)
except Exception as e:
    print(f"Error initializing HandTrackingModule: {e}")
    cap.release()
    exit()

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume.iid, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
volRange = volume.GetVolumeRange()  # Get volume range
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

while True:
    # Capture a frame
    success, img = cap.read()
    if not success:
        print("Error: Could not read a frame from the webcam.")
        break

    try:
        # Process the frame with the hand detector
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img, draw=False)
        
        # Print landmark list
        if len(lmList) != 0:
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Draw circles with orange color (BGR)
            cv2.circle(img, (x1, y1), 15, (0, 165, 255), cv2.FILLED)  # Orange circle
            cv2.circle(img, (x2, y2), 15, (0, 165, 255), cv2.FILLED)  # Orange circle
            cv2.line(img, (x1, y1), (x2, y2), (0, 165, 255), 3)  # Line between points with orange
            cv2.circle(img, (cx, cy), 15, (0, 165, 255), cv2.FILLED)  # Orange circle

            length = math.hypot(x2 - x1, y2 - y1)

            # Hand range 50 - 300
            # Volume Range -96 - 0
            vol = np.interp(length, [50, 300], [minVol, maxVol])
            volBar = np.interp(length, [50, 300], [400, 150])
            volPer = np.interp(length, [50, 300], [0, 100])
            volume.SetMasterVolumeLevel(vol, None)

            if length < 50:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

        # Draw Volume Bar with dark blue inside and dark blue border
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)  # Dark Blue border
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)  # Dark Blue inside
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    except Exception as e:
        print(f"Error processing the frame: {e}")
        break

    # Overlay current time on the frame
    current_time = datetime.now().strftime('%H:%M:%S')
    cv2.putText(img, f'Time: {current_time}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display the webcam feed
    cv2.imshow("Webcam Feed", img)

    # Exit program on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting program.")
        break

cap.release()
cv2.destroyAllWindows()
