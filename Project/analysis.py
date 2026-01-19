# Angle and squat analysis based on ArUco marker positions
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import math


@dataclass
class AngleResult:
    # Main outputs
    femur_angle_deg: Optional[float]   # femur angle relative to floor (deg)
    knee_angle_deg: Optional[float]    # knee angle (deg)
    bar_height_px: Optional[float]     # bar height above floor in pixels

    # Rep / event state
    rep_count: int                     # total counted reps
    new_rep: bool                      # rep completed (back to top)
    new_depth: bool                    # depth reached event (for sound)
    state: str                         # current state ("above" or "below")

    # Helpful flags for UI/logic (so other modules don't need to re-derive them)
    depth_reached: bool                # based on femur threshold
    standing: bool                     # based on femur + knee thresholds

    # Debug / diagnostics
    missing_markers: Tuple[int, ...]   # ids that were missing in this frame
    floor_y: Optional[float]           # y-position of floor marker (pixels)
    bar_y: Optional[float]             # y-position of bar marker (pixels)
    status_text: str

# vector from point a to point b
def _vec(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (b[0] - a[0], b[1] - a[1])

# vector length
def _norm(v: Tuple[float, float]) -> float:
    return math.hypot(v[0], v[1])

# compute angle between two vectors (0..180 deg)
def _angle_deg(u: Tuple[float, float], v: Tuple[float, float]) -> Optional[float]:
    nu, nv = _norm(u), _norm(v)
    if nu == 0 or nv == 0:
        return None
    dot = u[0] * v[0] + u[1] * v[1]
    c = max(-1.0, min(1.0, dot / (nu * nv)))
    return math.degrees(math.acos(c))

# signed angle between reference and vector (-180..180 deg)
def _signed_angle_deg(ref: Tuple[float, float], vec: Tuple[float, float]) -> Optional[float]:
    nr, nv = _norm(ref), _norm(vec)
    if nr == 0 or nv == 0:
        return None

    rx, ry = ref[0] / nr, ref[1] / nr # normalize reference
    vx, vy = vec[0] / nv, vec[1] / nv # normalize vector

    dot = rx * vx + ry * vy  
    cross_z = rx * vy - ry * vx
    return math.degrees(math.atan2(cross_z, dot))


class AngleAnalyzer:
    def __init__(
        self,
        hip_id: int,
        knee_id: int,
        ankle_id: int,
        floor_id: int,          # single floor marker to define floor_y (required)
        bar_id: int,            # marker on the bar (required)
        require_all_markers: bool = True,

        # knee angle threshold for standing
        top_knee_deg: float = 165.0,

        # femur angle thresholds for depth
        bottom_femur_deg: float = 5.0,   # deep enough when |femur| <= this
        top_femur_deg: float = 70.0,      # standing when |femur| >= this

        # rep counting settings
        min_frames_below: int = 2,   # below = depth reached (femur <= 0)
        min_frames_above: int = 2,   # above = standing again
    ):
        self.hip_id = hip_id
        self.knee_id = knee_id
        self.ankle_id = ankle_id
        self.floor_id = int(floor_id)
        self.bar_id = int(bar_id)
        self.require_all_markers = require_all_markers

        self.top_knee_deg = float(top_knee_deg)
        self.bottom_femur_deg = float(bottom_femur_deg)
        self.top_femur_deg = float(top_femur_deg)
        self.min_frames_below = max(1, int(min_frames_below))
        self.min_frames_above = max(1, int(min_frames_above))

        # rep counting state
        self.state = "above"  # above (=standing/ready) or below (=depth reached)
        self.rep_count = 0
        self._below_counter = 0
        self._above_counter = 0

    def reset(self) -> None:
        # reset rep counter and state
        self.state = "above"
        self.rep_count = 0
        self._below_counter = 0
        self._above_counter = 0

    def update(self, markers: Dict[int, Dict[str, Any]]) -> AngleResult:
        # process one frame of marker data
        # body markers needed for angle calculation
        core_ids = (self.hip_id, self.knee_id, self.ankle_id)
        missing_core = [mid for mid in core_ids if mid not in markers]

        # track missing markers
        all_required = core_ids
        if self.require_all_markers:
            all_required = all_required + (self.floor_id, self.bar_id)
        missing_all = tuple(mid for mid in all_required if mid not in markers)

        if missing_core:
            status = f"Missing core markers: {missing_core}"
            return AngleResult(
                None, None, None,
                self.rep_count, False, False, self.state,
                False, False,
                missing_all,
                None, None,
                status,
            )

        # read marker centers
        hip = markers[self.hip_id]["center"]
        knee = markers[self.knee_id]["center"]
        ankle = markers[self.ankle_id]["center"]

        # convert to float
        hip = (float(hip[0]), float(hip[1]))
        knee = (float(knee[0]), float(knee[1]))
        ankle = (float(ankle[0]), float(ankle[1]))

        # build body vectors
        femur = _vec(hip, knee)      # hip -> knee
        tibia = _vec(ankle, knee)    # ankle -> knee

        # floor marker y position
        floor_y: Optional[float] = None
        floor_status = "floor:IMAGE_X"
        if self.floor_id in markers:
            fy = markers[self.floor_id]["center"]
            floor_y = float(fy[1])
        else:
            floor_status = "floor:MISSING"

        # bar marker y position
        bar_y: Optional[float] = None
        if self.bar_id in markers:
            by = markers[self.bar_id]["center"]
            bar_y = float(by[1])
        else:
            if floor_y is not None:
                floor_status = "bar:MISSING"

        bar_height_px: Optional[float] = None
        if floor_y is not None and bar_y is not None:
            bar_height_px = floor_y - bar_y  # positive when bar is above floor

        # floor direction (image x-axis)
        floor_dir = (1.0, 0.0)

        # ensure femur points forward
        if femur[0] * floor_dir[0] + femur[1] * floor_dir[1] < 0:
            femur = (-femur[0], -femur[1])
                
        # femur angle relative to floor
        femur_angle = _signed_angle_deg(floor_dir, femur)

        # knee angle
        knee_angle = _angle_deg(femur, tibia)

        if femur_angle is None or knee_angle is None:
            return AngleResult(
                femur_angle, knee_angle, bar_height_px,
                self.rep_count, False, False, self.state,
                False, False,
                missing_all,
                floor_y, bar_y,
                "Angle computation failed (zero-length vector)",
            )

        # rep counting logic
        new_rep = False
        new_depth = False
        rep_status = ""

        femur_abs = abs(femur_angle)
        depth_reached = (femur_abs <= self.bottom_femur_deg)
        standing_femur = (femur_abs >= self.top_femur_deg)
        standing_knee = (knee_angle >= self.top_knee_deg)
        standing = bool(standing_femur and standing_knee)

        if self.state == "above":
            # Wait until depth is reached for enough frames
            if depth_reached:
                self._below_counter += 1
            else:
                self._below_counter = 0

            if self._below_counter >= self.min_frames_below:
                self.state = "below"
                self._below_counter = 0
                self._above_counter = 0
                new_depth = True
                rep_status = f"Reached depth (|femur| <= {self.bottom_femur_deg:.0f}°)"
            else:
                rep_status = "Standing / going down"

        elif self.state == "below":
            # Wait until standing again (femur upright + knee extended) for enough frames
            if standing:
                self._above_counter += 1
            else:
                self._above_counter = 0

            if self._above_counter >= self.min_frames_above:
                self.state = "above"
                self.rep_count += 1
                new_rep = True
                self._above_counter = 0
                rep_status = "Rep completed"
            else:
                rep_status = "Depth / coming up"

        status = f"OK ({floor_status}, {rep_status})"
        return AngleResult(
            femur_angle, knee_angle, bar_height_px,
            self.rep_count, new_rep, new_depth, self.state,
            depth_reached, standing,
            missing_all,
            floor_y, bar_y,
            status,
        )
