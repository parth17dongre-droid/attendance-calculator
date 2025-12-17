from importer import ExcelImporter
from backend import AttendanceEngine
import os

# --- CONFIGURATION ---
# IMPORTANT: Use ONLY the batch code (e.g., "A1", "B2"), not "CSE A1"
STUDENT_BATCH = "A1"  

SEMESTER_START = "2025-07-01" 
SEMESTER_END   = "2026-01-02"

EXCEL_FILE_NAME = "timetable.xlsx" 

def test_final():
    print(f"🚀 Starting Database Refresh for Batch: {STUDENT_BATCH}\n")

    # 1. Setup Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, EXCEL_FILE_NAME)
    db_path = os.path.join(base_dir, "attendance.db")

    # 2. CLEAR OLD DATA (Crucial!)
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Deleted old 'attendance.db' to start fresh.")

    # 3. Run the New Importer
    print(f"📂 Reading Excel file from {file_path}...")
    importer = ExcelImporter()
    
    # NEW LOGIC: This single function gets Theory AND Labs
    final_schedule = importer.get_student_schedule(file_path, STUDENT_BATCH)
    
    if not final_schedule:
        print("❌ Error: No schedule found. Check your file name and path.")
        return

    # Debug: Print what we found to prove Labs are there
    print("\n🔎 Preview of Data Found:")
    for day, classes in final_schedule.items():
        print(f"  {day}: {classes}")
        
    # 4. Save to Database
    print("\n⚙️ Saving to Database...")
    engine = AttendanceEngine()
    engine.generate_semester_schedule(SEMESTER_START, SEMESTER_END, final_schedule)
    
    print("✅ Success! Database rebuilt. Run 'app.py' now.")

if __name__ == "__main__":
    test_final()