# test_run.py
import cv2
from Project.camera import Camera
from Project.analysis import SquatAnalyzer

def main():
    cam = Camera(0)
    analyzer = SquatAnalyzer(
        hip_id=0,             # <-- deine Hip-Marker-ID eintragen
        top_threshold=200,    # <-- später kalibrieren
        bottom_threshold=350, # <-- später kalibrieren
        min_frames_below=2
    )

    while True:
        frame, markers = cam.get_frame_and_markers()
        if frame is None:
            break

        result = analyzer.update(markers)

        # Overlay-Info ins Bild
        cv2.putText(frame, f"Reps: {result.rep_count}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(frame, f"State: {result.state}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, result.status_text, (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Debug: welche Marker sind sichtbar?
        cv2.putText(frame, f"IDs: {list(markers.keys())}", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Squat Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()