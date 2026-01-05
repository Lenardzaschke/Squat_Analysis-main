from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import math


@dataclass
class AngleResult:
    femur_angle_deg: Optional[float]
    knee_angle_deg: Optional[float]
    rep_count: int
    new_rep: bool
    state: str
    status_text: str


def _vec(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (b[0] - a[0], b[1] - a[1])


def _norm(v: Tuple[float, float]) -> float:
    return math.hypot(v[0], v[1])


def _angle_deg(u: Tuple[float, float], v: Tuple[float, float]) -> Optional[float]:
    nu, nv = _norm(u), _norm(v)
    if nu == 0 or nv == 0:
        return None
    dot = u[0] * v[0] + u[1] * v[1]
    c = max(-1.0, min(1.0, dot / (nu * nv)))
    return math.degrees(math.acos(c))


class AngleAnalyzer:
    """
    Computes femur angle w.r.t. floor and knee angle.
    Additionally counts valid squat reps based on knee angle thresholds.

    Rep definition (default):
      standing (knee_angle >= top_knee_deg) -> deep (knee_angle <= bottom_knee_deg) -> standing
    """

    def __init__(
        self,
        hip_id: int,
        knee_id: int,
        ankle_id: int,
        floor_id1: Optional[int] = None,
        floor_id2: Optional[int] = None,
        require_all_markers: bool = True,

        # --- Rep counting parameters (knee-angle based) ---
        top_knee_deg: float = 165.0,        # "standing" threshold
        bottom_knee_deg: float = 100.0,     # "deep enough" threshold
        min_frames_below: int = 2,          # noise rejection
        min_frames_above: int = 2,          # noise rejection
    ):
        self.hip_id = hip_id
        self.knee_id = knee_id
        self.ankle_id = ankle_id
        self.floor_id1 = floor_id1
        self.floor_id2 = floor_id2
        self.require_all_markers = require_all_markers

        # rep counting config
        self.top_knee_deg = float(top_knee_deg)
        self.bottom_knee_deg = float(bottom_knee_deg)
        self.min_frames_below = max(1, int(min_frames_below))
        self.min_frames_above = max(1, int(min_frames_above))

        # rep counting state
        self.state = "above"  # above (=standing) or below (=deep)
        self.rep_count = 0
        self._below_counter = 0
        self._above_counter = 0

    def reset(self) -> None:
        self.state = "above"
        self.rep_count = 0
        self._below_counter = 0
        self._above_counter = 0

    def update(self, markers: Dict[int, Dict[str, Any]]) -> AngleResult:
        # Require hip/knee/ankle markers for angles
        missing = [mid for mid in (self.hip_id, self.knee_id, self.ankle_id) if mid not in markers]
        if missing:
            status = f"Missing markers: {missing}"
            return AngleResult(None, None, self.rep_count, False, self.state, status)

        hip = markers[self.hip_id]["center"]
        knee = markers[self.knee_id]["center"]
        ankle = markers[self.ankle_id]["center"]

        hip = (float(hip[0]), float(hip[1]))
        knee = (float(knee[0]), float(knee[1]))
        ankle = (float(ankle[0]), float(ankle[1]))

        femur = _vec(hip, knee)     # hip -> knee
        tibia = _vec(ankle, knee)   # ankle -> knee

        # Floor direction (fallback: image x-axis)
        floor_dir = (1.0, 0.0)
        floor_status = "floor:FALLBACK"
        if self.floor_id1 is not None and self.floor_id2 is not None:
            if self.floor_id1 in markers and self.floor_id2 in markers:
                f1 = markers[self.floor_id1]["center"]
                f2 = markers[self.floor_id2]["center"]
                f1 = (float(f1[0]), float(f1[1]))
                f2 = (float(f2[0]), float(f2[1]))
                floor_dir = _vec(f1, f2)
                floor_status = "floor:OK"

        femur_angle = _angle_deg(femur, floor_dir)
        knee_angle = _angle_deg(femur, tibia)

        if femur_angle is None or knee_angle is None:
            return AngleResult(femur_angle, knee_angle, self.rep_count, False, self.state,
                               "Angle computation failed (zero-length vector)")

        # --------------------
        # Rep counting (knee angle)
        # --------------------
        new_rep = False
        rep_status = ""

        if self.state == "above":
            # Wait until deep enough for enough frames
            if knee_angle <= self.bottom_knee_deg:
                self._below_counter += 1
            else:
                self._below_counter = 0

            if self._below_counter >= self.min_frames_below:
                self.state = "below"
                self._below_counter = 0
                self._above_counter = 0
                rep_status = "Reached depth"
            else:
                rep_status = "Standing / going down"

        elif self.state == "below":
            # Wait until standing again for enough frames
            if knee_angle >= self.top_knee_deg:
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
                rep_status = "Deep / coming up"

        status = f"OK ({floor_status}, {rep_status})"
        return AngleResult(femur_angle, knee_angle, self.rep_count, new_rep, self.state, status)
