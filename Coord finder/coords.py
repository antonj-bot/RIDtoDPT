import pyautogui
import keyboard
import time
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

print("Press ESC to quit.\n")

try:
    while True:
        if keyboard.is_pressed('esc'):
            print("ESC pressed. Exiting...")
            break

        x, y = pyautogui.position()
        clear_console()
        print(f"Mouse Position: X={x} Y={y}")
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
