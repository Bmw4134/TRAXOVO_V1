import json

def render_sidebar():
    with open("sidebar_config.json") as f:
        config = json.load(f)
    for module in config["modules"]:
        print(f"📘 Module: {module}")
