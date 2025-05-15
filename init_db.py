"""
Initialize database script

Run this script to create all database tables:
$ python init_db.py

"""
from app import app, db
import models  # Import all models to ensure they're registered with SQLAlchemy

def init_db():
    """Initialize the database"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()