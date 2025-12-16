import sqlite3

def find_labs():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    print("\n🔎 SEARCHING FOR LABS IN DATABASE...")
    print("---------------------------------------")
    
    # We search for common Lab keywords or your batch name
    # Adjust '%A1%' if your batch is different
    cursor.execute("""
        SELECT session_date, day_name, subject 
        FROM sessions 
        WHERE subject LIKE '%(LL)%' 
           OR subject LIKE '%Lab%' 
           OR subject LIKE '%Prac%'
           OR subject LIKE '%A1%'
        ORDER BY session_date ASC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No Labs found. The 'Merge Trap' might still be deleting them.")
    else:
        print(f"✅ Found {len(rows)} Lab entries! Here are the first few:")
        for date, day, sub in rows:
            print(f"   📅 {date} ({day}): {sub}")

    conn.close()

if __name__ == "__main__":
    find_labs()