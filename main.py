import os
import time
import threading
import queue
import pyautogui
import pyperclip
import keyboard
import pygame

pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
SUCCESS_SOUND = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "copy_successfully.wav"))
FAIL_SOUND = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "copy_failed.wav"))

from core.installer import install_and_import
from core.config_manager import get_config
from core.excel_helper import paste_to_excel
from ui.ui_widget import LastCopiedWidget

install_and_import(["pyautogui", "pyperclip", "pywin32", "keyboard", "tk", "screeninfo"])

# ----------------- SOUND FUNCTION -----------------
def play_sound(sound):
    import ui.ui_widget as ui_widget
    if ui_widget.MUTED:
        return
    try:
        sound.stop()
        sound.play()
    except Exception as e:
        print(f"Error playing sound: {e}")
# --------------------------------------------------

def main():
    wb_name = input("Excel workbook name (e.g. book.xlsx): ").strip()
    sheet_name = input("Sheet name (e.g. Sheet1): ").strip()

    left_cell = "C10"
    right_cell = "I10"

    print(f"AutoExtracted='{left_cell}', Manual='{right_cell}'")

    config = get_config()
    click_pos = config["click_pos"]
    key_left = config["hotkey_left"]
    key_right = config["hotkey_right"]

    widget = LastCopiedWidget()

    # Excel queue for background writing
    task_queue = queue.Queue()

    def excel_worker():
        """Handles Excel writes one by one (prevents lag)."""
        while True:
            wb, sheet, cell, clip = task_queue.get()
            try:
                paste_to_excel(wb, sheet, cell, clip)
                widget.update_text(clip)
            except Exception as e:
                print("Excel error:", e)
                threading.Thread(target=play_sound, args=(FAIL_SOUND,), daemon=True).start()
            task_queue.task_done()

    threading.Thread(target=excel_worker, daemon=True).start()

    def key_loop():
        while True:
            if keyboard.is_pressed("esc"):
                os._exit(0)

            # LEFT hotkey
            if keyboard.is_pressed(key_left):
                pyautogui.moveTo(*click_pos)
                pyautogui.click(clicks=2)
                pyautogui.hotkey("ctrl", "c")
                clip = pyperclip.paste().strip()

                if clip and clip not in ("[", "]", "{", "}"):
                    threading.Thread(target=play_sound, args=(SUCCESS_SOUND,), daemon=True).start()
                    task_queue.put((wb_name, sheet_name, left_cell, clip))
                else:
                    threading.Thread(target=play_sound, args=(FAIL_SOUND,), daemon=True).start()

                while keyboard.is_pressed(key_left):
                    time.sleep(0.01)

            # RIGHT hotkey
            if keyboard.is_pressed(key_right):
                pyautogui.moveTo(*click_pos)
                pyautogui.click(clicks=2)
                pyautogui.hotkey("ctrl", "c")
                clip = pyperclip.paste().strip()

                if clip and clip not in ("[", "]", "{", "}"):
                    threading.Thread(target=play_sound, args=(SUCCESS_SOUND,), daemon=True).start()
                    task_queue.put((wb_name, sheet_name, right_cell, clip))
                else:
                    threading.Thread(target=play_sound, args=(FAIL_SOUND,), daemon=True).start()

                while keyboard.is_pressed(key_right):
                    time.sleep(0.01)

            time.sleep(0.01)

    threading.Thread(target=key_loop, daemon=True).start()
    widget.start()


if __name__ == "__main__":
    main()
