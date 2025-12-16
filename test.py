# In file: test.py 

from importer import ExcelImporter
from backend import AttendanceEngine
import os


STUDENT_BATCH = "CSE A1" 


TARGET_SHEET_INDEX = 0 	
SEMESTER_START = "2025-07-01" 
SEMESTER_END 	 = "2026-01-02"

def test_final():
    print(f"🚀 Starting Import for Batch: {STUDENT_BATCH}\n")

    # 1. Find File
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'timetable.xlsx')
    
    # 2. Run Importer
    print(f"📂 Reading Excel file from {file_path}...")
    importer = ExcelImporter()
    
    # Passing '0' opens the first sheet regardless of its name
    weekly_schedule = importer.parse_excel(file_path, sheet_name=TARGET_SHEET_INDEX)
    
    if not weekly_schedule:
        print("❌ Found nothing. Please check the Excel file path and structure.")
        print("   1. Make sure 'timetable.xlsx' is in the same directory.")
        return

    print("✅ Schedule Found!")
    
    # ------------------ CRITICAL FILTERING STEP ------------------
    # 3. Filter the schedule to get only the classes for the user's batch
    print(f"⚙️ Filtering schedule for {STUDENT_BATCH} using importer logic...")
    filtered_schedule = importer.get_filtered_schedule(weekly_schedule, STUDENT_BATCH)
    print(f"✅ Filtered schedule generated. Total class days: {len(filtered_schedule)}")
    # -------------------------------------------------------------

    # 4. Save the FILTERED schedule to Database
    print("\n⚙️ Saving Filtered Schedule to Database...")
    engine = AttendanceEngine()
    
    # !!! Use the filtered_schedule for database generation !!!
    engine.generate_semester_schedule(SEMESTER_START, SEMESTER_END, filtered_schedule)
    
    print("✅ Done! Database populated with filtered schedule. You can now run 'app.py'")

if __name__ == "__main__":
    test_final()