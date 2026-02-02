import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def add_is_locked_column():
    conn = sqlite3.connect(DATABASE, timeout=10)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT 0")
        conn.commit()
        print("Column 'is_locked' added successfully.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Column 'is_locked' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
def recreate_appointments_table():
    conn = sqlite3.connect(DATABASE, timeout=10)
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS appointments")
        cursor.execute("""
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vet_id INTEGER,
                date TEXT,
                time TEXT,
                notes TEXT
            )
        """)
        conn.commit()
        print("Table 'appointments' recreated successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()
      

if __name__ == '__main__':
    add_is_locked_column()
