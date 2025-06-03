from app import app
from models.models import User

with app.app_context():
    users = User.query.all()
    print('Available User Logins:')
    for user in users:
        print(f'Username: {user.username}, Role: {user.role}, Email: {user.email}')