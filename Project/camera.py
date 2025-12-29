# camera.py
import cv2
import numpy as np

class Camera:
    def __init__(self, camera_index=0):
        #open camera
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        # ArUco-Setup (wie im Beispiel: 6x6_250)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.parameters)

    def get_frame_and_markers(self):
        """reads picture and detects aruko code.

        Returns:
            frame: BGR-Frame (np.ndarray) or None, if no Frame.
            markers: dict {marker_id: {"center": (cx, cy), "corners": corners_4x2}}
        """
        ret, frame = self.cap.read()
        if not ret:
            return None, {}

        # Greyscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect aruko codes
        corners, ids, rejected = self.detector.detectMarkers(gray)

        markers = {}

        if ids is not None:
            ids = ids.flatten()
            for i, marker_id in enumerate(ids):
                pts = corners[i][0]         # shape (4, 2)
                cx = int(np.mean(pts[:, 0]))
                cy = int(np.mean(pts[:, 1]))

                markers[int(marker_id)] = {
                    "center": (cx, cy),
                    "corners": pts
                }

                # Optional: Marker ins Bild einzeichnen
                cv2.aruco.drawDetectedMarkers(frame, [corners[i]], np.array([[marker_id]]))
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                cv2.putText(frame, str(marker_id), (cx, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return frame, markers

    def release(self):
        if self.cap.isOpened():
            self.cap.release()