# main.py
from camera import Camera
from analysis import SquatAnalyzer
import sound_utils
from gui_app import SquatApp

def main():
    cam = Camera(camera_index=0)

    # NOTE: hip_id MUST match one of your 4 ArUco marker IDs
    analyzer = SquatAnalyzer(
        hip_id=0,
        top_threshold=200,
        bottom_threshold=350,
        min_frames_below=2
    )

    app = SquatApp(cam, analyzer, sound_utils, fps=30)
    app.mainloop()

if __name__ == "__main__":
    main()