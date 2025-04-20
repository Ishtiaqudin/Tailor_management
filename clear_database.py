import sqlite3
import os
from database import DB_PATH, init_db

print(f"Starting database reset...")
print(f"Database path: {DB_PATH}")

# First: Delete the existing database if it exists
if os.path.exists(DB_PATH):
    print(f"Database file exists at: {DB_PATH}")
    try:
        os.remove(DB_PATH)
        print(f"Deleted existing database: {DB_PATH}")
    except Exception as e:
        print(f"Error deleting database: {e}")
        print("Please close any applications that might be using the database.")
        exit(1)
else:
    print(f"No existing database found at {DB_PATH}")

# Second: Recreate the empty database with schema
try:
    print("Creating new empty database...")
    init_db()
    print("Database has been reset successfully.")
    print("A fresh database with empty tables has been created.")
    
    # Verify the database was created
    if os.path.exists(DB_PATH):
        db_size = os.path.getsize(DB_PATH)
        print(f"New database created: {DB_PATH} (Size: {db_size} bytes)")
    else:
        print("WARNING: Database file not found after initialization!")
except Exception as e:
    print(f"Error recreating database: {e}")
    exit(1)

print("Database reset complete!") 