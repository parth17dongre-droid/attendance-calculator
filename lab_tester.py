import pandas as pd
import re

def get_clean_lab_schedule(file_path, target_batch):
    print(f"--- Processing Schedule for Batch {target_batch} ---")
    
    try:
        df = pd.read_excel(file_path, header=None)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Fill down day names
    df.iloc[:, 0] = df.iloc[:, 0].ffill()
    valid_days = ["MON", "MONDAY", "TUE", "TUESDAY", "WED", "WEDNESDAY", 
                  "THU", "THURSDAY", "FRI", "FRIDAY", "SAT", "SATURDAY"]

    for index, row in df.iterrows():
        day_raw = str(row[0]).strip().upper()
        if day_raw not in valid_days:
            continue
            
        for col_idx in range(1, len(row) - 1):
            current_cell = row[col_idx]
            next_cell = row[col_idx + 1]
            
            # Check for non-empty cell
            if pd.notna(current_cell) and str(current_cell).strip() not in ["-", "nan", ""]:
                
                # Check for 2-hour lab (Next cell is empty)
                is_lab_2hr = pd.isna(next_cell) or str(next_cell).strip() in ["", "nan"]
                
                if is_lab_2hr:
                    cell_text = str(current_cell).strip()
                    lines = cell_text.split('\n')
                    
                    for line in lines:
                        # Split line into list of words
                        tokens = re.split(r'\s+', line.strip())
                        
                        # Find where our batch is in this list
                        batch_index = -1
                        search_term = f"{target_batch}:" # e.g. "A1:"
                        
                        for i, token in enumerate(tokens):
                            # Check if token contains "A1:" (Handles "CSE A1:" and "AIMLA1:")
                            if search_term in token:
                                batch_index = i
                                break
                        
                        # If batch found, apply your logic
                        if batch_index != -1:
                            try:
                                # We need indices i+1 and i+3
                                if len(tokens) > batch_index + 3:
                                    subject = tokens[batch_index + 1]
                                    room = tokens[batch_index + 3]
                                    
                                    # Optional: Remove brackets for cleaner output
                                    subject = subject.replace('(', '').replace(')', '')
                                    room = room.replace('(', '').replace(')', '')
                                    
                                    # Create the ONE string
                                    final_output = f"{subject} {room}"
                                    print(f"[{day_raw}] {final_output}")
                                    
                                elif len(tokens) > batch_index + 1:
                                    # Fallback if list is too short (just print subject)
                                    subject = tokens[batch_index + 1].replace('(', '').replace(')', '')
                                    print(f"[{day_raw}] {subject}")
                                    
                            except IndexError:
                                pass

# --- TEST IT ---
# Replace with your file name
get_clean_lab_schedule("timetable.xlsx","A1")