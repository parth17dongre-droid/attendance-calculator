import pandas as pd
import sqlite3
from datetime import datetime, timedelta, date
import traceback
import re

# --- PART 1: EXCEL READER ---
class ExcelImporter:
    def get_schedule(self, file_path, batch, sheet_name=None):
        schedule = {}
        print(f"DEBUG: [Importer] Reading file: {file_path} (Sheet: {sheet_name})")
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
        except Exception as e:
            raise Exception(f"Error reading Excel: {e}")

        df.iloc[:, 0] = df.iloc[:, 0].ffill()

        for index, row in df.iterrows():
            if len(row) < 2: continue
            day_raw = str(row[0]).strip().upper()
            day_map = {
                "MON": "Monday", "MONDAY": "Monday",
                "TUE": "Tuesday", "TUESDAY": "Tuesday",
                "WED": "Wednesday", "WEDNESDAY": "Wednesday",
                "THU": "Thursday", "THURSDAY": "Thursday",
                "FRI": "Friday", "FRIDAY": "Friday",
                "SAT": "Saturday", "SATURDAY": "Saturday"
            }
            
            if day_raw in day_map:
                day_key = day_map[day_raw]
                if day_key not in schedule: schedule[day_key] = []

                for col in range(1, len(row) - 1):
                    cell = row[col]
                    next_cell = row[col+1]

                    if pd.notna(cell) and str(cell).strip() not in ["-", "nan", ""]:
                        is_lab = pd.isna(next_cell) or str(next_cell).strip() in ["", "nan"]
                        data = self._parse_cell(str(cell), batch, is_lab)
                        if data: schedule[day_key].append(data)

        return schedule

    def _parse_cell(self, text, batch, is_lab):
        text = str(text).strip().replace("\n", " ")
        if "LUNCH" in text.upper(): return None

        # THEORY (2 Points)
        if not is_lab: return {"name": text, "type": "Theory", "points": 2}

        # LAB (4 Points) - Surgical Extraction
        pattern = fr"(?:CSE\s+)?{re.escape(batch)}\s*[:\-\s]\s*(.*?)(?=\s+(?:CSE\s+)?[A-Z]\d[:\-\s]|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            lab_info = match.group(1).strip()
            if not lab_info: return None
            return {"name": f"[LAB] {lab_info}", "type": "Lab", "points": 4}
        
        if batch.lower() in text.lower() and "CSE" not in text and ":" not in text:
             return {"name": f"[LAB] {text}", "type": "Lab", "points": 4}
        
        return None

# --- PART 2: DB ENGINE ---
class AttendanceEngine:
    def __init__(self, db_name="attendance.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # We DROP the table to ensure the new 'points' column is added correctly
        self.cursor.execute("DROP TABLE IF EXISTS sessions")
        self.cursor.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT,
                day_name TEXT,
                subject TEXT,
                type TEXT,
                points INTEGER,
                status TEXT DEFAULT 'Pending'
            )
        """)
        self.conn.commit()

    def generate_semester_schedule(self, weekly_timetable, start_date_str, end_date_str):
        # 1. Parse Dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise Exception("Invalid Date Format! Use YYYY-MM-DD")

        print(f"DEBUG: Generating schedule from {start_date} to {end_date}")

        current_day = start_date
        count = 0
        
        # 2. Loop through every day of the semester
        while current_day <= end_date:
            day_name = current_day.strftime("%A")
            
            if day_name in weekly_timetable:
                classes = weekly_timetable[day_name]
                for cls in classes:
                    # cls is now a dictionary: {'name': 'Math', 'points': 2}
                    self.add_session(current_day, day_name, cls['name'], cls['type'], cls['points'])
                    count += 1
            
            current_day += timedelta(days=1)
        
        self.conn.commit()
        return count

    def add_session(self, date_obj, day_name, subject, type, points):
        date_str = date_obj.strftime("%Y-%m-%d")
        self.cursor.execute("""
            INSERT INTO sessions (session_date, day_name, subject, type, points, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, day_name, subject, type, points, 'Pending'))

# --- PART 3: BRIDGE ---
def process_excel(file_path, batch, start_date, end_date, sheet_name=None):
    try:
        importer = ExcelImporter()
        timetable_data = importer.get_schedule(file_path, batch, sheet_name)
        
        if not timetable_data:
            print(f"WARNING: No classes found for batch {batch}")
            
        engine = AttendanceEngine()
        # Pass the custom dates here
        count = engine.generate_semester_schedule(timetable_data, start_date, end_date)
        
        print(f"SUCCESS: Generated {count} sessions.")
        return count

    except Exception as e:
        traceback.print_exc()
        raise e