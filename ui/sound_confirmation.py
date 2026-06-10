import os
import pygame

pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
SUCCESS_SOUND = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "copy_successfully.wav"))
FAIL_SOUND = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "copy_failed.wav"))

def play_sound(sound):
    import ui.ui_widget as ui_widget
    if ui_widget.MUTED:
        return
    try:
        sound.stop()
        sound.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

