#importer file
import pandas as pd
import datetime
import re
class ExcelImporter:
    def parse_excel(self, file_path, sheet_name=0):
        try:
            # 1. Read the Excel File
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            
            df.iloc[:, 0] = df.iloc[:, 0].ffill()
            
            # NOW it is safe to fill the rest with dashes
            df = df.fillna("-")
            
            weekly_schedule = {}
            ignore_list = ["-", "nan", "lunch", "break"] 

            def get_day_from_cell(cell_val):
                if isinstance(cell_val, (pd.Timestamp, datetime.date, datetime.datetime)):
                    return cell_val.strftime("%A")
                text = str(cell_val).strip().upper()
                if text in ["MON", "MONDAY"]: return "Monday"
                if text in ["TUE", "TUESDAY"]: return "Tuesday"
                if text in ["WED", "WEDNESDAY"]: return "Wednesday"
                if text in ["THU", "THURSDAY"]: return "Thursday"
                if text in ["FRI", "FRIDAY"]: return "Friday"
                if text in ["SAT", "SATURDAY"]: return "Saturday"
                if text in ["SUN", "SUNDAY"]: return "Sunday"
                return None

            for index, row in df.iterrows():
                first_cell = row[0]
                day_name = get_day_from_cell(first_cell)
                
                if day_name:
                    # Initialize list if new day
                    if day_name not in weekly_schedule:
                        weekly_schedule[day_name] = []
                    
                    subjects = []
                    for cell_value in row[1:]:
                        raw_text = str(cell_value).strip()
                        clean_text = raw_text.lower()
                        
                        is_ignored = any(x in clean_text for x in ignore_list)
                        if not is_ignored and len(clean_text) > 2:
                            # Add to the day's list (allows multiple rows per day)
                            weekly_schedule[day_name].append(raw_text)

            return weekly_schedule

        except Exception as e:
            print(f"❌ Error parsing Excel: {e}")
            return None

    import pandas as pd
import datetime
import re

class ExcelImporter:
    def get_filtered_schedule(self, full_schedule, user_batch):
        cleaned_schedule = {}
        
        possible_batches = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
        
        all_batches_pattern = "|".join(re.escape(b) for b in possible_batches)
        
        user_pattern = re.compile(
            rf"({re.escape(user_batch)}[\:\s\/\-].*?)(\n|{all_batches_pattern}|\Z)",
            re.IGNORECASE | re.DOTALL
        )
        
        for day, subject_list in full_schedule.items():
            daily_classes = []
            
            for cell_text in subject_list:
                raw_text = str(cell_text).strip()
                
                is_batch_specific = any(b in raw_text for b in possible_batches)
                if not is_batch_specific:
                    if len(raw_text) > 2:
                        daily_classes.append(raw_text)
                    continue

                normalized_text = raw_text.replace('\n', ' | ').replace(' / ', ' | ')
                
                sections = [s.strip() for s in normalized_text.split(' | ') if s.strip()]
                
                found_class = None
                for section in sections:
                    if section.startswith(user_batch) or f" {user_batch}:" in section or f" {user_batch} " in section:
                        found_class = section
                        break

                if found_class:
                    is_lab = any(kw in found_class.upper() for kw in ["LAB", "PRACTICAL", "TUTORIAL", "TUTE", "CL"])
                    
                    if not is_lab:
                        pass 

                    final_subject_tagged = f"[LAB] {found_class}"
                    daily_classes.append(final_subject_tagged)

            if daily_classes:
                cleaned_schedule[day] = daily_classes

        return cleaned_schedule