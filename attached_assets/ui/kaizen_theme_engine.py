# kaizen_theme_engine.py
import json
import os

THEMES = ["default", "dark", "vp_mode", "print_safe"]

def apply_theme(theme_name):
    if theme_name not in THEMES:
        raise ValueError("Theme not recognized")
    config = {"active_theme": theme_name}
    with open("meta/ui_theme_config.json", "w") as f:
        json.dump(config, f)
    print(f"🎨 Applied theme: {theme_name}")

def get_current_theme():
    if os.path.exists("meta/ui_theme_config.json"):
        with open("meta/ui_theme_config.json") as f:
            return json.load(f).get("active_theme", "default")
    return "default"

if __name__ == "__main__":
    apply_theme("vp_mode")
