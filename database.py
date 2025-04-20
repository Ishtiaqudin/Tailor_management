import sqlite3
import os
import sys
import contextlib
import hashlib

# Get database path - works in both frozen and non-frozen environments
def get_db_path():
    """Get database path that works both in development and when frozen"""
    DB_NAME = 'tmms.db'
    
    if getattr(sys, 'frozen', False):
        # Running as a frozen executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, DB_NAME)

# Database path
DB_PATH = get_db_path()

CUSTOMER_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naap_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    mobile_number TEXT NOT NULL,
    address TEXT,
    date_of_entry TEXT NOT NULL
);
"""

MEASUREMENT_TABLE = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    dress_type TEXT NOT NULL,
    measurements TEXT NOT NULL,
    collar_type TEXT,
    stitch_type TEXT,
    fabric_type TEXT,
    tailor_instructions TEXT,
    urgent_delivery INTEGER,
    expected_delivery_date TEXT,
    date_created TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
"""

ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    measurement_id INTEGER, -- Optional link to a specific measurement
    order_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    due_date TEXT, -- Expected completion date
    price REAL NOT NULL,
    amount_paid REAL DEFAULT 0,
    payment_status TEXT CHECK(payment_status IN ('Unpaid', 'Partially Paid', 'Paid')) DEFAULT 'Unpaid',
    order_status TEXT CHECK(order_status IN ('Pending', 'In Progress', 'Ready', 'Completed', 'Delivered', 'Cancelled')) DEFAULT 'Pending',
    notes TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(measurement_id) REFERENCES measurements(id)
);
"""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
"""

COUNTERS_TABLE = """
CREATE TABLE IF NOT EXISTS counters (
    year INTEGER PRIMARY KEY,
    last_number INTEGER NOT NULL
);
"""

def init_db():
    # Update DB_PATH when initializing
    global DB_PATH
    DB_PATH = get_db_path()
    print(f"Initializing database at: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(CUSTOMER_TABLE)
    c.execute(MEASUREMENT_TABLE)
    c.execute(ORDERS_TABLE)
    c.execute(USERS_TABLE)
    c.execute(COUNTERS_TABLE)
    conn.commit()
    create_default_admin(conn)
    conn.close()

def create_default_admin(conn):
    """Creates a default admin user if the users table is empty."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    
    if user_count == 0:
        print("No users found. Creating default admin user (admin/password)...")
        username = "admin"
        password = "password"
        # Hash the password using SHA-256
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        try:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            print("Default admin user created.")
        except sqlite3.Error as e:
            print(f"Error creating default admin user: {e}")
            conn.rollback() # Rollback changes on error

@contextlib.contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper cleanup."""
    conn = None
    try:
        # Always get the latest DB_PATH
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        yield conn
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
