import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect(r"C:\Users\ABUBAKAR SADEEQ\Desktop\community_cyber_alert\instance\database.db")
cursor = conn.cursor()

# Add the missing columns
cursor.execute("ALTER TABLE user ADD COLUMN first_name TEXT;")
cursor.execute("ALTER TABLE user ADD COLUMN last_name TEXT;")
cursor.execute("ALTER TABLE user ADD COLUMN local_government TEXT;")
cursor.execute("ALTER TABLE user ADD COLUMN community TEXT;")
cursor.execute("ALTER TABLE user ADD COLUMN date_of_birth DATE;")
cursor.execute("ALTER TABLE user ADD COLUMN gender TEXT;")

# Commit the changes
conn.commit()

# Check the schema of the 'user' table
cursor.execute("PRAGMA table_info(user);")
columns = cursor.fetchall()

# Print the columns
for column in columns:
    print(column)

# Close the connection
conn.close()
