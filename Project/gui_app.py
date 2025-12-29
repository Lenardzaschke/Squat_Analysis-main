# gui_app.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2


class SquatApp(tk.Tk):
    """
    Tkinter GUI:
    - Displays live camera feed
    - Shows rep count + status text
    - Start/Stop button (pauses processing but can keep showing last frame)
    - Optional live threshold tuning via sliders
    """

    def __init__(self, camera, analyzer, sound_module, fps: int = 30):
        super().__init__()
        self.title("Squat Analyzer")
        self.camera = camera
        self.analyzer = analyzer
        self.sound_module = sound_module

        self.delay_ms = max(1, int(1000 / fps))
        self.running = True  # controls whether we process + count reps

        # --- Layout ---
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Video area
        self.video_label = ttk.Label(root)
        self.video_label.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Info labels
        self.rep_var = tk.StringVar(value="Reps: 0")
        self.state_var = tk.StringVar(value="State: -")
        self.status_var = tk.StringVar(value="Status: -")

        ttk.Label(root, textvariable=self.rep_var, font=("Arial", 16)).grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.state_var, font=("Arial", 12)).grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Label(root, textvariable=self.status_var, font=("Arial", 12)).grid(row=1, column=2, sticky="w", pady=(10, 0))

        # Controls
        self.start_stop_btn = ttk.Button(root, text="Pause", command=self.toggle_running)
        self.start_stop_btn.grid(row=2, column=0, sticky="w", pady=10)

        self.reset_btn = ttk.Button(root, text="Reset Reps", command=self.reset_reps)
        self.reset_btn.grid(row=2, column=1, sticky="w", pady=10)

        self.quit_btn = ttk.Button(root, text="Quit", command=self.on_close)
        self.quit_btn.grid(row=2, column=2, sticky="e", pady=10)

        # --- Optional: Live threshold tuning ---
        # This is super useful later for quick calibration without changing code.
        self.top_slider = ttk.Scale(
            root, from_=0, to=800, value=self.analyzer.top_threshold, command=self._on_top_change
        )
        self.bottom_slider = ttk.Scale(
            root, from_=0, to=800, value=self.analyzer.bottom_threshold, command=self._on_bottom_change
        )
        ttk.Label(root, text="Top threshold (standing)").grid(row=3, column=0, sticky="w")
        self.top_slider.grid(row=3, column=1, columnspan=2, sticky="ew")
        ttk.Label(root, text="Bottom threshold (depth)").grid(row=4, column=0, sticky="w")
        self.bottom_slider.grid(row=4, column=1, columnspan=2, sticky="ew")

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
        self.state_var.set("State: -")
        self.status_var.set("Status: -")

    def _on_top_change(self, _):
        # ttk.Scale returns strings via callback; cast safely
        self.analyzer.top_threshold = int(float(self.top_slider.get()))

    def _on_bottom_change(self, _):
        self.analyzer.bottom_threshold = int(float(self.bottom_slider.get()))

    def update_loop(self):
        frame, markers = self.camera.get_frame_and_markers()

        if frame is not None:
            if self.running:
                result = self.analyzer.update(markers)

                # Trigger sound only when a new rep is detected
                if result.new_rep:
                    self.sound_module.play_valid_squat_sound()

                self.rep_var.set(f"Reps: {result.rep_count}")
                self.state_var.set(f"State: {result.state}")
                self.status_var.set(f"Status: {result.status_text}")

                # Optional: show visible marker IDs in the frame
                cv2.putText(frame, f"IDs: {list(markers.keys())}", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            else:
                # When paused: still show camera image, but don't count reps
                cv2.putText(frame, "PAUSED", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Convert BGR -> RGB for Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Keep reference to prevent garbage collection
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(self.delay_ms, self.update_loop)

    def on_close(self):
        try:
            self.camera.release()
        finally:
            self.destroy()