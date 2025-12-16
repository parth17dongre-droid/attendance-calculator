import sqlite3
from datetime import datetime, timedelta

class AttendanceEngine:
    def __init__(self, db_name="attendance.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT,      -- Changed to TEXT to fix DeprecationWarning
                day_name TEXT,
                subject TEXT,
                status TEXT DEFAULT 'Pending'
            )
        """)
        self.conn.commit()

    def generate_semester_schedule(self, start_date_str, end_date_str, weekly_timetable):
        # 1. Convert Strings to Date Objects
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        # 2. CLEAR OLD DATA (Critical Step!)
        # This prevents duplicates and stuck session counts
        self.cursor.execute("DELETE FROM sessions")
        self.conn.commit()
        print("DEBUG: Cleared old database sessions.")

        current_day = start
        count = 0
        
        # 3. Generate New Sessions
        while current_day <= end:
            day_name = current_day.strftime("%A")
            
            if day_name in weekly_timetable:
                subjects = weekly_timetable[day_name]
                for sub in subjects:
                    self.add_session(current_day, day_name, sub)
                    count += 1
            
            current_day += timedelta(days=1)
        
        self.conn.commit()
        print(f"✅ Generated {count} total sessions from {start} to {end}.")

    def add_session(self, date_obj, day_name, subject):
        # FIX: Convert Date Object -> String explicitly
        # This fixes the "DeprecationWarning" and makes app.py lookups work
        date_str = date_obj.strftime("%Y-%m-%d")
        
        self.cursor.execute("""
            INSERT INTO sessions (session_date, day_name, subject, status)
            VALUES (?, ?, ?, ?)
        """, (date_str, day_name, subject, 'Pending'))

# Note: No commit here, we commit in the main loop for speed