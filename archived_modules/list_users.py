import sqlite3

conn = sqlite3.connect('data/systemsmith.db')
cursor = conn.cursor()

try:
    print("Available User Logins:")
    cursor.execute("SELECT username, role, email FROM users")
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"Username: {user[0]}, Role: {user[1]}, Email: {user[2]}")
    else:
        print("No users found in the database.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()