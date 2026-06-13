import re


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