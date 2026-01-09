from logging import root
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2


class SquatApp(tk.Tk):
    """
    Tkinter GUI for angle measurement:
    - Displays live camera feed
    - Shows femur angle (w.r.t. floor) and knee angle
    - Start/Stop button (pauses processing but keeps showing frames)
    """

    def __init__(self, camera, analyzer, sound_module, fps: int = 30):
        super().__init__()
        self.title("Squat Angle Analyzer")
        self.camera = camera
        self.analyzer = analyzer
        self.sound_module = sound_module

        self.delay_ms = max(1, int(1000 / fps))
        self.running = True

        # --- Layout ---
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Video area
        self.video_label = ttk.Label(root)
        self.video_label.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Info labels (angles)
        self.femur_var = tk.StringVar(value="Femur angle: -")
        self.knee_var = tk.StringVar(value="Knee angle: -")
        self.status_var = tk.StringVar(value="Status: -")

        ttk.Label(root, textvariable=self.femur_var, font=("Arial", 16)).grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.knee_var, font=("Arial", 16)).grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.status_var, font=("Arial", 12)).grid(row=1, column=2, sticky="w", pady=(10, 0))

        self.rep_var = tk.StringVar(value="Reps: 0")

        ttk.Label(root, textvariable=self.rep_var, font=("Arial", 16)).grid(row=2, column=0, sticky="w", pady=(5, 0))


        # Controls 
        self.start_stop_btn = ttk.Button(root, text="Pause", command=self.toggle_running) 
        self.start_stop_btn.grid(row=3, column=0, sticky="w", pady=10) 
        self.reset_btn = ttk.Button(root, text="Reset Reps", command=self.reset_reps) 
        self.reset_btn.grid(row=3, column=1, sticky="w", pady=10) 
        self.quit_btn = ttk.Button(root, text="Quit", command=self.on_close) 
        self.quit_btn.grid(row=3, column=2, sticky="e", pady=10)


        # Stretching
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.rowconfigure(0, weight=1)

        # Close hook
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start loop
        self.after(self.delay_ms, self.update_loop)

    def toggle_running(self):
        self.running = not self.running
        self.start_stop_btn.config(text="Pause" if self.running else "Start")

    def reset_reps(self):
        self.analyzer.reset()
        self.rep_var.set("Reps: 0")
        self.status_var.set("Status: -")


    def update_loop(self):
        frame, markers = self.camera.get_frame_and_markers()

        if frame is not None:
            if self.running:
                result = self.analyzer.update(markers)

                                # Sound bei neuer Rep
                if result.new_rep:
                    self.sound_module.play_valid_squat_sound()

                self.rep_var.set(f"Reps: {result.rep_count}")
                


                # ---------- VECTOR VISUALIZATION ----------

                # Femur vector: Hip -> Knee
                hip_id = self.analyzer.hip_id
                knee_id = self.analyzer.knee_id

                if hip_id in markers and knee_id in markers:
                    hip = markers[hip_id]["center"]
                    knee = markers[knee_id]["center"]

                    hip = (int(hip[0]), int(hip[1]))
                    knee = (int(knee[0]), int(knee[1]))

                    # draw femur vector (green)
                    cv2.arrowedLine(
                        frame,
                        hip,
                        knee,
                        color=(0, 255, 0),
                        thickness=3,
                        tipLength=0.2
                    )
                    cv2.putText(frame, "Femur", hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # ---------- TIBIA VECTOR (Knee -> Ankle) ----------

                    knee_id = self.analyzer.knee_id
                    ankle_id = self.analyzer.ankle_id

                    if knee_id in markers and ankle_id in markers:
                        knee = markers[knee_id]["center"]
                        ankle = markers[ankle_id]["center"]

                        knee = (int(knee[0]), int(knee[1]))
                        ankle = (int(ankle[0]), int(ankle[1]))

                        # draw tibia vector (red)
                        cv2.arrowedLine(
                            frame,
                            knee,
                            ankle,
                            color=(0, 0, 255),
                            thickness=3,
                            tipLength=0.2
                        )

                        cv2.putText(
                            frame,
                            "Tibia",
                            knee,
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2
                        )


                # Floor vector: Floor1 -> Floor2 (if available)
                fid1 = self.analyzer.floor_id1
                fid2 = self.analyzer.floor_id2

                if fid1 is not None and fid2 is not None:
                    if fid1 in markers and fid2 in markers:
                        f1 = markers[fid1]["center"]
                        f2 = markers[fid2]["center"]

                        f1 = (int(f1[0]), int(f1[1]))
                        f2 = (int(f2[0]), int(f2[1]))

                        # draw floor vector (blue)
                        cv2.arrowedLine(
                            frame,
                            f1,
                            f2,
                            color=(255, 0, 0),
                            thickness=3,
                            tipLength=0.2
                        )
                        cv2.putText(frame, "Floor", f1,
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)


                if result.femur_angle_deg is not None:
                    self.femur_var.set(f"Femur angle: {result.femur_angle_deg:.1f}°")
                else:
                    self.femur_var.set("Femur angle: -")

                if result.knee_angle_deg is not None:
                    self.knee_var.set(f"Knee angle: {result.knee_angle_deg:.1f}°")
                else:
                    self.knee_var.set("Knee angle: -")

                self.status_var.set(f"Status: {result.status_text}")

                # show visible marker IDs
                cv2.putText(frame, f"IDs: {list(markers.keys())}", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            else:
                cv2.putText(frame, "PAUSED", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Convert BGR -> RGB for Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(self.delay_ms, self.update_loop)

    def on_close(self):
        try:
            self.camera.release()
        finally:
            self.destroy()
