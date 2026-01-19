import tkinter as tk
from collections import deque
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# live knee angle plot window
class KneeAngleDashboard(tk.Toplevel):
    def __init__(self, master, max_points: int = 300, refresh_ms: int = 100):
        super().__init__(master)
        self.title("Knee Angle (Live)")
        self.max_points = max(50, int(max_points))
        self.refresh_ms = max(20, int(refresh_ms))

        # data buffers
        self.t0 = time.time()
        self.t_data = deque(maxlen=self.max_points)
        self.knee_data = deque(maxlen=self.max_points)

        # matplotlib figure
        self.fig = Figure(figsize=(6, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Knee angle [deg]")
        self.ax.grid(True)

        (self.line,) = self.ax.plot([], []) 

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # make close only hide window (optional)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._visible = True

        self.after(self.refresh_ms, self._redraw)

    def _on_close(self):
        # hide instead of destroy, so it can be shown again
        self._visible = False
        self.withdraw()

    def show(self):
        self._visible = True
        self.deiconify()
        self.lift()

    def add_sample(self, knee_angle_deg: float):
        # add new sample to buffers
        t = time.time() - self.t0
        self.t_data.append(t)
        self.knee_data.append(knee_angle_deg)

    def _redraw(self):
        if self._visible:
            # update line data
            self.line.set_data(list(self.t_data), list(self.knee_data))

            # rescale axes
            if len(self.t_data) >= 2:
                self.ax.set_xlim(self.t_data[0], self.t_data[-1])

                ymin = min(self.knee_data)
                ymax = max(self.knee_data)
                if ymin == ymax:
                    ymin -= 1
                    ymax += 1
                self.ax.set_ylim(ymin - 2, ymax + 2)

            self.canvas.draw_idle()

        self.after(self.refresh_ms, self._redraw)


# live bar height plot window (cm)
class BarHeightDashboard(tk.Toplevel):
    def __init__(self, master, max_points: int = 300, refresh_ms: int = 100):
        super().__init__(master)
        self.title("Bar Height (Live)")
        self.max_points = max(50, int(max_points))
        self.refresh_ms = max(20, int(refresh_ms))

        # data buffers
        self.t0 = time.time()
        self.t_data = deque(maxlen=self.max_points)
        self.height_cm_data = deque(maxlen=self.max_points)

        # matplotlib figure
        self.fig = Figure(figsize=(6, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Bar height [cm]")
        self.ax.grid(True)

        (self.line,) = self.ax.plot([], [])  # no color specified -> matplotlib default

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # make close only hide window (optional)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._visible = True
        self.after(self.refresh_ms, self._redraw)

    def _on_close(self):
        # hide instead of destroy, so it can be shown again
        self._visible = False
        self.withdraw()

    def show(self):
        self._visible = True
        self.deiconify()
        self.lift()

    def add_sample(self, bar_height_cm: float):
        # add new sample to buffers
        t = time.time() - self.t0
        self.t_data.append(t)
        self.height_cm_data.append(bar_height_cm)

    def _redraw(self):
        if self._visible:
            # update line data
            self.line.set_data(list(self.t_data), list(self.height_cm_data))

            # rescale axes
            if len(self.t_data) >= 2:
                self.ax.set_xlim(self.t_data[0], self.t_data[-1])

                ymin = min(self.height_cm_data)
                ymax = max(self.height_cm_data)
                if ymin == ymax:
                    ymin -= 1
                    ymax += 1
                self.ax.set_ylim(ymin - 2, ymax + 2)

            self.canvas.draw_idle()

        self.after(self.refresh_ms, self._redraw)


# live femur angle plot window
class FemurAngleDashboard(tk.Toplevel):
    def __init__(self, master, max_points: int = 300, refresh_ms: int = 100):
        super().__init__(master)
        self.title("Femur Angle (Live)")
        self.max_points = max(50, int(max_points))
        self.refresh_ms = max(20, int(refresh_ms))

        # data buffers
        self.t0 = time.time()
        self.t_data = deque(maxlen=self.max_points)
        self.femur_data = deque(maxlen=self.max_points)

        # matplotlib figure
        self.fig = Figure(figsize=(6, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Femur angle [deg]")
        self.ax.grid(True)

        (self.line,) = self.ax.plot([], [])  # no color specified -> matplotlib default

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # make close only hide window (optional)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._visible = True
        self.after(self.refresh_ms, self._redraw)

    def _on_close(self):
        # hide instead of destroy, so it can be shown again
        self._visible = False
        self.withdraw()

    def show(self):
        self._visible = True
        self.deiconify()
        self.lift()

    def add_sample(self, femur_angle_deg: float):
        # add new sample to buffers
        t = time.time() - self.t0
        self.t_data.append(t)
        self.femur_data.append(femur_angle_deg)

    def _redraw(self):
        if self._visible:
            # update line data
            self.line.set_data(list(self.t_data), list(self.femur_data))

            # rescale axes
            if len(self.t_data) >= 2:
                self.ax.set_xlim(self.t_data[0], self.t_data[-1])

                ymin = min(self.femur_data)
                ymax = max(self.femur_data)
                if ymin == ymax:
                    ymin -= 1
                    ymax += 1
                self.ax.set_ylim(ymin - 2, ymax + 2)

            self.canvas.draw_idle()

        self.after(self.refresh_ms, self._redraw)
