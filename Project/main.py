# main.py
from camera import Camera
from analysis import AngleAnalyzer
import sound_utils
from gui_app import SquatApp

def main():
    cam = Camera(camera_index=0)

    # NOTE: hip_id MUST match one of your 4 ArUco marker IDs
    analyzer = AngleAnalyzer(
    hip_id=39,
    knee_id=40,
    ankle_id=42,
    floor_id1=41,
    floor_id2=38,
    require_all_markers=True
    )

    app = SquatApp(cam, analyzer, sound_utils, fps=30)
    app.mainloop()

if __name__ == "__main__":
    main()