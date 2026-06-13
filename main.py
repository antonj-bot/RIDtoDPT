import os
import re
import time
import threading
import queue
import keyboard

from playwright.sync_api import sync_playwright

from ui.sound_confirmation import play_sound, SUCCESS_SOUND, FAIL_SOUND
from core.config_manager import get_config
from core.excel_helper import paste_to_excel
from ui.ui_widget import LastCopiedWidget


def main():
    wb_name = input("Excel workbook name (e.g. book.xlsx): ").strip()
    sheet_name = input("Sheet name (e.g. Sheet1): ").strip()

    left_cell = "C10"
    right_cell = "I10"

    print(f"AutoExtracted='{left_cell}', Manual='{right_cell}'")

    config = get_config()
    key_left = config["hotkey_left"]
    key_right = config["hotkey_right"]

    widget = LastCopiedWidget()

    # Get screen size from Tkinter main thread.
    screen_width = widget.root.winfo_screenwidth()
    screen_height = widget.root.winfo_screenheight()

    # Optional adjustment so browser does not overlap taskbar too badly.
    # If you want true full screen size, set this to 0.
    taskbar_adjustment = 120
    browser_width = screen_width
    browser_height = screen_height - taskbar_adjustment

    print(f"Detected screen size: {screen_width}x{screen_height}")
    print(f"Browser size: {browser_width}x{browser_height}")

    # Queue for Excel writes
    task_queue = queue.Queue()

    # Queue for safe Tkinter UI actions
    ui_queue = queue.Queue()

    def clean_rid_text(text):
        """
        Converts:
            'Report Id: 1327309097'
        into:
            '1327309097'
        """
        return re.sub(
            r"^Report\s*Id:\s*",
            "",
            text,
            flags=re.IGNORECASE
        ).strip()

    def play_success():
        threading.Thread(
            target=play_sound,
            args=(SUCCESS_SOUND,),
            daemon=True
        ).start()

    def play_fail():
        threading.Thread(
            target=play_sound,
            args=(FAIL_SOUND,),
            daemon=True
        ).start()

    def request_shutdown(reason="Browser closed"):
        """
        Tell the main Tkinter thread to close the widget/app.
        """
        print(reason)
        ui_queue.put(("shutdown", reason))

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

    def playwright_loop():
        """
        All Playwright calls stay inside this one thread.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    f"--window-size={browser_width},{browser_height}",
                    "--window-position=0,0"
                ]
            )

            # Match Playwright viewport to actual browser window size.
            context = browser.new_context(
                viewport={
                    "width": browser_width,
                    "height": browser_height
                },
                screen={
                    "width": browser_width,
                    "height": browser_height
                }
            )

            active_page = context.new_page()
            registered_pages = set()

            def maximize_window(pg):
                """
                Force browser window bounds to match screen size.
                This avoids mismatch between Chrome window and Playwright viewport.
                """
                try:
                    session = context.new_cdp_session(pg)
                    window = session.send("Browser.getWindowForTarget")

                    session.send(
                        "Browser.setWindowBounds",
                        {
                            "windowId": window["windowId"],
                            "bounds": {
                                "left": 0,
                                "top": 0,
                                "width": browser_width,
                                "height": browser_height
                            }
                        }
                    )

                    print("Browser window resized to desktop size.")
                except Exception as e:
                    print("Resize warning:", e)

            def get_alive_pages():
                alive_pages = []

                try:
                    for pg in context.pages:
                        try:
                            if not pg.is_closed():
                                alive_pages.append(pg)
                        except Exception:
                            pass
                except Exception:
                    pass

                return alive_pages

            def playwright_pause(ms=50):
                """
                Allows Playwright to process events.
                Falls back to time.sleep if no page is available.
                """
                alive_pages = get_alive_pages()

                if alive_pages:
                    try:
                        alive_pages[-1].wait_for_timeout(ms)
                    except Exception:
                        time.sleep(ms / 1000)
                else:
                    time.sleep(ms / 1000)

            def register_page(pg):
                if pg in registered_pages:
                    return

                registered_pages.add(pg)

                def handle_dialog(dialog):
                    """
                    Let the website/browser's original dialog appear.

                    IMPORTANT:
                    We do not call dialog.accept() or dialog.dismiss() here,
                    because you want the user to click the original OK/Cancel popup.
                    """
                    try:
                        print("Browser dialog appeared:", dialog.type, dialog.message)

                        # Do not show Tkinter popup here.
                        # Do not call dialog.accept().
                        # Do not call dialog.dismiss().
                        # Let the user interact with the original site popup.

                    except Exception as e:
                        print("Dialog notice warning:", e)

                try:
                    pg.on("popup", handle_popup)
                    pg.on("close", lambda: handle_page_close(pg))
                    pg.on("dialog", handle_dialog)
                except Exception as e:
                    print("Page registration warning:", e)

                try:
                    print("Registered page:", pg.url)
                except Exception:
                    print("Registered page: unknown URL")

            def handle_page_close(closed_page):
                nonlocal active_page

                print("Page closed.")

                try:
                    registered_pages.discard(closed_page)
                except Exception:
                    pass

                try:
                    if active_page == closed_page:
                        alive_pages = get_alive_pages()

                        if alive_pages:
                            active_page = alive_pages[-1]
                            print("Switched active page to:", active_page.url)
                        else:
                            active_page = None
                            print("No active page available.")
                except Exception as e:
                    print("Page close handling warning:", e)

            def handle_popup(popup_page):
                nonlocal active_page

                print("POPUP detected!")

                active_page = popup_page
                register_page(popup_page)

                try:
                    popup_page.bring_to_front()
                except Exception as e:
                    print("Bring popup to front warning:", e)

                try:
                    popup_page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception as e:
                    print("Popup load warning:", e)

                maximize_window(popup_page)

                try:
                    print("Active page changed to popup:", popup_page.url)
                except Exception:
                    print("Active page changed to popup.")

            def handle_new_page(new_page):
                nonlocal active_page

                print("NEW TAB/PAGE detected!")

                active_page = new_page
                register_page(new_page)

                try:
                    new_page.bring_to_front()
                except Exception as e:
                    print("Bring new page to front warning:", e)

                try:
                    new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception as e:
                    print("New page load warning:", e)

                maximize_window(new_page)

                try:
                    print("Active page changed to:", new_page.url)
                except Exception:
                    print("Active page changed to new page.")

            def find_text_in_all_pages(selector, timeout=1000):
                """
                Scans all open tabs/pages and iframes for selector.
                Good for around 5 tabs.
                Returns: text, found_page
                """
                alive_pages = get_alive_pages()

                if not alive_pages:
                    raise Exception("No open Playwright pages available.")

                for pg in alive_pages:
                    try:
                        print("Scanning page:", pg.url)

                        # 1. Try main page
                        try:
                            locator = pg.locator(selector)

                            if locator.count() > 0:
                                locator.first.wait_for(timeout=timeout)
                                text = locator.first.inner_text().strip()

                                print("Found selector on page:", pg.url)
                                return text, pg

                        except Exception:
                            pass

                        # 2. Try iframes
                        for frame in pg.frames:
                            try:
                                locator = frame.locator(selector)

                                if locator.count() > 0:
                                    locator.first.wait_for(timeout=timeout)
                                    text = locator.first.inner_text().strip()

                                    print("Found selector inside iframe:", frame.url)
                                    print("Parent page:", pg.url)

                                    return text, pg

                            except Exception:
                                pass

                    except Exception as e:
                        print("Scan page error:", e)

                raise Exception(f"Selector not found in any open tab/page: {selector}")

            def process_hotkey(target_cell, side_name):
                nonlocal active_page

                try:
                    selector = config["RID_selector"]

                    print(f"{side_name} hotkey pressed")
                    print("Scanning all tabs for selector:", selector)

                    raw_text, found_page = find_text_in_all_pages(selector, timeout=1000)

                    active_page = found_page

                    print("Raw extracted text:", raw_text)

                    clip = clean_rid_text(raw_text)

                    print("Trimmed RID:", clip)
                    print("Found on page:", active_page.url)

                    if clip and clip not in ("[", "]", "{", "}"):
                        play_success()
                        task_queue.put((wb_name, sheet_name, target_cell, clip))
                    else:
                        play_fail()

                except Exception as e:
                    print(f"{side_name} extraction error:", e)
                    play_fail()

            # Detect new tabs/pages
            context.on("page", handle_new_page)

            # Register first page
            register_page(active_page)

            # Resize before loading site
            maximize_window(active_page)

            active_page.goto(config["live_site"], wait_until="domcontentloaded")

            # Resize again after loading site
            maximize_window(active_page)

            print("Browser is running...")
            print("Initial page:", active_page.url)

            while True:
                try:
                    # If browser window was closed manually, close everything.
                    if not browser.is_connected():
                        request_shutdown("Browser closed. Closing app.")
                        break

                    alive_pages = get_alive_pages()

                    # If all tabs/pages are closed, close everything.
                    if not alive_pages:
                        request_shutdown("No browser pages left. Closing app.")
                        break

                    # Fallback page registration
                    for pg in alive_pages:
                        if pg not in registered_pages:
                            print("Fallback detected page:", pg.url)
                            active_page = pg
                            register_page(pg)
                            maximize_window(pg)

                    if keyboard.is_pressed(key_left):
                        process_hotkey(left_cell, "LEFT")

                        while keyboard.is_pressed(key_left):
                            playwright_pause(10)

                    if keyboard.is_pressed(key_right):
                        process_hotkey(right_cell, "RIGHT")

                        while keyboard.is_pressed(key_right):
                            playwright_pause(10)

                    playwright_pause(50)

                except Exception as e:
                    print("Playwright loop warning:", e)

                    try:
                        if not browser.is_connected():
                            request_shutdown("Browser closed during operation. Closing app.")
                            break
                    except Exception:
                        request_shutdown("Browser unavailable. Closing app.")
                        break

                    time.sleep(0.2)

    # Start Excel worker
    threading.Thread(target=excel_worker, daemon=True).start()

    # Start Playwright thread
    threading.Thread(target=playwright_loop, daemon=True).start()

    # Start UI queue polling in main Tkinter thread
    widget.root.after(100, process_ui_queue)

    # Tkinter must run in main thread
    widget.start()


if __name__ == "__main__":
    main()