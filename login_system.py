import flet as ft
import importer
from datetime import datetime

def get_setup_view(page: ft.Page):
    # --- UI COMPONENTS ---
    name_input = ft.TextField(label="Full Name", icon=ft.Icons.PERSON)
    
    branch_input = ft.Dropdown(
        label="Branch",
        options=[ft.dropdown.Option(x) for x in ["CSE", "AIML", "ECE", "MECH"]],
        icon=ft.Icons.SCHOOL,
        expand=True
    )

    class_input = ft.Dropdown(
        label="Section",
        options=[ft.dropdown.Option(x) for x in ["A", "B", "C"]],
        icon=ft.Icons.CLASS_OUTLINED,
        expand=True
    )

    batch_input = ft.TextField(label="Batch (e.g., A1, B2)", icon=ft.Icons.GROUP)
    file_status = ft.Text("No file selected", color="grey", size=12)

    # Date Inputs (Text Fields for simplicity, usually cleaner than Pickers for initial setup)
    start_date_input = ft.TextField(
        label="Sem Start Date (YYYY-MM-DD)", 
        icon=ft.Icons.DATE_RANGE, 
        hint_text="2025-08-16",
        expand=True
    )
    end_date_input = ft.TextField(
        label="Sem End Date (YYYY-MM-DD)", 
        icon=ft.Icons.EVENT_BUSY, 
        hint_text="2026-01-02",
        expand=True
    )

    # --- LOGIC ---
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_status.value = e.files[0].path
            file_status.color = "green"
            file_status.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def start_setup(e):
        # Validation
        if not all([name_input.value, branch_input.value, class_input.value, 
                    batch_input.value, start_date_input.value, end_date_input.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Please fill in ALL fields!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        if "No file" in file_status.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please upload a file!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        try:
            # 1. Validate Date Format
            datetime.strptime(start_date_input.value, "%Y-%m-%d")
            datetime.strptime(end_date_input.value, "%Y-%m-%d")

            # 2. Process
            sheet_name = f"{branch_input.value}-{class_input.value}"
            
            count = importer.process_excel(
                file_status.value, 
                batch_input.value, 
                start_date_input.value, # Pass Start
                end_date_input.value,   # Pass End
                sheet_name=sheet_name
            )
            
            # 3. Save User Info
            page.client_storage.set("user_name", name_input.value)
            page.client_storage.set("setup_complete", True)
            
            page.go("/app")

        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Invalid Date Format! Use YYYY-MM-DD"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(err)}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # --- LAYOUT ---
    return ft.View(
        "/setup",
        [
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Icon(name=ft.Icons.ADMIN_PANEL_SETTINGS, size=60, color="blue"),
                    ft.Text("Welcome!", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("Setup your semester dates.", color="grey"),
                    ft.Divider(height=20, color="transparent"),
                    name_input,
                    ft.Row([branch_input, class_input]),
                    batch_input,
                    ft.Row([start_date_input, end_date_input]), # New Row for Dates
                    ft.Divider(height=20, color="transparent"),
                    ft.Text("Upload Timetable (Excel)", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton("Choose File", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files()),
                        file_status
                    ]),
                    ft.Divider(height=40, color="transparent"),
                    ft.ElevatedButton("Start Attendance", on_click=start_setup, width=400, height=50, bgcolor="blue", color="white")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
            )
        ]
    )