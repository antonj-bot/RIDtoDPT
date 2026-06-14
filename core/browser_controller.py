import time
import threading
import keyboard

from playwright.sync_api import sync_playwright

from core.text_utils import clean_rid_text
from ui.sound_confirmation import play_sound, SUCCESS_SOUND, FAIL_SOUND


class BrowserController:
    def __init__(
        self,
        config,
        wb_name,
        sheet_name,
        left_cell,
        right_cell,
        browser_width,
        browser_height,
        task_queue,
        ui_queue,
        hotkeys_enabled_event=None
    ):
        self.config = config
        self.wb_name = wb_name
        self.sheet_name = sheet_name
        self.left_cell = left_cell
        self.right_cell = right_cell
        self.browser_width = browser_width
        self.browser_height = browser_height
        self.task_queue = task_queue
        self.ui_queue = ui_queue
        self.hotkeys_enabled_event = hotkeys_enabled_event

        self.browser = None
        self.context = None
        self.active_page = None
        self.registered_pages = set()

    def play_success(self):
        threading.Thread(
            target=play_sound,
            args=(SUCCESS_SOUND,),
            daemon=True
        ).start()

    def play_fail(self):
        threading.Thread(
            target=play_sound,
            args=(FAIL_SOUND,),
            daemon=True
        ).start()

    def request_shutdown(self, reason="Browser closed"):
        """
        Tell the main Tkinter thread to close the widget/app.
        """
        print(reason)
        self.ui_queue.put(("shutdown", reason))

    def hotkeys_are_enabled(self):
        """
        Returns True only when the widget toggle has enabled hotkeys.
        Hotkeys are OFF by default because the event starts cleared.
        """
        return (
            self.hotkeys_enabled_event is not None
            and self.hotkeys_enabled_event.is_set()
        )

    def maximize_window(self, page):
        """
        Force browser window bounds to match screen size.
        """
        try:
            session = self.context.new_cdp_session(page)
            window = session.send("Browser.getWindowForTarget")

            session.send(
                "Browser.setWindowBounds",
                {
                    "windowId": window["windowId"],
                    "bounds": {
                        "left": 0,
                        "top": 0,
                        "width": self.browser_width,
                        "height": self.browser_height
                    }
                }
            )

            print("Browser window resized to desktop size.")

        except Exception as e:
            print("Resize warning:", e)

    def get_alive_pages(self):
        alive_pages = []

        try:
            for page in self.context.pages:
                try:
                    if not page.is_closed():
                        alive_pages.append(page)
                except Exception:
                    pass
        except Exception:
            pass

        return alive_pages

    def playwright_pause(self, ms=50):
        """
        Allows Playwright to process events.
        Falls back to time.sleep if no page is available.
        """
        alive_pages = self.get_alive_pages()

        if alive_pages:
            try:
                alive_pages[-1].wait_for_timeout(ms)
            except Exception:
                time.sleep(ms / 1000)
        else:
            time.sleep(ms / 1000)

    def handle_dialog(self, dialog):
        """
        Let the website/browser's original dialog appear.

        IMPORTANT:
        We do not call dialog.accept() or dialog.dismiss() here,
        because the user wants to click the original OK/Cancel popup.
        """
        try:
            print("Browser dialog appeared:", dialog.type, dialog.message)

            # Do not show a Tkinter popup here.
            # Do not call dialog.accept().
            # Do not call dialog.dismiss().
            # Let the user interact with the original browser/site popup.

        except Exception as e:
            print("Dialog notice warning:", e)

    def register_page(self, page):
        if page in self.registered_pages:
            return

        self.registered_pages.add(page)

        try:
            page.on("popup", self.handle_popup)
            page.on("close", lambda: self.handle_page_close(page))
            page.on("dialog", self.handle_dialog)
        except Exception as e:
            print("Page registration warning:", e)

        try:
            print("Registered page:", page.url)
        except Exception:
            print("Registered page: unknown URL")

    def handle_page_close(self, closed_page):
        print("Page closed.")

        try:
            self.registered_pages.discard(closed_page)
        except Exception:
            pass

        try:
            if self.active_page == closed_page:
                alive_pages = self.get_alive_pages()

                if alive_pages:
                    self.active_page = alive_pages[-1]
                    print("Switched active page to:", self.active_page.url)
                else:
                    self.active_page = None
                    print("No active page available.")

        except Exception as e:
            print("Page close handling warning:", e)

    def handle_popup(self, popup_page):
        print("POPUP detected!")

        self.active_page = popup_page
        self.register_page(popup_page)

        try:
            popup_page.bring_to_front()
        except Exception as e:
            print("Bring popup to front warning:", e)

        try:
            popup_page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception as e:
            print("Popup load warning:", e)

        self.maximize_window(popup_page)

        try:
            print("Active page changed to popup:", popup_page.url)
        except Exception:
            print("Active page changed to popup.")

    def handle_new_page(self, new_page):
        print("NEW TAB/PAGE detected!")

        self.active_page = new_page
        self.register_page(new_page)

        try:
            new_page.bring_to_front()
        except Exception as e:
            print("Bring new page to front warning:", e)

        try:
            new_page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception as e:
            print("New page load warning:", e)

        self.maximize_window(new_page)

        try:
            print("Active page changed to:", new_page.url)
        except Exception:
            print("Active page changed to new page.")

    def find_text_in_all_pages(self, selector, timeout=1000):
        """
        Scans all open tabs/pages and iframes for selector.
        Returns: text, found_page
        """
        alive_pages = self.get_alive_pages()

        if not alive_pages:
            raise Exception("No open Playwright pages available.")

        for page in alive_pages:
            try:
                print("Scanning page:", page.url)

                # 1. Try main page
                try:
                    locator = page.locator(selector)

                    if locator.count() > 0:
                        locator.first.wait_for(timeout=timeout)
                        text = locator.first.inner_text().strip()

                        print("Found selector on page:", page.url)
                        return text, page

                except Exception:
                    pass

                # 2. Try iframes
                for frame in page.frames:
                    try:
                        locator = frame.locator(selector)

                        if locator.count() > 0:
                            locator.first.wait_for(timeout=timeout)
                            text = locator.first.inner_text().strip()

                            print("Found selector inside iframe:", frame.url)
                            print("Parent page:", page.url)

                            return text, page

                    except Exception:
                        pass

            except Exception as e:
                print("Scan page error:", e)

        raise Exception(f"Selector not found in any open tab/page: {selector}")

    def process_hotkey(self, target_cell, side_name):
        """
        Extracts the Report ID and queues it for Excel paste.

        Important:
        If hotkeys are OFF, this returns immediately.
        That means no extraction, no Excel paste, and no sounds.
        """
        if not self.hotkeys_are_enabled():
            return

        try:
            selector = self.config["RID_selector"]

            print(f"{side_name} hotkey pressed")
            print("Scanning all tabs for selector:", selector)

            raw_text, found_page = self.find_text_in_all_pages(
                selector,
                timeout=1000
            )

            self.active_page = found_page

            print("Raw extracted text:", raw_text)

            clip = clean_rid_text(raw_text)

            print("Trimmed RID:", clip)
            print("Found on page:", self.active_page.url)

            if clip and clip not in ("[", "]", "{", "}"):
                self.play_success()

                self.task_queue.put((
                    self.wb_name,
                    self.sheet_name,
                    target_cell,
                    clip
                ))
            else:
                self.play_fail()

        except Exception as e:
            print(f"{side_name} extraction error:", e)
            self.play_fail()

    def run_browser_loop(self):
        key_left = self.config["hotkey_left"]
        key_right = self.config["hotkey_right"]

        while True:
            try:
                if not self.browser.is_connected():
                    self.request_shutdown("Browser closed. Closing app.")
                    break

                alive_pages = self.get_alive_pages()

                if not alive_pages:
                    self.request_shutdown("No browser pages left. Closing app.")
                    break

                # Fallback page registration
                for page in alive_pages:
                    if page not in self.registered_pages:
                        print("Fallback detected page:", page.url)
                        self.active_page = page
                        self.register_page(page)
                        self.maximize_window(page)

                # Hotkeys are ignored completely when OFF.
                # This prevents extraction, Excel paste, success sound, and fail sound.
                if self.hotkeys_are_enabled():
                    if keyboard.is_pressed(key_left):
                        self.process_hotkey(self.left_cell, "LEFT")

                        while keyboard.is_pressed(key_left):
                            self.playwright_pause(10)

                    if keyboard.is_pressed(key_right):
                        self.process_hotkey(self.right_cell, "RIGHT")

                        while keyboard.is_pressed(key_right):
                            self.playwright_pause(10)

                self.playwright_pause(50)

            except Exception as e:
                print("Playwright loop warning:", e)

                try:
                    if not self.browser.is_connected():
                        self.request_shutdown(
                            "Browser closed during operation. Closing app."
                        )
                        break
                except Exception:
                    self.request_shutdown("Browser unavailable. Closing app.")
                    break

                time.sleep(0.2)

    def start(self):
        """
        Main Playwright entry point.
        """
        with sync_playwright() as p:
            self.browser = p.chromium.launch(
                headless=False,
                args=[
                    f"--window-size={self.browser_width},{self.browser_height}",
                    "--window-position=0,0"
                ]
            )

            self.context = self.browser.new_context(
                viewport={
                    "width": self.browser_width,
                    "height": self.browser_height
                },
                screen={
                    "width": self.browser_width,
                    "height": self.browser_height
                }
            )

            self.active_page = self.context.new_page()

            # Detect new tabs/pages
            self.context.on("page", self.handle_new_page)

            # Register first page
            self.register_page(self.active_page)

            # Resize before loading site
            self.maximize_window(self.active_page)

            self.active_page.goto(
                self.config["live_site"],
                wait_until="domcontentloaded"
            )

            # Resize again after loading site
            self.maximize_window(self.active_page)

            print("Browser is running...")
            print("Initial page:", self.active_page.url)

            self.run_browser_loop()