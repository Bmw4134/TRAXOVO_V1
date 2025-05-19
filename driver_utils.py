import re

def extract_driver_from_label(label):
    match = re.search(r'\((.*?)\)', label)
    return match.group(1) if match else "UNKNOWN"

def clean_asset_info(label):
    return re.sub(r'\(.*?\)', '', label).strip()