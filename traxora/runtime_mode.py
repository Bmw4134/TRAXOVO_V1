import os

def is_dev_mode():
    return os.getenv("REPLIT_PROFILE", "dev") == "dev"

def get_mode_tag():
    return "[DEVELOPMENT]" if is_dev_mode() else "[PRODUCTION]"
