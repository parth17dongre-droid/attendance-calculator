import sqlite3

def init_db():
    # 1. Connect to the database (creates attendance.db if it doesn't exist)
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    print("🔧 Setting up database...")

    # 2. Create the 'students' table
    # This holds the list of students (Roll No, Name)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        division TEXT
    )
    ''')
    print("✅ Table 'students' is ready.")

    # 3. Create the 'attendance' table
    # This records every time someone is marked present/absent
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT,
        date TEXT,
        time TEXT,
        subject TEXT,
        status TEXT,
        FOREIGN KEY(roll_no) REFERENCES students(roll_no)
    )
    ''')
    print("✅ Table 'attendance' is ready.")

    # 4. Save and Close
    conn.commit()
    conn.close()
    print("🚀 Database setup complete!")

if __name__ == "__main__":
    init_db()