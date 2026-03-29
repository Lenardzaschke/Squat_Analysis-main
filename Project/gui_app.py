# Simple Tkinter GUI for squat analysis
# Shows camera image, joint angles and live plots
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import sound_utils
from plot_angle import KneeAngleDashboard, FemurAngleDashboard, BarHeightDashboard

class SquatApp(tk.Tk):
    def __init__(self, camera, analyzer, sound_utils, fps: int = 30):
        super().__init__()
        self.title("Squat Angle Analyzer")
        self.camera = camera
        self.analyzer = analyzer
        self.sound_module = sound_utils

        self.delay_ms = max(1, int(1000 / fps))
        self.running = True

        # main layout
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # camera image
        self.video_label = ttk.Label(root)
        self.video_label.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # angle text display
        self.femur_var = tk.StringVar(value="Femur angle: -")
        self.knee_var = tk.StringVar(value="Knee angle: -")
        self.status_var = tk.StringVar(value="Status: -")

        ttk.Label(root, textvariable=self.femur_var, font=("Arial", 16)).grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.knee_var, font=("Arial", 16)).grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.status_var, font=("Arial", 12)).grid(row=1, column=2, sticky="w", pady=(10, 0))

        self.rep_var = tk.StringVar(value="Reps: 0")

        ttk.Label(root, textvariable=self.rep_var, font=("Arial", 16)).grid(row=2, column=0, sticky="w", pady=(5, 0))

        # simple angle bars (femur / knee)
        self.bar_canvas = tk.Canvas(root, width=260, height=140, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.bar_canvas.grid(row=2, column=1, columnspan=2, sticky="w", pady=(5, 0))

        self._bar_base_y = 120
        self._bar_max_h = 100

        # bar graphics
        self.femur_bar_rect = self.bar_canvas.create_rectangle(40, self._bar_base_y, 100, self._bar_base_y, fill="#4AA3DF", outline="")
        self.knee_bar_rect = self.bar_canvas.create_rectangle(150, self._bar_base_y, 210, self._bar_base_y, fill="#F39C12", outline="")

        # Labels
        self.bar_canvas.create_text(70, 130, text="Femur", anchor="n", fill="#000000")
        self.bar_canvas.create_text(180, 130, text="Knee", anchor="n", fill="#000000")

        # Value text
        self.femur_bar_text = self.bar_canvas.create_text(
            70, 10, text="-", anchor="n", fill="#000000"
        )
        self.knee_bar_text = self.bar_canvas.create_text(
            180, 10, text="-", anchor="n", fill="#000000"
        )

        # separate live plots
        self.knee_dashboard = KneeAngleDashboard(self, max_points=300, refresh_ms=100)
        self.femur_dashboard = FemurAngleDashboard(self, max_points=300, refresh_ms=100)
        self.bar_height_dashboard = BarHeightDashboard(self, max_points=300, refresh_ms=100)

        # control buttons
        self.start_stop_btn = ttk.Button(root, text="Pause", command=self.toggle_running) 
        self.start_stop_btn.grid(row=3, column=0, sticky="w", pady=10) 
        self.reset_btn = ttk.Button(root, text="Reset Reps", command=self.reset_reps) 
        self.reset_btn.grid(row=3, column=1, sticky="w", pady=10) 
        self.quit_btn = ttk.Button(root, text="Quit", command=self.on_close) 
        self.quit_btn.grid(row=3, column=2, sticky="e", pady=10)
        self.show_plot_btn = ttk.Button(root, text="Show Knee Plot", command=self.knee_dashboard.show)
        self.show_plot_btn.grid(row=4, column=0, sticky="w", pady=5)
        self.show_femur_plot_btn = ttk.Button(root, text="Show Femur Plot", command=self.femur_dashboard.show)
        self.show_femur_plot_btn.grid(row=4, column=1, sticky="w", pady=5)
        self.show_bar_height_plot_btn = ttk.Button(root, text="Show Bar Height Plot", command=self.bar_height_dashboard.show)
        self.show_bar_height_plot_btn.grid(row=4, column=2, sticky="w", pady=5)


        # grid resizing
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.rowconfigure(0, weight=1)

        # handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # start update loop
        self.after(self.delay_ms, self.update_loop)

      
    def _resize_to_fit(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        if max_w <= 0 or max_h <= 0:
            return img
        w, h = img.size
        if w <= 0 or h <= 0:
            return img
        scale = min(max_w / w, max_h / h)
        # If the label is larger, we keep original size to avoid unnecessary upscaling.
        if scale >= 1.0:
            return img
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

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
                res = self.analyzer.update(markers)
                if res.knee_angle_deg is not None and res.femur_angle_deg is not None:
                    self.knee_dashboard.add_sample(res.knee_angle_deg)
                    self.femur_dashboard.add_sample(res.femur_angle_deg)
                # Bar height (relative to floor marker) from analysis
                if getattr(res, "bar_height_px", None) is not None:
                    self.bar_height_dashboard.add_sample(res.bar_height_px)

                # Sound when depth is reached
                if getattr(res, "new_depth", False):
                    self.sound_module.play_valid_squat_sound()

                self.rep_var.set(f"Reps: {res.rep_count}")



                # draw body vectors

                # femur vector (hip -> knee)
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
                    
                    # tibia vector (knee -> ankle)

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


                # floor reference (marker or image bottom)
                h, w = frame.shape[:2]
                y_floor = h - 5
                floor_id = getattr(self.analyzer, "floor_id", None)
                if floor_id is not None and floor_id in markers:
                    y_floor = int(markers[floor_id]["center"][1])

                cv2.line(frame, (0, y_floor), (w, y_floor), (255, 0, 0), 3)
                cv2.putText(frame, "Floor(ref)", (10, max(15, y_floor - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # bar height visualization (line only)
                bar_height_px = getattr(res, "bar_height_px", None)

                bar_id = getattr(self.analyzer, "bar_id", None)
                if bar_id is not None and bar_id in markers:
                    bar_y = int(markers[bar_id]["center"][1])
                    bx = int(markers[bar_id]["center"][0])
                    cv2.line(frame, (bx, bar_y), (bx, y_floor), (255, 255, 255), 2)
                    cv2.putText(frame, "Bar", (bx + 5, bar_y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


                if res.femur_angle_deg is not None:
                    self.femur_var.set(f"Femur angle: {res.femur_angle_deg:.1f}°")
                else:
                    self.femur_var.set("Femur angle: -")

                if res.knee_angle_deg is not None:
                    self.knee_var.set(f"Knee angle: {res.knee_angle_deg:.1f}°")
                else:
                    self.knee_var.set("Knee angle: -")

                self.status_var.set(f"Status: {res.status_text}")

                # update angle bars
                femur_val = float(res.femur_angle_deg) if res.femur_angle_deg is not None else 0.0
                knee_val = float(res.knee_angle_deg) if res.knee_angle_deg is not None else 0.0

                # Scale: Femur 0..90 deg, Knee 0..180 deg
                femur_h = min(1.0, femur_val / 90.0) * self._bar_max_h
                knee_h = min(1.0, knee_val / 180.0) * self._bar_max_h

                self.bar_canvas.coords(self.femur_bar_rect, 40, self._bar_base_y - femur_h, 100, self._bar_base_y)
                self.bar_canvas.coords(self.knee_bar_rect, 150, self._bar_base_y - knee_h, 210, self._bar_base_y)

                # Update value text and move it to the top of each bar
                self.bar_canvas.coords(self.femur_bar_text, 70, self._bar_base_y - femur_h - 15)
                self.bar_canvas.coords(self.knee_bar_text, 180, self._bar_base_y - knee_h - 15)
                self.bar_canvas.itemconfig(self.femur_bar_text, text=f"{femur_val:.1f}°")
                self.bar_canvas.itemconfig(self.knee_bar_text, text=f"{knee_val:.1f}°")

                # debug: visible marker ids
                cv2.putText(frame, f"IDs: {list(markers.keys())}", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            else:
                cv2.putText(frame, "PAUSED", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Convert BGR -> RGB for Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            # Fit the full frame into the video label to avoid clipping (which looks like "zoom")
            self.update_idletasks()
            max_w = self.video_label.winfo_width()
            max_h = self.video_label.winfo_height()
            if max_w > 1 and max_h > 1:
                img = self._resize_to_fit(img, max_w, max_h)

            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(self.delay_ms, self.update_loop)

    def on_close(self):
        try:
            self.camera.release()
        finally:
            self.destroy()
