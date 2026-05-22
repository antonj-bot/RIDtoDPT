import os
import json
from screeninfo import get_monitors
import pyautogui
import tkinter as tk
import keyboard



CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return None

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def show_monitor_labels():
    windows = []
    for i, m in enumerate(get_monitors()):
        root = tk.Tk()
        root.overrideredirect(True)  # no borders
        # Small window in the top-left corner of each monitor
        root.geometry(f"200x150+{m.x}+{m.y}")
        root.configure(bg="black")

        label = tk.Label(root, text=str(i), font=("Arial", 60, "bold"), fg="white", bg="black")
        label.pack(expand=True)

        # Make window topmost but don't steal focus
        root.attributes("-topmost", True)
        root.attributes("-disabled", True)
        root.update()

        windows.append(root)

    return windows

def get_click_position_with_ctrl():
    print("Now point your mouse to the RID and press CTRL to copy the position...")
    while True:
        # Wait until CTRL is pressed
        if keyboard.is_pressed("ctrl"):
            x, y = pyautogui.position()
            print(f"Captured position at ({x}, {y})")
            return x, y

# Example usage
if __name__ == "__main__":
    show_monitor_labels()        

def get_config():
    monitors = get_monitors()
    saved = load_config()
    
    if saved:
        print("\nFound saved config:")
        print(f"  Monitor index: {saved['monitor_index']}")
        print(f"  Relative X/Y: ({saved['relative_x']}, {saved['relative_y']})")
        print(f"  Left Hotkey: {saved['hotkey_left']}")
        print(f"  Right Hotkey: {saved['hotkey_right']}")
        use = input("Use saved config? (y/n): ").strip().lower()
        if use == "y":
            mon = monitors[saved['monitor_index']]
            abs_x = mon.x + saved['relative_x']
            abs_y = mon.y + saved['relative_y']
            return {
                "click_pos": (abs_x, abs_y),
                "hotkey_left": saved["hotkey_left"],
                "hotkey_right": saved["hotkey_right"]
            }
        else:
            windows = show_monitor_labels() 
            idx = int(input("Monitor numbers are shown on screen, please choose which monitor: "))
            abs_x, abs_y = get_click_position_with_ctrl()
            rel_x = abs_x - monitors[idx].x
            rel_y = abs_y - monitors[idx].y
            hotkey_left = input("Enter LEFT/Autoextract hotkey (default `{`): ").strip() or "{"
            hotkey_right = input("Enter RIGHT/Manual hotkey (default `}`): ").strip() or "}"
            print("Good to Go!")
        
        for w in windows:
            w.destroy()
        
        config = {
        "monitor_index": idx,
        "relative_x": rel_x,
        "relative_y": rel_y,
        "hotkey_left": hotkey_left,
        "hotkey_right": hotkey_right
    }    
        save_config(config)
        return {"click_pos": (abs_x, abs_y), "hotkey_left": hotkey_left, "hotkey_right": hotkey_right}
        
    else:
        print("No settings found, let's make a new one")
        windows = show_monitor_labels() 
        idx = int(input("Monitor numbers are shown on screen, please choose which monitor: "))
        abs_x, abs_y = get_click_position_with_ctrl()
        rel_x = abs_x - monitors[idx].x
        rel_y = abs_y - monitors[idx].y
        hotkey_left = input("Enter LEFT/Autoextract hotkey (default `{`): ").strip() or "{"
        hotkey_right = input("Enter RIGHT/Manual hotkey (default `}`): ").strip() or "}"
        print("Good to Go!")
        
        for w in windows:
            w.destroy()
        
        config = {
        "monitor_index": idx,
        "relative_x": rel_x,
        "relative_y": rel_y,
        "hotkey_left": hotkey_left,
        "hotkey_right": hotkey_right
    }    
        save_config(config)
        return {"click_pos": (abs_x, abs_y), "hotkey_left": hotkey_left, "hotkey_right": hotkey_right}
    
    print("\nAvailable monitors:")
    for i, m in enumerate(monitors):
        print(f"[{i}] {m.width}x{m.height} at ({m.x},{m.y})")


