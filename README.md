A Python tool that automates copying text from anywhere on screen and pasting it into specific Excel cells using keyboard shortcuts.

Features:

 Hotkey-based copy and paste
- Automatically pastes into Excel (predefined cells)
- Sound feedback (success / failure)
- On-screen widget showing last copied value
- Configurable hotkeys and click position

Requirements:

- Python 3.8+
- Windows OS (required for `pywin32` and keyboard hooks)


Installation:

1. Clone or download this project

2. Install dependencies:
   ```bash
   pip install -r requirements.txt


How to Use:

1. Run the app:
   python main.py

2. Enter:
   - Excel workbook name
   - Sheet name

3. App will ask for one time setup of chosen Monitor, Screen Coordinates and Hotkeys.
   
3. Use your chosen or default hotkeys:
   - Left hotkey → copies to row C10 in excel, app can detect if cell has value and will move to next cell
   - Right hotkey → copies to row I10 in excel, app can detect if cell has value and will move to next cell
     
4.Minimize console and start keying

4.Once done using app, press ESC to exit.


