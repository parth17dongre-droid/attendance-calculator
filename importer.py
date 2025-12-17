import pandas as pd
import re

class ExcelImporter:
    def get_student_schedule(self, file_path, user_batch):
        """
        Main function to get the schedule for a specific batch (e.g., "A1").
        Returns a dictionary: {'Monday': ['Math (D101)', '[LAB] OOP OSTL'], ...}
        """
        schedule = {}
        
        print(f"--- Reading file: {file_path} ---")
        try:
            df = pd.read_excel(file_path, header=None)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            return {}

        # 1. Clean Data: Fill down Day names
        df.iloc[:, 0] = df.iloc[:, 0].ffill()
        
        valid_days = ["MON", "MONDAY", "TUE", "TUESDAY", "WED", "WEDNESDAY", 
                      "THU", "THURSDAY", "FRI", "FRIDAY", "SAT", "SATURDAY"]

        # 2. Iterate through rows
        for index, row in df.iterrows():
            day_raw = str(row[0]).strip().upper()
            
            # Map "MON" -> "Monday" for the app
            if day_raw in ["MON", "MONDAY"]: day_key = "Monday"
            elif day_raw in ["TUE", "TUESDAY"]: day_key = "Tuesday"
            elif day_raw in ["WED", "WEDNESDAY"]: day_key = "Wednesday"
            elif day_raw in ["THU", "THURSDAY"]: day_key = "Thursday"
            elif day_raw in ["FRI", "FRIDAY"]: day_key = "Friday"
            elif day_raw in ["SAT", "SATURDAY"]: day_key = "Saturday"
            else: continue # Skip invalid rows

            if day_key not in schedule:
                schedule[day_key] = []

            # 3. Iterate columns (Time Slots)
            # We stop 1 column early to allow checking the "next_cell"
            for col_idx in range(1, len(row) - 1):
                current_cell = row[col_idx]
                next_cell = row[col_idx + 1]
                
                # Check if cell is valid (not empty/dash)
                if pd.notna(current_cell) and str(current_cell).strip() not in ["-", "nan", ""]:
                    
                    # --- THE DECISION LOGIC ---
                    # If next cell is Empty/NaN, it is a 2-Hour Lab
                    is_lab_lecture = pd.isna(next_cell) or str(next_cell).strip() in ["", "nan"]
                    
                    extracted_data = None

                    if is_lab_lecture:
                        # Call the NEW function
                        extracted_data = self._extract_lab(str(current_cell), user_batch)
                    else:
                        # Call the OLD function
                        extracted_data = self._extract_theory(str(current_cell))

                    # If we found valid data, add it to the list
                    if extracted_data:
                        schedule[day_key].append(extracted_data)

        return schedule

    def _extract_theory(self, cell_text):
        """
        Old Logic: Just cleans up the text for Theory lectures.
        """
        raw_text = cell_text.strip()
        
        # Filter out "Lunch" or "Break"
        if "LUNCH" in raw_text.upper():
            return "LUNCH"
            
        # Replace newlines with spaces so it fits in one line
        clean_text = raw_text.replace('\n', ' ')
        return clean_text

    def _extract_lab(self, cell_text, target_batch):
        """
        New Logic: Finds the specific batch line and returns 'Subject Room' string.
        """
        # Regex to find batch safely (e.g., "A1" followed by colon or space)
        batch_pattern = re.compile(rf"{re.escape(target_batch)}[:\s]", re.IGNORECASE)
        
        lines = cell_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 1. Search for the batch
            if batch_pattern.search(line):
                
                # 2. Tokenize (Split by words)
                tokens = re.split(r'\s+', line)
                
                # Find index of batch code (e.g. "A1:")
                for i, token in enumerate(tokens):
                    if target_batch in token:
                        try:
                            # We want the word AFTER batch (Subject) and 3rd word (Room)
                            # List: ['CSE', 'A1:', 'OOP', '(AK)', '(OSTL)']
                            # Index:   0      1      2       3        4
                            
                            # Safety check: make sure list is long enough
                            if len(tokens) > i + 3:
                                subject = tokens[i + 1].replace('(', '').replace(')', '')
                                room = tokens[i + 3].replace('(', '').replace(')', '')
                                return f"[LAB] {subject} {room}"
                            
                            elif len(tokens) > i + 1:
                                # Fallback if room is missing
                                subject = tokens[i + 1].replace('(', '').replace(')', '')
                                return f"[LAB] {subject}"
                                
                        except IndexError:
                            return None
        return None