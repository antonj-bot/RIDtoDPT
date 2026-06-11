import os
import json



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
        json.dump(config, f, indent=4)

def get_config():
    config = load_config()
    if not config:
        print("No valid config found. Using defaults.")
        
        config = {
            "hotkey_left": "[",
            "hotkey_right": "]"
        }
        save_config(config)
        
    return config
