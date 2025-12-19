import flet as ft
import sqlite3
from datetime import date
import os
import shutil 
import importer

# --- 1. DATABASE & UTILITY FUNCTIONS ---
def get_todays_sessions():
    """Fetch all classes scheduled for today."""
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT id, subject, status FROM sessions WHERE session_date = ?", (today_str,))
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"Database Error: {e}")
        return []

def update_status(session_id, new_status):
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", (new_status, session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Update Error: {e}")

# --- 2. MAIN APP STRUCTURE ---
def main(page: ft.Page):
    page.title = "SIT Attendance Manager"
    page.window_width = 400
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    # --- UI STATE VARIABLES ---
    uploaded_file_path = ft.Text("No file selected", size=12, color="grey")
    batch_input = ft.TextField(label="Batch Year (e.g., 2024)", width=280)

    # --- FILE PICKER HANDLER ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_name = e.files[0].name
            # In a real desktop app, we might copy this file to our project folder
            # For now, we just display the name to prove it worked
            uploaded_file_path.value = f"Selected: {file_name}"
            uploaded_file_path.update()
        else:
            uploaded_file_path.value = "Cancelled selection"
            uploaded_file_path.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # --- NAVIGATION FUNCTIONS ---
    def route_change(e):
        page.views.clear()
        
        # VIEW 1: LOGIN PAGE
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(name="school", size=60, color="blue"),
                                ft.Text("SIT Attendance", size=24, weight="bold"),
                                ft.Divider(height=20, color="transparent"),
                                username_input,
                                password_input,
                                ft.ElevatedButton("Login", on_click=login_click, width=280, bgcolor="blue", color="white"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            padding=50,
                            expand=True
                        )
                    ]
                )
            )

        # VIEW 2: UPLOAD PAGE
        elif page.route == "/upload":
            page.views.append(
                ft.View(
                    "/upload",
                    [
                        ft.AppBar(title=ft.Text("Setup Attendance"), bgcolor="surfaceVariant"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Step 1: Upload Excel Sheet", size=16, weight="bold"),
                                ft.ElevatedButton("Select File", icon="upload_file", on_click=lambda _: file_picker.pick_files(allow_multiple=False)),
                                uploaded_file_path,
                                ft.Divider(),
                                ft.Text("Step 2: Enter Batch", size=16, weight="bold"),
                                batch_input,
                                ft.Divider(height=40, color="transparent"),
                                ft.ElevatedButton("Process & Start", on_click=process_click, width=280, bgcolor="green", color="white")
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=30,
                            alignment=ft.alignment.center,
                            expand=True
                        )
                    ]
                )
            )

        # VIEW 3: MAIN APP (Your original code)
        elif page.route == "/app":
            # Load your original Tabs structure here
            load_sessions() # Refresh data
            page.views.append(
                ft.View(
                    "/app",
                    [
                        ft.Tabs(
                            selected_index=0,
                            animation_duration=300,
                            tabs=[
                                ft.Tab(text="Home", icon="home", content=home_tab),
                                ft.Tab(text="Settings", icon="settings", content=settings_tab),
                            ],
                            expand=True
                        )
                    ]
                )
            )
        
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # --- EVENT HANDLERS ---
    username_input = ft.TextField(label="Username", width=280)
    password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=280)

    def login_click(e):
        if username_input.value == "admin" and password_input.value == "sit123":
            page.go("/upload")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Invalid credentials!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    
    def process_click(e):
            if "No file" in uploaded_file_path.value:
                page.snack_bar = ft.SnackBar(ft.Text("Please upload a file first!"), bgcolor="orange")
                page.snack_bar.open = True
                page.update()
                return
                
            # --- THE CONNECTION IS HERE ---
            try:
                import importer  # This imports your importer.py file
                
                # This calls the main function in your importer.
                # CHECK: Does your importer.py have a function named 'process_excel' or 'main'?
                # Replace 'process_excel' below with whatever your function is actually named.
                importer.process_excel(uploaded_file_path.value, batch_input.value)
                
                page.snack_bar = ft.SnackBar(ft.Text("Processing Complete!"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
                
                # Move to the main app view to see the results
                page.go("/app")
                
            except Exception as err:
                # If something breaks in the importer, show the error on screen
                page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(err)}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
            
        # HERE IS WHERE YOU CONNECT YOUR BACKEND IMPORTER
        # import importer
        # importer.process(uploaded_file_path.value, batch_input.value)
        
    page.snack_bar = ft.SnackBar(ft.Text("Processing Complete!"), bgcolor="green")
    page.snack_bar.open = True
    page.update()
        
        # Move to the main app view
    page.go("/app")


    # --- YOUR ORIGINAL UI COMPONENTS (Preserved) ---
    sessions_column = ft.Column(spacing=10, scroll="auto", expand=True)
    
    # Header
    today_str = date.today().strftime("%A, %b %d")
    header_text = ft.Text(today_str, size=28, weight=ft.FontWeight.BOLD)
    
    # Home Tab Container
    home_tab = ft.Container(
        padding=10,
        content=ft.Column([
            header_text,
            ft.Divider(),
            sessions_column
        ], expand=True)
    )

    # Theme Switcher Logic
    def change_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.update()

    settings_tab = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Settings", size=24, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.Text("Dark Mode", size=18),
                ft.Switch(value=True, on_change=change_theme)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ElevatedButton("Logout", on_click=lambda _: page.go("/"), color="red")
        ])
    )

    # --- DATA LOADING (Your original logic) ---
    def load_sessions():
        sessions_column.controls.clear()
        classes = get_todays_sessions()

        if not classes:
            sessions_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(name="bedtime", size=50, color="grey"),
                        ft.Text("No classes today!", size=16, color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        else:
            for s_id, sub, status in classes:
                sessions_column.controls.append(create_class_card(s_id, sub, status))

    def create_class_card(s_id, sub_name, current_status):
        status_color = "green" if current_status == "Present" else "red" if current_status == "Absent" else "bluegrey"
        status_text = current_status if current_status != "Pending" else "Pending"
        icon_name = "science" if "[LAB]" in sub_name else "menu_book"
        icon_color = "purple" if "[LAB]" in sub_name else "blue"
        sub_name = sub_name.replace("[LAB]", "").strip()

        def on_present(e):
            update_status(s_id, "Present")
            load_sessions()
            page.update()

        def on_absent(e):
            update_status(s_id, "Absent")
            load_sessions()
            page.update()

        return ft.Container(
            padding=15, border_radius=10, bgcolor="surfaceVariant",
            content=ft.Column([
                ft.Row([
                    ft.Row([ft.Icon(name=icon_name, color=icon_color), ft.Text(sub_name, size=16, weight="bold")]),
                    ft.Container(content=ft.Text(status_text, size=10, color="white", weight="bold"), bgcolor=status_color, padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=5)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=20, color="grey"),
                ft.Row([
                    ft.ElevatedButton("Present", icon="check", on_click=on_present, color="white", bgcolor="green700"),
                    ft.ElevatedButton("Absent", icon="close", on_click=on_absent, color="white", bgcolor="red700"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ])
        )

    # --- INITIALIZATION ---
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

ft.app(target=main)