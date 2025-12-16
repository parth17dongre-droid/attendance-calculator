#app file for the gui 
import flet as ft
import sqlite3
from datetime import date

# --- 1. DATABASE FUNCTIONS ---
def get_todays_sessions():
    """Fetch all classes scheduled for today."""
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # FIX: Convert the Date Object to a String "YYYY-MM-DD"
        # This matches exactly what we saved in the database.
        today_str = date.today().strftime("%Y-%m-%d") 
        
        print(f"DEBUG: Querying database for date: {today_str}") 
        
        cursor.execute("SELECT id, subject, status FROM sessions WHERE session_date = ?", (today_str,))
        data = cursor.fetchall()
        
        print(f"DEBUG: Database found {len(data)} entries.") 
        
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

# --- 2. THE APP INTERFACE ---
def main(page: ft.Page):
    # Window Settings
    page.title = "SIT Attendance Manager"
    page.window_width = 400
    page.window_height = 700
    page.padding = 20
    
    # Start in Dark Mode by default
    page.theme_mode = ft.ThemeMode.DARK 
    
    # --- DYNAMIC HEADER (Day & Date) ---
    today_str = date.today().strftime("%A, %b %d")
    header_text = ft.Text(today_str, size=28, weight=ft.FontWeight.BOLD)

    # Container for the list of classes
    sessions_column = ft.Column(spacing=10, scroll="auto", expand=True)

    # Icon for the settings tab (defined early so we can update it)
    theme_icon = ft.Icon(name="dark_mode")

    # --- FUNCTION TO TOGGLE THEME ---
    def change_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon.name = "wb_sunny" # Sun icon
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon.name = "dark_mode" # Moon icon
        page.update()

    # --- FUNCTION TO LOAD DATA ---
    def load_sessions():
        sessions_column.controls.clear()
        classes = get_todays_sessions()

        if not classes:
            sessions_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(name="bedtime", size=50, color="grey"),
                        ft.Text("No classes today! Sleep well.", size=16, color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        else:
            for session_id, subject, status in classes:
                sessions_column.controls.append(create_class_card(session_id, subject, status))
        
        page.update()

    # --- CARD CREATOR ---
    def create_class_card(s_id, sub_name, current_status):
        
        status_color = "bluegrey"
        status_text = "Pending"
        
        # Default Icon (Book for Theory)
        icon_name = "menu_book"
        icon_color = "blue"

        # Check for [LAB] tag
        if "[LAB]" in sub_name:
            # Clean the name (remove the tag for display)
            sub_name = sub_name.replace("[LAB]", "").strip()
            # Change Icon to Flask
            icon_name = "science" 
            icon_color = "purple"
        
        if current_status == "Present": 
            status_color = "green"
            status_text = "PRESENT"
        elif current_status == "Absent": 
            status_color = "red"
            status_text = "ABSENT"

        def on_present(e):
            update_status(s_id, "Present")
            load_sessions()

        def on_absent(e):
            update_status(s_id, "Absent")
            load_sessions()

        return ft.Container(
            padding=15,
            border_radius=10,
            # Use string "surfaceVariant" to avoid version errors
            bgcolor="surfaceVariant", 
            content=ft.Column([
                # Row 1: Icon + Name + Status
                ft.Row([
                    ft.Row([
                        ft.Icon(name=icon_name, color=icon_color),
                        ft.Text(sub_name, size=16, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(
                        content=ft.Text(status_text, size=10, color="white", weight=ft.FontWeight.BOLD),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=5
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=20, color="grey"),
                
                # Row 2: Buttons
                ft.Row([
                    ft.ElevatedButton("Present", icon="check", on_click=on_present, 
                                      color="white", bgcolor="green700"),
                    ft.ElevatedButton("Absent", icon="close", on_click=on_absent, 
                                      color="white", bgcolor="red700"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ])
        )

    # --- LAYOUT: TABS ---
    # Tab 1: Home (The Schedule)
    home_tab = ft.Container(
        padding=10,
        content=ft.Column([
            header_text,
            ft.Divider(),
            sessions_column
        ], expand=True)
    )

    # Tab 2: Settings (Theme Switcher)
    settings_tab = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.Text("Theme Mode", size=18),
                ft.Switch(label="Dark Mode", value=True, on_change=change_theme)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text("Toggle to switch between Light and Dark themes.", size=12, color="grey")
        ])
    )

    # Add Tabs to Page
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Home", icon="home", content=home_tab),
            ft.Tab(text="Settings", icon="settings", content=settings_tab),
        ],
        expand=True
    )

    page.add(t)
    load_sessions()

ft.app(target=main)