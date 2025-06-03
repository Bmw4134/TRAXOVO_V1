from werkzeug.security import generate_password_hash
import os
import psycopg2

# Connect to the database using environment variables
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Reset admin password
new_password = "admin123"
password_hash = generate_password_hash(new_password)

# Update the user
cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (password_hash,))
conn.commit()

print(f"Password reset for admin user to: {new_password}")

cursor.close()
conn.close()