import flet as ft
import sqlite3
from datetime import date
import os
import shutil

# --- UTILS ---
def get_todays_sessions():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, status FROM sessions WHERE session_date = ?", (date.today().strftime("%Y-%m-%d"),))
    data = cursor.fetchall()
    conn.close()
    return data

def update_status_db(s_id, status):
    conn = sqlite3.connect("attendance.db")
    conn.execute("UPDATE sessions SET status = ? WHERE id = ?", (status, s_id))
    conn.commit()
    conn.close()

# --- MAIN APP ---
def main(page: ft.Page):
    page.title = "SIT Attendance"
    page.window_width = 400
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- 1. SETUP PAGE COMPONENTS ---
    name_input = ft.TextField(label="Full Name", icon="person")
    class_input = ft.Dropdown(label="Class", options=[
        ft.dropdown.Option("CSE"), ft.dropdown.Option("AIML"), 
        ft.dropdown.Option("ECE"), ft.dropdown.Option("MECH")
    ], icon="school")
    batch_input = ft.TextField(label="Batch (e.g., A1, B2)", icon="group")
    
    file_status = ft.Text("No file selected", color="grey", size=12)
    
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_status.value = e.files[0].path
            file_status.color = "green"
            file_status.update()
    
    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def finish_setup(e):
        if not name_input.value or not batch_input.value or "No file" in file_status.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please fill all details!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        try:
            # 1. Run the Backend Importer
            import importer
            count = importer.process_excel(file_status.value, batch_input.value)
            
            # 2. Save User Details locally
            page.client_storage.set("user_name", name_input.value)
            page.client_storage.set("user_batch", batch_input.value)
            page.client_storage.set("setup_complete", True)

            page.snack_bar = ft.SnackBar(ft.Text(f"Setup Complete! Added {count} classes."), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            
            # 3. Go to App
            page.go("/app")
            
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(err)}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # --- 2. MAIN APP COMPONENTS ---
    sessions_col = ft.Column(scroll="auto", expand=True)

    def load_data():
        sessions_col.controls.clear()
        data = get_todays_sessions()
        
        # User Greeting
        user_name = page.client_storage.get("user_name") or "Student"
        sessions_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Hi, {user_name} 👋", size=24, weight="bold"),
                    ft.Text(date.today().strftime("%A, %b %d"), size=16, color="grey"),
                    ft.Divider(height=20, color="transparent"),
                ]), padding=20
            )
        )

        if not data:
            sessions_col.controls.append(ft.Container(content=ft.Text("No classes today!", size=16, color="grey"), alignment=ft.alignment.center, padding=50))
        
        for s_id, sub, status in data:
            # Card Logic
            icon = "science" if "[LAB]" in sub else "menu_book"
            color = "green" if status == "Present" else "red" if status == "Absent" else "surfaceVariant"
            
            c = ft.Container(
                padding=15, border_radius=10, bgcolor="surfaceVariant",
                content=ft.Column([
                    ft.Row([ft.Icon(icon), ft.Text(sub, weight="bold", size=16)], alignment="start"),
                    ft.Row([
                        ft.ElevatedButton("Present", on_click=lambda e, sid=s_id: mark(sid, "Present"), bgcolor="green", color="white"),
                        ft.ElevatedButton("Absent", on_click=lambda e, sid=s_id: mark(sid, "Absent"), bgcolor="red", color="white")
                    ], alignment="spaceBetween", margin=ft.margin.only(top=10))
                ])
            )
            sessions_col.controls.append(c)
        page.update()

    def mark(s_id, status):
        update_status_db(s_id, status)
        load_data()

    # --- 3. ROUTING ---
    def route_change(route):
        page.views.clear()
        
        # VIEW: SETUP
        if page.route == "/setup":
            page.views.append(
                ft.View(
                    "/setup",
                    [
                        ft.Container(
                            padding=30,
                            content=ft.Column([
                                ft.Icon(name="school", size=80, color="blue"),
                                ft.Text("Welcome!", size=30, weight="bold"),
                                ft.Text("Let's set up your profile.", color="grey"),
                                ft.Divider(height=20, color="transparent"),
                                name_input,
                                class_input,
                                batch_input,
                                ft.Divider(height=10, color="transparent"),
                                ft.Text("Upload Timetable (Excel)", weight="bold"),
                                ft.Row([
                                    ft.ElevatedButton("Choose File", icon="upload", on_click=lambda _: file_picker.pick_files()),
                                    file_status
                                ]),
                                ft.Divider(height=30, color="transparent"),
                                ft.ElevatedButton("Start Attendance", on_click=finish_setup, width=400, height=50, bgcolor="blue", color="white")
                            ])
                        )
                    ]
                )
            )
        
        # VIEW: APP
        elif page.route == "/app":
            load_data()
            page.views.append(
                ft.View(
                    "/app",
                    [
                        sessions_col,
                        ft.FloatingActionButton(icon="settings", on_click=lambda _: clear_data())
                    ]
                )
            )
        page.update()

    def clear_data():
        # Reset everything (Logout)
        page.client_storage.clear()
        page.go("/setup")

    # --- INITIAL CHECK ---
    page.on_route_change = route_change
    
    if page.client_storage.contains_key("setup_complete"):
        page.go("/app")
    else:
        page.go("/setup")

ft.app(target=main)