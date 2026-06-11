# RID to DPT Automation Tool

Small Python tool for extracting a Report ID from the live site and writing it directly into an open Excel workbook.

This version does not use clipboard copy/paste. It gets the Report ID directly from the page using a CSS selector.

## What it does

- Opens the configured live site with Playwright
- Finds the Report ID using a CSS selector
- Scans open tabs and popups
- Checks iframes when looking for the Report ID
- Removes `Report Id:` from the extracted text
- Writes the cleaned RID into Excel
- Plays a success or fail sound
- Shows the last extracted RID in a small widget
- Closes the app when the browser is closed

## Requirements

- Windows
- Python 3.10 or newer
- Microsoft Excel
- Open Excel workbook before running the app
- Playwright browser installed

## Install

Install the required Python packages:

```bash
pip install -r requirements.txt
