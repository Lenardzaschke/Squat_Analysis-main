# sound_utils.py
import os
import sys
import subprocess

def play_valid_squat_sound():
    # Play a short wav sound cross-platform.
    path = os.path.join(os.path.dirname(__file__), "b98b6050.wav")

    if sys.platform.startswith("darwin"):  # macOS
        # built-in macOS player
        subprocess.Popen(["afplay", path])
    elif sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:  # Linux
        # try common players
        for player in (["aplay", path], ["paplay", path]):
            try:
                subprocess.Popen(player)
                break
            except FileNotFoundError:
                continue