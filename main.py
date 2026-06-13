import os
import threading
import queue

from core.config_manager import get_config
from core.excel_helper import paste_to_excel
from core.browser_controller import BrowserController

from ui.sound_confirmation import play_sound, FAIL_SOUND
from ui.ui_widget import LastCopiedWidget


def play_fail():
    threading.Thread(
        target=play_sound,
        args=(FAIL_SOUND,),
        daemon=True
    ).start()


def main():
    wb_name = input("Excel workbook name (e.g. book.xlsx): ").strip()
    sheet_name = input("Sheet name (e.g. Sheet1): ").strip()

    left_cell = "C10"
    right_cell = "I10"

    print(f"AutoExtracted='{left_cell}', Manual='{right_cell}'")

    config = get_config()

    widget = LastCopiedWidget()

    # Get screen size from Tkinter main thread.
    screen_width = widget.root.winfo_screenwidth()
    screen_height = widget.root.winfo_screenheight()

    taskbar_adjustment = 120
    browser_width = screen_width
    browser_height = screen_height - taskbar_adjustment

    print(f"Detected screen size: {screen_width}x{screen_height}")
    print(f"Browser size: {browser_width}x{browser_height}")

    # Queue for Excel writes
    task_queue = queue.Queue()

    # Queue for safe Tkinter UI actions
    ui_queue = queue.Queue()

    def process_ui_queue():
        """
        Runs in Tkinter main thread.
        Handles widget updates and shutdown safely.
        """
        try:
            while True:
                action = ui_queue.get_nowait()

                if action[0] == "update":
                    text = action[1]
                    widget.update_text(text)

                elif action[0] == "shutdown":
                    reason = action[1]
                    print("Closing app:", reason)

                    try:
                        widget.root.destroy()
                    except Exception:
                        pass

                    os._exit(0)

        except queue.Empty:
            pass

        try:
            widget.root.after(100, process_ui_queue)
        except Exception:
            pass

    def excel_worker():
        """
        Handles Excel writes one by one.
        Safe to run in background thread.
        """
        while True:
            wb, sheet, cell, clip = task_queue.get()

            try:
                paste_to_excel(wb, sheet, cell, clip)

                # Do not update Tkinter directly from this thread.
                ui_queue.put(("update", clip))

            except Exception as e:
                print("Excel error:", e)
                play_fail()

            task_queue.task_done()

    browser_controller = BrowserController(
        config=config,
        wb_name=wb_name,
        sheet_name=sheet_name,
        left_cell=left_cell,
        right_cell=right_cell,
        browser_width=browser_width,
        browser_height=browser_height,
        task_queue=task_queue,
        ui_queue=ui_queue
    )

    # Start Excel worker
    threading.Thread(
        target=excel_worker,
        daemon=True
    ).start()

    # Start Playwright browser controller
    threading.Thread(
        target=browser_controller.start,
        daemon=True
    ).start()

    # Start UI queue polling in main Tkinter thread
    widget.root.after(100, process_ui_queue)

    # Tkinter must run in main thread
    widget.start()


if __name__ == "__main__":
    main()
