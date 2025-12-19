import flet as ft
import sqlite3
from datetime import date
import login_system

# --- DATABASE LOGIC ---
def get_todays_sessions():
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT id, subject, status, points FROM sessions WHERE session_date = ?", (today_str,))
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"DB Error: {e}")
        return []

def update_status(session_id, new_status):
    conn = sqlite3.connect("attendance.db")
    conn.execute("UPDATE sessions SET status = ? WHERE id = ?", (new_status, session_id))
    conn.commit()
    conn.close()

def get_overall_stats():
    """Calculates Overall Points-based attendance."""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Filter out ELH from calculations entirely
    cursor.execute("SELECT SUM(points) FROM sessions WHERE status = 'Present' AND subject != 'ELH'")
    earned = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(points) FROM sessions WHERE status = 'Absent' AND subject != 'ELH'")
    lost = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(points) FROM sessions WHERE status = 'Pending' AND subject != 'ELH'")
    future = cursor.fetchone()[0] or 0
    
    conn.close()
    
    total_conducted = earned + lost
    total_semester = earned + lost + future
    
    current_pct = (earned / total_conducted * 100) if total_conducted > 0 else 0.0
    max_pct = ((earned + future) / total_semester * 100) if total_semester > 0 else 0.0
    min_pct = (earned / total_semester * 100) if total_semester > 0 else 0.0
    
    return earned, total_semester, current_pct, max_pct, min_pct

def get_subject_stats():
    """Calculates attendance per individual subject (Excluding ELH)."""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # FETCH ALL SESSIONS (Pending included) so we see every subject
    cursor.execute("SELECT subject, status, points FROM sessions")
    data = cursor.fetchall()
    conn.close()
    
    stats = {}
    for sub, status, pts in data:
        clean_name = sub.replace("[LAB]", "").strip()
        
        # --- LOGIC FIX: REMOVE ELH ---
        if clean_name == "ELH":
            continue
            
        if clean_name not in stats:
            # earned = points got, conducted = points finished, future = points pending
            stats[clean_name] = {'earned': 0, 'conducted': 0, 'future': 0}
        
        if status == 'Present':
            stats[clean_name]['earned'] += pts
            stats[clean_name]['conducted'] += pts
        elif status == 'Absent':
            stats[clean_name]['conducted'] += pts
        elif status == 'Pending':
            stats[clean_name]['future'] += pts
            
    return stats

# --- UI COMPONENTS ---
def main(page: ft.Page):
    page.title = "SIT Attendance Pro"
    page.window_width = 420
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- TAB CONTENTS ---
    home_column = ft.Column(spacing=10, scroll="auto", expand=True)
    stats_column = ft.Column(spacing=10, scroll="auto", expand=True)
    settings_column = ft.Column(spacing=10, scroll="auto", expand=True)

    def load_home_tab():
        home_column.controls.clear()
        
        user_name = page.client_storage.get("user_name") or "Student"
        home_column.controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"Hi, {user_name} 👋", size=24, weight="bold"),
                ft.Text(date.today().strftime("%A, %b %d"), size=16, color="grey"),
            ]), padding=20
        ))

        classes = get_todays_sessions()
        
        if not classes:
            home_column.controls.append(ft.Container(
                content=ft.Column([
                    ft.Icon(name=ft.Icons.BEDTIME, size=50, color="grey"),
                    ft.Text("No classes today!", size=16, color="grey")
                ], horizontal_alignment="center"), alignment=ft.alignment.center, padding=50
            ))
        else:
            for s_id, sub, status, pts in classes:
                home_column.controls.append(create_class_card(s_id, sub, status, pts))
        
        page.update()

    def show_subject_details(sub_name, data):
        # DEBUG: Print to terminal to confirm click works
        print(f"Clicked on: {sub_name}") 
        
        earned = data['earned']
        conducted = data['conducted']
        future = data['future']
        total_sem = conducted + future

        # Calculate percentages
        current = (earned / conducted * 100) if conducted > 0 else 0.0
        max_possible = ((earned + future) / total_sem * 100) if total_sem > 0 else 0.0
        min_possible = (earned / total_sem * 100) if total_sem > 0 else 0.0

        # Create the Dialog UI
        dlg = ft.AlertDialog(
            title=ft.Text(sub_name, weight="bold"),
            content=ft.Container(
                width=300, # Force width
                content=ft.Column([
                    ft.Text(f"Current: {current:.1f}%", size=20, weight="bold"),
                    ft.Divider(),
                    
                    ft.Row([
                        ft.Text("Max Possible:", color="grey"),
                        ft.Text(f"{max_possible:.1f}%", color="green", weight="bold")
                    ], alignment="spaceBetween"),
                    
                    ft.Row([
                        ft.Text("Min Possible:", color="grey"),
                        ft.Text(f"{min_possible:.1f}%", color="red", weight="bold")
                    ], alignment="spaceBetween"),
                    
                    ft.Divider(),
                    ft.Text(f"Total Points: {total_sem}", size=12, italic=True, color="grey"),
                ], tight=True, spacing=10)
            ),
            actions=[
                # UPDATED CLOSE ACTION
                ft.TextButton("Close", on_click=lambda e: page.close(dlg)) 
            ],
            actions_alignment="end",
        )

        # --- UPDATED OPENING LOGIC ---
        # This handles both new and old Flet versions safely
        try:
            page.open(dlg)
        except AttributeError:
            # Fallback for older Flet versions
            page.dialog = dlg
            dlg.open = True
            page.update()

    def load_stats_tab():
        stats_column.controls.clear()
        
        # 1. OVERALL DASHBOARD
        earned, total_sem, curr_pct, max_pct, min_pct = get_overall_stats()
        color = "green" if curr_pct >= 75 else "orange" if curr_pct >= 60 else "red"
        
        overall_card = ft.Container(
            padding=20, border_radius=15, bgcolor="surfaceVariant",
            content=ft.Column([
                ft.Text("Overall Attendance", size=16, weight="bold"),
                ft.Divider(height=10, color="transparent"),
                ft.Row([
                    ft.Column([
                        ft.Text(f"{curr_pct:.1f}%", size=40, weight="bold", color=color),
                        ft.Text(f"Points: {earned}/{total_sem}", size=12, color="grey")
                    ]),
                    ft.Stack([
                        ft.PieChart(
                            sections=[
                                ft.PieChartSection(curr_pct, color=color, radius=8), 
                                ft.PieChartSection(100-curr_pct, color="#1A808080", radius=8)
                            ],
                            sections_space=0, center_space_radius=25, height=70, width=70,
                        ),
                        ft.Container(content=ft.Icon(ft.Icons.ANALYTICS, color=color), alignment=ft.alignment.center, width=70, height=70)
                    ])
                ], alignment="spaceBetween"),
                ft.Divider(),
                ft.Row([
                    ft.Column([ft.Text("Max Possible", size=10, color="grey"), ft.Text(f"{max_pct:.1f}%", color="green")]),
                    ft.Column([ft.Text("Min Possible", size=10, color="grey"), ft.Text(f"{min_pct:.1f}%", color="red")])
                ], alignment="spaceAround")
            ])
        )
        stats_column.controls.append(overall_card)
        stats_column.controls.append(ft.Text("Subject-wise Performance", size=16, weight="bold"))

        # 2. SUBJECT LIST
        subject_data = get_subject_stats()
        if not subject_data:
            stats_column.controls.append(ft.Text("No data found.", color="grey"))
        else:
            for sub_name, data in subject_data.items():
                conducted = data['conducted']
                earned_pts = data['earned']
                
                if conducted > 0:
                    pct = (earned_pts / conducted * 100)
                    bar_color = "green" if pct >= 75 else "orange" if pct >= 60 else "red"
                    label_text = f"{pct:.1f}%"
                    progress_val = pct/100
                else:
                    bar_color = "grey"
                    label_text = "No classes yet"
                    progress_val = 0
                
                # --- NEW CLICKABLE CONTAINER ---
                stats_column.controls.append(ft.Container(
                    padding=15, 
                    border_radius=10, 
                    bgcolor="surfaceVariant",
                    # Binds the click event to open the details dialog
                    on_click=lambda e, n=sub_name, d=data: show_subject_details(n, d),
                    ink=True, 
                    content=ft.Column([
                        ft.Row([
                            ft.Text(sub_name, weight="bold", expand=True),
                            ft.Text(label_text, color=bar_color, weight="bold")
                        ]),
                        ft.ProgressBar(value=progress_val, color=bar_color, bgcolor="#1A808080")
                    ])
                ))
        page.update()

    def create_class_card(s_id, sub_name, current_status, points):
        clean_name = sub_name.replace("[LAB]", "").strip()
        icon = ft.Icons.SCIENCE if "[LAB]" in sub_name else ft.Icons.BOOK
        
        present_bg = "green" if current_status == "Present" else "surface"
        absent_bg = "red" if current_status == "Absent" else "surface"
        
        return ft.Container(
            padding=15, border_radius=10, bgcolor="surfaceVariant",
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color="blue"), 
                    ft.Column([
                        ft.Text(clean_name, weight="bold", size=16),
                        ft.Text(f"{points} Points", size=12, color="grey")
                    ], expand=True),
                ]),
                ft.Divider(height=10, color="transparent"),
                ft.Row([
                    ft.ElevatedButton(
                        "Present", 
                        icon=ft.Icons.CHECK, 
                        bgcolor=present_bg, 
                        color="white" if current_status == "Present" else "green",
                        on_click=lambda e: mark(s_id, "Present"),
                        expand=True
                    ),
                    ft.Container(width=10), 
                    ft.ElevatedButton(
                        "Absent", 
                        icon=ft.Icons.CLOSE, 
                        bgcolor=absent_bg, 
                        color="white" if current_status == "Absent" else "red",
                        on_click=lambda e: mark(s_id, "Absent"),
                        expand=True
                    ),
                ])
            ])
        )

    def mark(s_id, status):
        update_status(s_id, status)
        load_home_tab()

    # --- NAVIGATION ---
    def route_change(route):
        page.views.clear()
        
        if page.route == "/setup":
            page.views.append(login_system.get_setup_view(page))
        
        elif page.route == "/app":
            load_home_tab()
            
            def on_tab_change(e):
                idx = e.control.selected_index
                if idx == 0: load_home_tab()
                elif idx == 1: load_stats_tab()
                page.update()

            page.views.append(ft.View("/app", [
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    on_change=on_tab_change,
                    tabs=[
                        ft.Tab(text="Home", icon=ft.Icons.HOME, content=ft.Container(padding=10, content=home_column)),
                        ft.Tab(text="Records", icon=ft.Icons.INSERT_CHART, content=ft.Container(padding=10, content=stats_column)),
                        ft.Tab(text="Settings", icon=ft.Icons.SETTINGS, content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.Text("Settings", size=24, weight="bold"),
                                ft.Divider(),
                                ft.ElevatedButton("Logout / Reset App", color="red", on_click=lambda _: page.go("/setup"))
                            ])
                        )),
                    ],
                    expand=True
                )
            ]))
        page.update()

    page.on_route_change = route_change
    
    if page.client_storage.contains_key("setup_complete"):
        page.go("/app")
    else:
        page.go("/setup")

ft.app(target=main)
