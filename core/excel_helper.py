import pythoncom
import win32com.client

EXCEL_INSTANCES = {}

def get_col_row(cell):
    col = ''.join(filter(str.isalpha, cell))
    row_str = ''.join(filter(str.isdigit, cell))
    return col, int(row_str)

def col_to_num(col):
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord("A") + 1)
    return num

def get_excel_instance(wb_name):
    """Return the same Excel instance for the workbook."""
    pythoncom.CoInitialize()
    if wb_name in EXCEL_INSTANCES:
        return EXCEL_INSTANCES[wb_name]

    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
    except Exception:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True

    wb = None
    for book in excel.Workbooks:
        if book.Name.lower().startswith(wb_name.lower()):
            wb = book
            break
    if wb is None:
        raise FileNotFoundError(f"No open workbook found matching '{wb_name}'.")

    EXCEL_INSTANCES[wb_name] = (excel, wb)
    return excel, wb

def paste_to_excel(wb_name, sheet_name, start_cell, text):
    excel, wb = get_excel_instance(wb_name)
    ws = wb.Worksheets(sheet_name)

    col, row = get_col_row(start_cell)
    col_num = col_to_num(col)
    current_row = row

    while ws.Cells(current_row, col_num).Value not in (None, ""):
        current_row += 1

    ws.Cells(current_row, col_num).Value = text

    # Save every 10 writes
    if not hasattr(paste_to_excel, "write_count"):
        paste_to_excel.write_count = 0
    paste_to_excel.write_count += 1
    if paste_to_excel.write_count % 10 == 0:
        wb.Save()
