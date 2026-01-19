# camera.py
import cv2
import numpy as np

class Camera:
    def __init__(self, camera_index=1):
        #open camera
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        # ArUco-Setup (wie im Beispiel: 6x6_250)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.parameters)

    def get_frame_and_markers(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, {}

        # Greyscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect aruko codes
        corners, ids, rejected = self.detector.detectMarkers(gray)

        markers = {}

        if ids is not None:
            # OpenCV expects ids as int32 with shape (N, 1) for drawing
            ids = ids.flatten().astype(np.int32)

            # Draw all detected markers once per frame (more stable than per-marker calls)
            cv2.aruco.drawDetectedMarkers(frame, corners, ids.reshape(-1, 1))

            for i, marker_id in enumerate(ids):
                pts = corners[i][0]         # shape (4, 2)
                cx = int(np.mean(pts[:, 0]))
                cy = int(np.mean(pts[:, 1]))

                markers[int(marker_id)] = {
                    "center": (cx, cy),
                    "corners": pts
                }

                # draw Markers center and id
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                cv2.putText(frame, str(marker_id), (cx, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return frame, markers

    def release(self):
        if self.cap.isOpened():
            self.cap.release()