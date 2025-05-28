# Simplified init_db.py mockup with config fallback
try:
    config
except NameError:
    config = {
        "database": "traxora_dev.db",
        "seed_on_startup": True
    }

def initialize_db():
    print(f"Initializing DB with config: {config}")
