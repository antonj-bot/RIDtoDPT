from playsound import playsound
import pyautogui, pyperclip, keyboard, threading, time, os

class Sound_Confirmation:
    def __init__(self, wb_name, sheet_name, click_pos, key_left, key_right, widget, success_sound, failure_sound):
        self.wb_name = wb_name
        self.sheet_name = sheet_name
        self.click_pos = click_pos
        self.key_left = key_left
        self.key_right = key_right
        self.widget = widget
        self.success_sound = success_sound
        self.failure_sound = failure_sound
        self.pasted_left = False
        self.pasted_right = False

    def play_success_sound(self):
        playsound(self.success_sound, block=False)

    def play_failure_sound(self):
        playsound(self.failure_sound, block=False)

    def paste_clipboard_to_excel(self, cell):
        pyautogui.moveTo(*self.click_pos)
        pyautogui.click(clicks=2)
        pyautogui.hotkey('ctrl', 'c')
        clip = pyperclip.paste().strip()
        if clip and clip not in ('[', ']', '{', '}'):
            from core.excel_helper import paste_to_excel
            if paste_to_excel(self.wb_name, self.sheet_name, cell, clip):
                self.widget.update_text(clip)
                self.play_success_sound()
            else:
                self.play_failure_sound()

    def key_loop(self):
        while True:
            if keyboard.is_pressed('esc'):
                os._exit(0)

            # LEFT
            if keyboard.is_pressed(self.key_left):
                if not self.pasted_left:
                    while keyboard.is_pressed(self.key_left): time.sleep(0.01)
                    self.paste_clipboard_to_excel("C10")
                    self.pasted_left = True
            else:
                self.pasted_left = False

            # RIGHT
            if keyboard.is_pressed(self.key_right):
                if not self.pasted_right:
                    while keyboard.is_pressed(self.key_right): time.sleep(0.01)
                    self.paste_clipboard_to_excel("I10")
                    self.pasted_right = True
            else:
                self.pasted_right = False

            time.sleep(0.03)

    def start(self):
        threading.Thread(target=self.key_loop, daemon=True).start()
        self.widget.start()
