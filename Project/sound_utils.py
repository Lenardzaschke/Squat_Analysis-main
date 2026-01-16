# sound_utils.py
import winsound
import os

def play_valid_squat_sound():
    path = os.path.join(os.path.dirname(__file__), "b98b6050.wav")
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
