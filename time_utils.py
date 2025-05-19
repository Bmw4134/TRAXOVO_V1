from datetime import datetime, timedelta

def parse_time_with_tz(time_str):
    time_str = time_str.replace(" CT", "").strip()
    try:
        return datetime.strptime(time_str, "%I:%M %p")
    except ValueError:
        return None

def calculate_lateness(actual, expected, threshold):
    if not actual or not expected:
        return None
    delta = (actual - expected).total_seconds() / 60
    return max(0, int(delta)) if delta > threshold else 0