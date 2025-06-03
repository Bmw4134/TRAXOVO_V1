"""
Script to count assets in the database
"""
from app import app, db
from models import Asset

def count_assets():
    """Count the number of assets in the database"""
    with app.app_context():
        count = Asset.query.count()
        print(f"Number of assets in database: {count}")

if __name__ == "__main__":
    count_assets()