import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
import config
from game_engine import GameEngine
from models import Club, Player

# --- COLORS & STYLES ---
COLORS = {
    "bg_dark": "#2C3E50",    # Sidebar
    "bg_light": "#ECF0F1",   # Main Content
    "card_bg": "#FFFFFF",    # Cards
    "primary": "#3498DB",    # Buttons/Highlights
    "success": "#27AE60",    # Good stats
    "warning": "#F1C40F",    # Average/Warning
    "danger": "#C0392B",     # Bad/Injured
    "text_dark": "#2C3E50",
    "text_light": "#ECF0F1",
    "text_muted": "#7F8C8D"
}

FORM_COLORS = {
    "W": "#27AE60",
    "L": "#C0392B",
    "T": "#7F8C8D"
}

class ModernGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cricket Club Manager v1 - Professional Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["bg_light"])
        
        self.game = GameEngine()
        self.game.initialize_game()
        self.managed_club = None
        self.current_view_func = self.view_dashboard # TRACK CURRENT VIEW
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.setup_styles()
        
        # Main Layout Container
        self.main_container = tk.Frame(self.root, bg=COLORS["bg_light"])
        self.main_container.pack(fill='both', expand=True)
        
        self.show_startup_screen()

    def setup_styles(self):
        # General
        self.style.configure("TFrame", background=COLORS["bg_light"])
        self.style.configure("Card.TFrame", background=COLORS["card_bg"], relief="flat")
        
        # Sidebar
        self.style.configure("Sidebar.TFrame", background=COLORS["bg_dark"])
        self.style.configure("Sidebar.TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_light"], font=("Segoe UI", 12))
        self.style.configure("Sidebar.TButton", background=COLORS["bg_dark"], foreground=COLORS["text_light"], 
                             font=("Segoe UI", 11), borderwidth=0, anchor="w", padding=10)
        self.style.map("Sidebar.TButton", background=[("active", COLORS["primary"])])
        
        # Headers
        self.style.configure("Header.TLabel", background=COLORS["bg_light"], foreground=COLORS["text_dark"], font=("Segoe UI", 24, "bold"))
        self.style.configure("CardHeader.TLabel", background=COLORS["card_bg"], foreground=COLORS["text_dark"], font=("Segoe UI", 14, "bold"))
        self.style.configure("CardValue.TLabel", background=COLORS["card_bg"], foreground=COLORS["primary"], font=("Segoe UI", 20, "bold"))
        self.style.configure("CardSub.TLabel", background=COLORS["card_bg"], foreground=COLORS["text_muted"], font=("Segoe UI", 10))
        
        # Treeview
        self.style.configure("Treeview", background="white", fieldbackground="white", foreground=COLORS["text_dark"], rowheight=30, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=COLORS["bg_light"])
        self.style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "white")])
        
        # Buttons
        self.style.configure("Action.TButton", background=COLORS["primary"], foreground="white", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.map("Action.TButton", background=[("active", "#2980B9")])

    def clear_window(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        
        def try_float(v):
            try:
                # Remove symbols for sorting
                clean = str(v).replace('$','').replace('K','').replace('%','').replace('Lvl ','')
                if '(+' in clean or '(' in clean: # Handle growth format "50 (+2)"
                    clean = clean.split('(')[0].strip()
                return float(clean)
            except ValueError:
                return v.lower()

        l.sort(key=lambda t: try_float(t[0]), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
            
        tv.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))

    # --- STARTUP SCREEN ---
    def show_startup_screen(self):
        self.clear_window()
        frame = tk.Frame(self.main_container, bg=COLORS["bg_dark"])
        frame.place(relx=0.5, rely=0.5, anchor="center", width=600, height=500)
        
        tk.Label(frame, text="CRICKET CLUB MANAGER", font=("Segoe UI", 28, "bold"), bg=COLORS["bg_dark"], fg=COLORS["text_light"]).pack(pady=(40, 10))
        tk.Label(frame, text="v1.0 | Professional Edition", font=("Segoe UI", 12), bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(pady=(0, 30))
        
        tk.Label(frame, text="Select Your Club:", font=("Segoe UI", 14), bg=COLORS["bg_dark"], fg=COLORS["text_light"]).pack(anchor="w", padx=50)
        
        # Listbox with Scrollbar
        list_frame = tk.Frame(frame, bg=COLORS["bg_dark"])
        list_frame.pack(pady=10, padx=50, fill="both", expand=True)
        
        sb = tk.Scrollbar(list_frame)
        sb.pack(side="right", fill="y")
        
        self.club_listbox = tk.Listbox(list_frame, font=("Consolas", 11), bg="#34495E", fg="white", 
                                       selectbackground=COLORS["primary"], borderwidth=0, highlightthickness=0, yscrollcommand=sb.set)
        self.club_listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self.club_listbox.yview)
        
        self.clubs_flat = []
        for div in config.DIVISIONS:
            self.club_listbox.insert(tk.END, f"--- {div} ---")
            self.clubs_flat.append(None) # Spacer
            for club in self.game.league.divisions[div]:
                self.clubs_flat.append(club)
                self.club_listbox.insert(tk.END, f"  {club.name}")
        
        btn_frame = tk.Frame(frame, bg=COLORS["bg_dark"])
        btn_frame.pack(pady=30)
        
        ttk.Button(btn_frame, text="NEW GAME", style="Action.TButton", command=self.start_game).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="LOAD GAME", style="Action.TButton", command=self.load_game_dialog).pack(side="left", padx=10)

    def load_game_dialog(self):
        if self.game.load_game():
            messagebox.showinfo("Success", "Game Loaded Successfully!")
            self.managed_club = self.game.managed_club
            self.setup_main_frame()
        else:
            messagebox.showerror("Error", "No savegame.json found.")

    def start_game(self):
        selection = self.club_listbox.curselection()
        if not selection: return
        club = self.clubs_flat[selection[0]]
        if not club: return # Header selected
        
        self.managed_club = club
        self.game.managed_club = club
        self.setup_main_frame()

    # --- MAIN DASHBOARD LAYOUT ---
    def setup_main_frame(self):
        self.clear_window()
        
        # 1. Sidebar (Left)
        self.sidebar = ttk.Frame(self.main_container, style="Sidebar.TFrame", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Sidebar Content
        tk.Label(self.sidebar, text="CCM v1", font=("Segoe UI", 20, "bold"), bg=COLORS["bg_dark"], fg=COLORS["text_light"]).pack(pady=30)
        
        menu_items = [
            ("Dashboard", self.view_dashboard),
            ("Squad", self.view_squad),
            ("Facilities & Staff", self.view_facilities),
            ("League Table", self.view_league),
            ("Finances", self.view_finances),
            ("History & Records", self.view_history)
        ]
        
        for label, cmd in menu_items:
            ttk.Button(self.sidebar, text=f"  {label}", style="Sidebar.TButton", command=cmd).pack(fill="x", pady=2)
            
        # Sidebar Footer
        tk.Label(self.sidebar, text="ACTIONS", font=("Segoe UI", 10, "bold"), bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(side="bottom", anchor="w", padx=20, pady=(0, 10))
        
        action_frame = tk.Frame(self.sidebar, bg=COLORS["bg_dark"])
        action_frame.pack(side="bottom", fill="x", padx=10, pady=20)
        
        ttk.Button(action_frame, text="PLAY WEEK", style="Action.TButton", command=self.play_week).pack(fill="x", pady=5)
        ttk.Button(action_frame, text="SAVE GAME", style="Action.TButton", command=self.save_game).pack(fill="x", pady=5)

        # 2. Header & Content (Right)
        self.right_panel = tk.Frame(self.main_container, bg=COLORS["bg_light"])
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Top Header
        self.header_frame = tk.Frame(self.right_panel, bg=COLORS["bg_light"], height=80)
        self.header_frame.pack(fill="x", padx=30, pady=20)
        self.header_label = ttk.Label(self.header_frame, text="", style="Header.TLabel")
        self.header_label.pack(side="left")
        
        self.sub_header = tk.Label(self.header_frame, text="", font=("Segoe UI", 12), bg=COLORS["bg_light"], fg=COLORS["text_muted"])
        self.sub_header.pack(side="left", padx=20, pady=(10, 0))

        # Content Area
        self.content_area = tk.Frame(self.right_panel, bg=COLORS["bg_light"])
        self.content_area.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.view_dashboard() # Default view

    def update_header(self):
        c = self.managed_club
        self.header_label.config(text=c.name)
        self.sub_header.config(text=f"{c.division} | Season {self.game.season_number} | Week {self.game.current_week}")

    def save_game(self):
        self.game.save_game()
        messagebox.showinfo("Saved", "Game saved successfully!")

    # --- VIEWS ---
    
    def _create_card(self, parent, title, value, subtext=None, width=250, height=150):
        card = ttk.Frame(parent, style="Card.TFrame", width=width, height=height)
        card.pack_propagate(False)
        
        ttk.Label(card, text=title, style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=(15, 5))
        ttk.Label(card, text=value, style="CardValue.TLabel").pack(anchor="w", padx=20, pady=0)
        if subtext:
            ttk.Label(card, text=subtext, style="CardSub.TLabel").pack(anchor="w", padx=20, pady=(5, 0))
        return card

    def _get_form_string(self, form_list):
        return " ".join(form_list) if form_list else "-"

    def view_dashboard(self):
        self.current_view_func = self.view_dashboard
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        c = self.managed_club
        
        # Top Row: KPI Cards
        kpi_frame = tk.Frame(self.content_area, bg=COLORS["bg_light"])
        kpi_frame.pack(fill="x", pady=10)
        
        standings = self.game.league.get_standings(c.division)
        pos = standings.index(c) + 1 if c in standings else "-"
        
        self._create_card(kpi_frame, "League Position", f"{pos}/{len(standings)}", "Top 2 Promote").pack(side="left", padx=(0, 20))
        self._create_card(kpi_frame, "Cash Balance", f"${c.cash}K", f"Wages: ${c.wage_bill}K/wk").pack(side="left", padx=20)
        self._create_card(kpi_frame, "Form", self._get_form_string(c.form), f"NRR: {c.net_run_rate:.2f}").pack(side="left", padx=20)
        self._create_card(kpi_frame, "Squad Size", f"{len(c.squad)}", f"Avg Age: {c.average_age:.1f}").pack(side="left", padx=20)

        # Bottom Row: News & Snapshot
        bottom_frame = tk.Frame(self.content_area, bg=COLORS["bg_light"])
        bottom_frame.pack(fill="both", expand=True, pady=20)
        
        # Left Panel: Table + Recent Results
        left_panel = tk.Frame(bottom_frame, bg=COLORS["bg_light"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Snapshot Card (SCROLLABLE)
        tbl_card = ttk.Frame(left_panel, style="Card.TFrame")
        tbl_card.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Label(tbl_card, text="Division Snapshot", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=15)
        
        cols = ("Pos", "Team", "P", "Pts", "Form")
        tv = ttk.Treeview(tbl_card, columns=cols, show="headings", height=8)
        for col in cols: 
            tv.heading(col, text=col)
            tv.column(col, width=40 if col != "Team" and col != "Form" else 150, anchor="center")
        tv.column("Team", anchor="w")
        
        sb = ttk.Scrollbar(tbl_card, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        
        tv.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        sb.pack(side="right", fill="y", pady=10, padx=(0, 10))
        
        for i, club in enumerate(standings):
            tv.insert("", "end", values=(i+1, club.name, club.played, club.points, self._get_form_string(club.form)), 
                      tags=("my_team",) if club == c else ())
        tv.tag_configure("my_team", background=COLORS["primary"], foreground="white")

        # Latest Results Card
        res_card = ttk.Frame(left_panel, style="Card.TFrame")
        res_card.pack(fill="both", expand=True, pady=(10, 0))
        ttk.Label(res_card, text="Latest Results / Fixtures", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=15)
        
        res_list = tk.Frame(res_card, bg="white")
        res_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        latest_results = [r for r in self.game.results if r.home_team.division == c.division][-5:]
        if latest_results:
            for r in reversed(latest_results):
                f = tk.Frame(res_list, bg="white")
                f.pack(fill="x", pady=2)
                tk.Label(f, text=f"{r.home_team.name} vs {r.away_team.name}", bg="white", font=("Segoe UI", 10)).pack(side="left")
                tk.Label(f, text=f"{r.home_score} - {r.away_score}", bg="white", font=("Segoe UI", 10, "bold"), fg=COLORS["primary"]).pack(side="right")
        else:
            round_idx = self.game.current_week - 1
            if c.division in self.game.fixtures and round_idx < len(self.game.fixtures[c.division]):
                for home, away in self.game.fixtures[c.division][round_idx]:
                    f = tk.Frame(res_list, bg="white")
                    f.pack(fill="x", pady=2)
                    tk.Label(f, text=f"{home.name} vs {away.name}", bg="white", font=("Segoe UI", 10)).pack(side="left")
                    tk.Label(f, text="UPCOMING", bg="white", font=("Segoe UI", 8, "italic"), fg=COLORS["text_muted"]).pack(side="right")
            else:
                tk.Label(res_list, text="No data available.", bg="white", font=("Segoe UI", 10, "italic")).pack()

        # Right Panel: Performers & Actions
        right_panel = tk.Frame(bottom_frame, bg=COLORS["bg_light"])
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Scorecard Button Card
        score_card_btn_card = ttk.Frame(right_panel, style="Card.TFrame")
        score_card_btn_card.pack(fill="x", pady=(0, 20))
        ttk.Label(score_card_btn_card, text="Last Match Analysis", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=15)
        
        my_last_match = next((r for r in reversed(self.game.results) if r.home_team == c or r.away_team == c), None)
        if my_last_match:
            tk.Label(score_card_btn_card, text=my_last_match.details, font=("Segoe UI", 10, "italic"), bg="white", wraplength=300).pack(padx=20, pady=(0, 10))
            ttk.Button(score_card_btn_card, text="VIEW SCORECARD", style="Action.TButton", command=lambda: self.show_scorecard_window(my_last_match)).pack(padx=20, pady=(0, 20), fill="x")
        else:
            tk.Label(score_card_btn_card, text="No matches played yet.", font=("Segoe UI", 10, "italic"), bg="white").pack(padx=20, pady=(0, 20))

        # Performers Card
        news_card = ttk.Frame(right_panel, style="Card.TFrame")
        news_card.pack(fill="both", expand=True)
        ttk.Label(news_card, text="Team Leaders", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=15)
        
        best_bat = max(c.squad, key=lambda p: p.season_runs, default=None)
        best_bowl = max(c.squad, key=lambda p: p.season_wickets, default=None)
        
        if best_bat and best_bat.season_runs > 0:
            tk.Label(news_card, text=f"Top Scorer: {best_bat.name}", font=("Segoe UI", 12, "bold"), bg="white", fg=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=5)
            tk.Label(news_card, text=f"{best_bat.season_runs} Runs @ Avg {best_bat.season_runs/max(1, best_bat.matches_played):.1f}", font=("Segoe UI", 10), bg="white", fg=COLORS["text_muted"]).pack(anchor="w", padx=20)
            
        if best_bowl and best_bowl.season_wickets > 0:
            tk.Label(news_card, text=f"Top Wicket Taker: {best_bowl.name}", font=("Segoe UI", 12, "bold"), bg="white", fg=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=(15, 5))
            tk.Label(news_card, text=f"{best_bowl.season_wickets} Wickets", font=("Segoe UI", 10), bg="white", fg=COLORS["text_muted"]).pack(anchor="w", padx=20)

    def view_squad(self):
        self.current_view_func = self.view_squad
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        # Squad Table Container
        card = ttk.Frame(self.content_area, style="Card.TFrame")
        card.pack(fill="both", expand=True)
        
        # Legend
        legend_frame = tk.Frame(card, bg="white")
        legend_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(legend_frame, text="Squad Overview (Click headers to sort)", font=("Segoe UI", 14, "bold"), bg="white").pack(side="left")
        
        cols = ("Name", "Role", "Age", "Ovr", "Bat", "Bowl", "Fld", "Fit", "Morale", "Wage", "Status")
        tv = ttk.Treeview(card, columns=cols, show="headings", height=20)
        
        for col in cols:
            tv.heading(col, text=col, command=lambda _c=col: self.treeview_sort_column(tv, _c, False))
            tv.column(col, width=60 if col not in ["Name", "Role"] else 150, anchor="center")
        
        tv.column("Name", anchor="w")
        
        vsb = ttk.Scrollbar(card, orient="vertical", command=tv.yview)
        tv.configure(yscroll=vsb.set)
        
        tv.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        vsb.pack(side="right", fill="y", pady=20, padx=(0, 20))
        
        # Tags for colors
        tv.tag_configure("elite", foreground=COLORS["success"])
        tv.tag_configure("good", foreground=COLORS["primary"])
        tv.tag_configure("injured", foreground=COLORS["danger"])
        
        for p in self.managed_club.squad:
            tag = "normal"
            if p.is_injured: tag = "injured"
            elif p.overall >= 80: tag = "elite"
            elif p.overall >= 60: tag = "good"
            
            status = f"Inj ({p.injury_duration}w)" if p.is_injured else "OK"
            
            tv.insert("", "end", values=(
                p.name, p.role, p.age, p.overall, 
                p.batting, p.bowling, p.fielding, 
                f"{p.fitness}%", f"{p.morale}%", f"${p.wage}K", status
            ), tags=(tag,))

    def view_facilities(self):
        self.current_view_func = self.view_facilities
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        c = self.managed_club
        
        # 1. Facilities
        fac_card = self._create_card(self.content_area, "Infrastructure", "", width=400, height=300)
        fac_card.pack(fill="x", pady=(0, 20))
        fac_card.pack_propagate(False) # Let content expand
        
        f_frame = tk.Frame(fac_card, bg="white")
        f_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def draw_level_bar(parent, label, level, max_level=10):
            row = tk.Frame(parent, bg="white")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, width=15, anchor="w", bg="white", font=("Segoe UI", 11)).pack(side="left")
            
            # Canvas for bar
            can = tk.Canvas(row, width=300, height=15, bg="#ECF0F1", highlightthickness=0)
            can.pack(side="left", padx=10)
            
            fill_width = (level / max_level) * 300
            can.create_rectangle(0, 0, fill_width, 15, fill=COLORS["primary"], outline="")
            
            tk.Label(row, text=f"Lvl {level}", bg="white", font=("Segoe UI", 11, "bold")).pack(side="left")

        draw_level_bar(f_frame, "Stadium", c.stadium_level, 5) 
        draw_level_bar(f_frame, "Academy", c.academy_level, 5)
        draw_level_bar(f_frame, "Medical", c.medical_level, 5)
        
        tk.Label(f_frame, text=f"Stadium Capacity: {c.stadium_capacity}", bg="white", fg=COLORS["text_muted"]).pack(anchor="w", pady=10)

        # 2. Staff
        staff_card = ttk.Frame(self.content_area, style="Card.TFrame")
        staff_card.pack(fill="both", expand=True)
        ttk.Label(staff_card, text="Coaching & Support Staff", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=15)
        
        cols = ("Name", "Role", "Skill", "Wage")
        tv = ttk.Treeview(staff_card, columns=cols, show="headings", height=8)
        for col in cols: 
            tv.heading(col, text=col, command=lambda _c=col: self.treeview_sort_column(tv, _c, False))
            tv.column(col, anchor="center")
        tv.pack(fill="both", expand=True, padx=20, pady=10)
        
        for s in c.staff:
            tv.insert("", "end", values=(s.name, s.role, s.skill, f"${s.wage}K"))

    def view_finances(self):
        self.current_view_func = self.view_finances
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        c = self.managed_club
        
        # Financial Overview Chart
        chart_card = ttk.Frame(self.content_area, style="Card.TFrame")
        chart_card.pack(fill="both", expand=True, pady=(0, 20))
        
        ttk.Label(chart_card, text="Cash History (Last 20 Weeks)", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=10)
        
        can = tk.Canvas(chart_card, bg="white", height=200, highlightthickness=0)
        can.pack(fill="x", padx=20, pady=10)
        
        history = c.history_cash[-20:]
        if len(history) > 1:
            w_can = 800
            h_can = 200
            min_val = min(history)
            max_val = max(history)
            range_val = max(1, max_val - min_val)
            
            can.create_line(0, h_can/2, w_can, h_can/2, fill="#ECF0F1")
            
            step_x = w_can / (len(history) - 1)
            prev_x, prev_y = 0, h_can - ((history[0] - min_val) / range_val * h_can)
            
            for i, val in enumerate(history[1:], 1):
                x = i * step_x
                y = h_can - ((val - min_val) / range_val * h_can)
                can.create_line(prev_x, prev_y, x, y, fill=COLORS["primary"], width=2)
                prev_x, prev_y = x, y
                
            tk.Label(chart_card, text=f"Start: ${history[0]}K  |  End: ${history[-1]}K", bg="white", fg=COLORS["text_muted"]).pack(pady=5)
        else:
            tk.Label(chart_card, text="Not enough history for chart", bg="white").pack(pady=50)

        # Breakdown Table
        break_card = ttk.Frame(self.content_area, style="Card.TFrame")
        break_card.pack(fill="x")
        
        ttk.Label(break_card, text="Weekly Expenses", style="CardHeader.TLabel").pack(anchor="w", padx=20, pady=10)
        
        def add_row(parent, label, val):
            f = tk.Frame(parent, bg="white")
            f.pack(fill="x", padx=20, pady=2)
            tk.Label(f, text=label, bg="white", font=("Segoe UI", 11)).pack(side="left")
            tk.Label(f, text=val, bg="white", font=("Segoe UI", 11, "bold")).pack(side="right")
            
        add_row(break_card, "Player Wages", f"${sum(p.wage for p in c.squad)}K")
        add_row(break_card, "Staff Wages", f"${sum(s.wage for s in c.staff)}K")
        
        maint = (c.stadium_level * 10) + (c.academy_level * 5) + (c.medical_level * 5)
        add_row(break_card, "Facility Maintenance", f"${maint}K")
        
        tk.Frame(break_card, height=1, bg=COLORS["bg_light"]).pack(fill="x", padx=20, pady=10)
        add_row(break_card, "Total Weekly Outflow", f"${c.wage_bill + maint}K")

    def view_league(self):
        self.current_view_func = self.view_league
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        card = ttk.Frame(self.content_area, style="Card.TFrame")
        card.pack(fill="both", expand=True)
        
        nb = ttk.Notebook(card)
        nb.pack(fill="both", expand=True, padx=20, pady=20)
        
        for div in config.DIVISIONS:
            f = tk.Frame(nb, bg="white")
            nb.add(f, text=div)
            
            cols = ("Pos", "Team", "P", "W", "L", "T", "Pts", "NRR", "Form")
            tv = ttk.Treeview(f, columns=cols, show="headings", height=20)
            for c in cols: 
                tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
                tv.column(c, width=50 if c not in ["Team", "Form", "NRR"] else (200 if c == "Team" else 150), anchor="center")
            tv.column("Team", anchor="w")
            tv.pack(fill="both", expand=True, padx=10, pady=10)
            
            standings = self.game.league.get_standings(div)
            for i, c in enumerate(standings):
                tag = "my_team" if c == self.managed_club else ""
                form_str = self._get_form_string(c.form)
                tv.insert("", "end", values=(i+1, c.name, c.played, c.won, c.lost, c.tied, c.points, f"{c.net_run_rate:.2f}", form_str), tags=(tag,))
            
            tv.tag_configure("my_team", background=COLORS["primary"], foreground="white")

    def view_history(self):
        self.current_view_func = self.view_history
        for w in self.content_area.winfo_children(): w.destroy()
        self.update_header()
        
        r = self.game.league.records
        
        card = self._create_card(self.content_area, "League Records", "", width=800, height=400)
        card.pack(fill="x", pady=20)
        
        stats = [
            ("Highest Team Score", r.highest_team_score_details),
            ("Highest Individual Score", r.highest_player_score_details),
            ("Best Bowling Figures", r.best_bowling_details),
            ("Most Runs (Season)", r.most_runs_season_details),
            ("Most Wickets (Season)", r.most_wickets_season_details)
        ]
        
        f = tk.Frame(card, bg="white")
        f.pack(fill="x", padx=20, pady=10)
        
        for lbl, val in stats:
            row = tk.Frame(f, bg="white")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=lbl, width=25, anchor="w", bg="white", fg=COLORS["primary"], font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(row, text=val, anchor="w", bg="white", font=("Segoe UI", 11)).pack(side="left")

    # --- ACTIONS ---
    def play_week(self):
        if self.game.current_week > config.MATCHES_PER_SEASON:
            if messagebox.askyesno("Season Over", "Season Finished. Start next season?"):
                self.game.end_season()
                self.view_dashboard()
            return

        results = self.game.advance_week()
        
        my_match = next((r for r in results if r.home_team == self.managed_club or r.away_team == self.managed_club), None)
        
        if not my_match:
            messagebox.showinfo("Bye Week", "No match for your team this week.")
        
        # REFRESH CURRENT VIEW INSTEAD OF FORCING DASHBOARD
        self.current_view_func()

    def show_scorecard_window(self, result):
        top = tk.Toplevel(self.root)
        top.title(f"{result.home_team.name} vs {result.away_team.name}")
        top.geometry("1000x850")
        top.configure(bg=COLORS["bg_light"])
        
        h = tk.Frame(top, bg=COLORS["bg_dark"], height=80)
        h.pack(fill="x")
        tk.Label(h, text=result.details, font=("Segoe UI", 18, "bold"), bg=COLORS["bg_dark"], fg="white").pack(pady=20)
        
        nb = ttk.Notebook(top)
        nb.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._add_innings_tab(nb, result.home_team.name, result.home_innings)
        self._add_innings_tab(nb, result.away_team.name, result.away_innings)

    def _add_innings_tab(self, nb, team_name, scorecard):
        f = tk.Frame(nb, bg="white")
        nb.add(f, text=team_name)
        
        if not scorecard: return
        
        tk.Label(f, text=f"Batting ({scorecard.total_runs}/{scorecard.wickets_lost})", font=("Segoe UI", 12, "bold"), bg="white", fg=COLORS["primary"]).pack(anchor="w", padx=10, pady=(10, 5))
        
        cols = ("Batter", "R", "B", "4s", "6s", "SR", "Status")
        tv = ttk.Treeview(f, columns=cols, show="headings", height=11)
        for c in cols: 
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
            tv.column(c, width=40 if c not in ["Batter", "Status"] else 120, anchor="center")
        tv.column("Batter", anchor="w")
        tv.pack(fill="x", padx=10)
        
        for s in scorecard.batting_stats:
            sr = f"{(s.runs/s.balls)*100:.1f}" if s.balls else "0.0"
            tv.insert("", "end", values=(s.player_name, s.runs, s.balls, s.fours, s.sixes, sr, "Out" if s.is_out else "not out"))

        tk.Label(f, text="Bowling", font=("Segoe UI", 12, "bold"), bg="white", fg=COLORS["primary"]).pack(anchor="w", padx=10, pady=(20, 5))
        
        bcols = ("Bowler", "O", "R", "W", "Econ")
        btv = ttk.Treeview(f, columns=bcols, show="headings", height=6)
        for c in bcols: 
            btv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(btv, _c, False))
            btv.column(c, width=50 if c != "Bowler" else 150, anchor="center")
        btv.column("Bowler", anchor="w")
        btv.pack(fill="x", padx=10)
        
        for s in scorecard.bowling_stats:
            econ = f"{s.runs_conceded/s.overs:.1f}" if s.overs else "0.0"
            btv.insert("", "end", values=(s.player_name, s.overs, s.runs_conceded, s.wickets, econ))

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernGUI(root)
    root.mainloop()
