# analysis.py
"""
analysis.py

This module contains the squat evaluation logic.

Goal:
- Use ArUco marker positions (pixel coordinates) to estimate squat "depth"
- Detect a valid squat repetition using a simple state machine:
    above -> below -> above  => 1 valid rep
- Provide rep count + "new rep" event for triggering a sound in the GUI

Important:
- This version uses the Y-position of ONE marker (e.g. hip marker) as the depth signal.
- In an image, Y usually increases downward:
    smaller Y = higher position
    larger Y  = lower position
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any


@dataclass
class SquatResult:
    """Returned by SquatAnalyzer.update() each frame."""
    rep_count: int
    new_rep: bool
    depth: Optional[float]
    state: str
    status_text: str


class SquatAnalyzer:
    """
    SquatAnalyzer evaluates squat repetitions based on marker positions.

    Markers format (as returned by camera.py in our earlier setup):
        markers = {
            marker_id: {
                "center": (cx, cy),
                "corners": np.ndarray shape (4,2)
            },
            ...
        }

    Basic approach here:
    - Track the hip marker Y coordinate as a proxy for squat depth.
    - Use two thresholds:
        * top_threshold: when hip_y is ABOVE (smaller) this value, athlete is considered "standing"
        * bottom_threshold: when hip_y is BELOW (greater) this value, athlete is considered "deep enough"
    - A valid rep is counted once the athlete:
        standing -> deep enough -> standing again
    """

    def __init__(
        self,
        hip_id: int = 0,
        top_threshold: int = 200,
        bottom_threshold: int = 350,
        min_frames_below: int = 1,
        require_marker: bool = True,
    ):
        """
        Args:
            hip_id: ArUco ID used as the main depth marker (e.g., on the hip/pelvis).
            top_threshold: Pixel Y threshold for "standing" (smaller Y = higher).
            bottom_threshold: Pixel Y threshold for "deep enough" (larger Y = lower).
            min_frames_below: How many consecutive frames must be below bottom_threshold
                              before accepting the "below" state. Helps reject noise.
            require_marker: If True and hip marker is missing, no update is performed.
        """
        self.hip_id = hip_id
        self.top_threshold = top_threshold
        self.bottom_threshold = bottom_threshold
        self.min_frames_below = max(1, int(min_frames_below))
        self.require_marker = require_marker

        # State machine variables
        self.state = "above"  # "above" or "below"
        self.rep_count = 0

        # Noise handling
        self._below_frame_counter = 0

    def update(self, markers: Dict[int, Dict[str, Any]]) -> SquatResult:
        """
        Update squat state based on the current frame's marker detections.

        Args:
            markers: Dictionary of detected markers (see class docstring).

        Returns:
            SquatResult containing:
              - rep_count: total reps counted
              - new_rep: True if a rep was completed on this frame
              - depth: current depth value (hip_y) or None if unavailable
              - state: current internal state ("above"/"below")
              - status_text: human-readable status for GUI
        """
        # If the hip marker is not visible, we cannot measure depth
        if self.hip_id not in markers:
            if self.require_marker:
                return SquatResult(
                    rep_count=self.rep_count,
                    new_rep=False,
                    depth=None,
                    state=self.state,
                    status_text="Hip marker not detected",
                )
            # If marker is optional, we could keep last state without changing it
            return SquatResult(
                rep_count=self.rep_count,
                new_rep=False,
                depth=None,
                state=self.state,
                status_text="No marker (ignored)",
            )

        # Extract hip marker center
        _, hip_y = markers[self.hip_id]["center"]
        depth = float(hip_y)

        new_rep = False
        status_text = ""

        # --- State machine logic ---
        if self.state == "above":
            # Athlete is considered "standing" (or not deep enough yet).
            # We wait until hip_y is "low enough" (>= bottom_threshold) for enough frames.
            if hip_y >= self.bottom_threshold:
                self._below_frame_counter += 1
            else:
                self._below_frame_counter = 0

            if self._below_frame_counter >= self.min_frames_below:
                self.state = "below"
                self._below_frame_counter = 0  # reset once we switch
                status_text = "Reached depth (below)"
            else:
                status_text = "Above / going down"

        elif self.state == "below":
            # Athlete is deep enough; we wait until they come back up to standing.
            if hip_y <= self.top_threshold:
                self.state = "above"
                self.rep_count += 1
                new_rep = True
                status_text = "Rep completed!"
            else:
                status_text = "Below / coming up"

        else:
            # Safety fallback (should not happen)
            self.state = "above"
            status_text = "State reset"

        return SquatResult(
            rep_count=self.rep_count,
            new_rep=new_rep,
            depth=depth,
            state=self.state,
            status_text=status_text,
        )

    def reset(self) -> None:
        """Reset repetition counter and internal state."""
        self.state = "above"
        self.rep_count = 0
        self._below_frame_counter = 0