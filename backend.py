import sqlite3
import os
import shutil
import sys
from datetime import datetime, timedelta

class AttendanceEngine:
    def __init__(self, db_name="attendance.db"):
        # --- START OF ANDROID DATABASE FIX ---
        
        # 1. Determine where the database file currently lives (Read-Only Source)
        # This is where the APK extracts your files initially.
        source_path = os.path.join(os.path.dirname(__file__), db_name)
        
        # 2. Determine where we WANT it to live (Writable Destination)
        # We check if we are on Android to choose the right folder.
        if "ANDROID_ARGUMENT" in os.environ:
            # On Android, we must use the internal app storage
            dest_folder = os.path.expanduser("~")
        else:
            # On PC, just use the current folder
            dest_folder = os.getcwd()
            
        dest_path = os.path.join(dest_folder, db_name)
        
        # 3. The "Cloning" Logic
        # If the database does NOT exist in the writable folder yet, 
        # we copy it from the read-only source.
        if not os.path.exists(dest_path):
            if os.path.exists(source_path):
                try:
                    shutil.copy(source_path, dest_path)
                    print(f"✅ [Android Setup] Copied database to writable storage: {dest_path}")
                except Exception as e:
                    print(f"❌ [Error] Could not copy database: {e}")
            else:
                print("⚠️ [Warning] No source database found. Creating a new empty one.")
        else:
            print(f"ℹ️ [Info] Using existing database at: {dest_path}")

        # --- END OF FIX ---

        # 4. Connect to the WRITABLE database path
        self.conn = sqlite3.connect(dest_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT,      
                day_name TEXT,
                subject TEXT,
                status TEXT DEFAULT 'Pending'
            )
        """)
        self.conn.commit()

    def generate_semester_schedule(self, start_date_str, end_date_str, weekly_timetable):
        # 1. Convert Strings to Date Objects
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"❌ Date Error: {e}")
            return

        # 2. CLEAR OLD DATA (Critical Step!)
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
        date_str = date_obj.strftime("%Y-%m-%d")
        
        self.cursor.execute("""
            INSERT INTO sessions (session_date, day_name, subject, status)
            VALUES (?, ?, ?, ?)
        """, (date_str, day_name, subject, 'Pending'))