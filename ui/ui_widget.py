import tkinter as tk
from tkinter import messagebox

# -------------------- CONFIG --------------------
WIDGET_WIDTH = 180
WIDGET_HEIGHT = 80

# Hotkeys ON theme
GRADIENT_ON_TOP = "#4b6cb7"
GRADIENT_ON_BOTTOM = "#182848"

# Hotkeys OFF theme
GRADIENT_OFF_TOP = "#b74b4b"
GRADIENT_OFF_BOTTOM = "#481818"

FONT_NAME = "Segoe UI"
FONT_SIZE = 11
TEXT_COLOR = "white"
BORDER_COLOR = "#ffffff"
BORDER_WIDTH = 2
# ------------------------------------------------

# Global mute flag
MUTED = False
IS_PAUSED = False


class LastCopiedWidget:
    def __init__(self, hotkeys_enabled_event=None):
        self.hotkeys_enabled_event = hotkeys_enabled_event

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        self.width = WIDGET_WIDTH
        self.height = WIDGET_HEIGHT

        # Canvas for gradient and text
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw OFF gradient by default
        self.draw_gradient(GRADIENT_OFF_TOP, GRADIENT_OFF_BOTTOM)

        # Draw border
        self.canvas.create_rectangle(
            0,
            0,
            self.width,
            self.height,
            outline=BORDER_COLOR,
            width=BORDER_WIDTH
        )

        # Draw text directly on canvas
        self.text_id = self.canvas.create_text(
            self.width // 2,
            self.height // 1.5,
            text="Last pasted:\n(none)",
            font=(FONT_NAME, FONT_SIZE, "bold"),
            fill=TEXT_COLOR,
            justify="center"
        )

        # Drag support
        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        # Hotkeys toggle button - OFF by default
        self.hotkeys_button = tk.Button(
            self.root,
            text="⌨ OFF",
            font=(FONT_NAME, 8, "bold"),
            command=self.toggle_hotkeys,
            bg="#ffdddd",
            fg="#000000",
            relief="flat",
            bd=0
        )
        self.hotkeys_button.place(x=self.width - 125, y=5, width=45, height=20)

        # Help button
        self.help_button = tk.Button(
            self.root,
            text="?",
            font=(FONT_NAME, 10, "bold"),
            command=self.show_help,
            bg="#ffffff",
            fg="#000000",
            relief="flat",
            bd=0
        )
        self.help_button.place(x=self.width - 75, y=5, width=20, height=20)

        # Mute button
        self.mute_button = tk.Button(
            self.root,
            text="🔊",
            font=(FONT_NAME, 10),
            command=self.toggle_mute,
            bg="#ffffff",
            fg="#000000",
            relief="flat",
            bd=0
        )
        self.mute_button.place(x=self.width - 50, y=5, width=20, height=20)

        # Reset button
        self.reset_button = tk.Button(
            self.root,
            text="🔄",
            font=(FONT_NAME, 10),
            command=self.place_top_right,
            bg="#ffffff",
            fg="#000000",
            relief="flat",
            bd=0
        )
        self.reset_button.place(x=self.width - 25, y=5, width=20, height=20)

        # Start at top-right
        self.place_top_right()

    # -------------------- HOTKEY TOGGLE --------------------
    def toggle_hotkeys(self):
        if self.hotkeys_enabled_event is None:
            return

        if self.hotkeys_enabled_event.is_set():
            self.hotkeys_enabled_event.clear()

            self.hotkeys_button.config(
                text="⌨ OFF",
                bg="#ffdddd"
            )

            # Turn widget reddish when hotkeys are OFF
            self.draw_gradient(GRADIENT_OFF_TOP, GRADIENT_OFF_BOTTOM)

        else:
            self.hotkeys_enabled_event.set()

            self.hotkeys_button.config(
                text="⌨ ON",
                bg="#ddffdd"
            )

            # Turn widget blue when hotkeys are ON
            self.draw_gradient(GRADIENT_ON_TOP, GRADIENT_ON_BOTTOM)

    # -------------------- HELP MENU --------------------
    def show_help(self):
        help_text = (
            "Help & Tips\n"
            "--------------------\n"
            "Hotkeys:\n"
            "• Press [ to paste to AutoExtract.\n"
            "• Press ] to paste to Manual.\n\n"
            "Hotkey Toggle:\n"
            "• Hotkeys are OFF when the app starts.\n"
            "• Red widget means hotkeys are OFF.\n"
            "• Blue widget means hotkeys are ON.\n"
            "• Click ⌨ OFF / ⌨ ON to disable or enable hotkeys.\n\n"
            "Tips:\n"
            "• The widget shows the most recent value pasted to Excel.\n"
            "• Click and drag this widget to move it.\n"
            "• Click 🔄 to return the widget to the top-right corner.\n"
            "• Click 🔊 / 🔇 to toggle sound feedback.\n"
            "• Make sure the correct browser tab or popup is open before using hotkeys.\n"
            "• If extraction fails, check that the Report ID is visible on the page.\n"
            "• Closing all browser pages will also close the app."
        )

        messagebox.showinfo(
            "Help",
            help_text,
            parent=self.root
        )

    # -------------------- MUTE TOGGLE --------------------
    def toggle_mute(self):
        global MUTED
        MUTED = not MUTED

        if MUTED:
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")

    # -------------------- GRADIENT --------------------
    def draw_gradient(self, top_color, bottom_color):
        self.canvas.delete("gradient")

        r1, g1, b1 = self.hex_to_rgb(top_color)
        r2, g2, b2 = self.hex_to_rgb(bottom_color)

        for i in range(self.height):
            r = int(r1 + (r2 - r1) * i / self.height)
            g = int(g1 + (g2 - g1) * i / self.height)
            b = int(b1 + (b2 - b1) * i / self.height)

            color = f"#{r:02x}{g:02x}{b:02x}"

            self.canvas.create_line(
                0,
                i,
                self.width,
                i,
                fill=color,
                tags="gradient"
            )

        self.canvas.lower("gradient")

    # -------------------- HELPER --------------------
    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(
            int(hex_color[i:i + 2], 16)
            for i in (0, 2, 4)
        )

    # -------------------- DRAG --------------------
    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.offset_x)
        y = self.root.winfo_y() + (event.y - self.offset_y)

        self.root.geometry(f"+{x}+{y}")

    # -------------------- PLACE WIDGET --------------------
    def place_top_right(self):
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()

        x = screen_width - self.width - 20
        y = 20

        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    # -------------------- UPDATE TEXT --------------------
    def update_text(self, text):
        if not text:
            text = "(none)"

        if len(text) > 70:
            text = text[:70] + "..."

        self.canvas.itemconfig(
            self.text_id,
            text=f"Last pasted:\n{text}"
        )

    # -------------------- START WIDGET --------------------
    def start(self):
        self.root.mainloop()