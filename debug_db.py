import sqlite3

# Connect to your database
# (Make sure this matches the filename created by test.py, likely 'attendance.db' or 'schedule.db')
conn = sqlite3.connect("attendance.db") 
cursor = conn.cursor()

print("--- DIAGNOSTIC REPORT ---")

# 1. Check if ANY data exists
cursor.execute("SELECT count(*) FROM sessions")
count = cursor.fetchone()[0]
print(f"Total Sessions found: {count}")

if count > 0:
    # 2. See what the dates actually look like
    print("\nSample of dates stored in the database:")
    cursor.execute("SELECT session_date, subject FROM sessions LIMIT 5")
    for row in cursor.fetchall():
        print(f"Date: {row[0]} | Type: {type(row[0])} | Subject: {row[1]}")

    # 3. Check for Today's Date
    from datetime import date
    today_str = date.today().isoformat() # "2025-12-16"
    print(f"\nChecking for today: {today_str}")
    
    cursor.execute("SELECT * FROM sessions WHERE session_date = ?", (today_str,))
    todays_classes = cursor.fetchall()
    
    if len(todays_classes) == 0:
        print("❌ NO CLASSES FOUND for today. (This is why your screen is empty)")
    else:
        print(f"✅ Found {len(todays_classes)} classes for today!")

conn.close()