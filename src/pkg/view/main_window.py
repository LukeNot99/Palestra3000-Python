import customtkinter as ctk
import os
from datetime import datetime, timedelta
from PIL import Image

from src.pkg.config.app_config import ConfigManager
from src.pkg.utility.utils import resource_path

from src.pkg.view.soci_window import MembersView
from src.pkg.view.tariffe_window import TiersView
from src.pkg.view.attivita_window import ActivitiesView
from src.pkg.view.lezioni_window import LessonsView
from src.pkg.view.calendario_window import CalendarView
from src.pkg.view.tornello_window import TurnstileView
from src.pkg.view.settings_window import SettingsView

class App(ctk.CTk):
    def __init__(self, di):
        super().__init__()
        self.di = di
        
        self.title("Palestra 3000 - Gestione")
        self.geometry("1350x850") 
        self.configure(fg_color=(ConfigManager.get_colors().get("bg_color", "#F2F2F7"), "#1C1C1E")) 
        self.icons_dir = resource_path("icons")
        
        self.access_history = [] 

        ui_callbacks = {
            "toast": self.show_toast_notification,
            "log": self.register_log,
            "update_counter": self.trigger_counter_update
        }

        self.access_manager = self.di.get_access_manager(ui_callbacks)
        self.reader_hw = self.di.get_reader_hardware()

        if self.reader_hw:
            self.reader_hw.start_listening(
                lambda badge: self.after(0, self.access_manager.process_badge, badge, self.get_current_settings())
            )

        self.bind_all("<F12>", lambda e: self.access_manager.process_manual_open())

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=("#FFFFFF", "#2C2C2E"), border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) 
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(10, weight=1) 

        self.logo_container = None
        self.update_logo() 

        ctk.CTkLabel(self.sidebar, text="QUOTIDIANO", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D")).grid(row=1, column=0, padx=24, pady=(0, 10), sticky="w")

        self.views = {} 
        self.menu_buttons = {}
        self.current_view_name = None
        self.current_frame = None

        self.create_menu_button("dashboard", "Dashboard", "dashboard", row=2)
        self.create_menu_button("tornello", "Controllo Accessi", "turnstile", row=3)
        self.create_menu_button("soci", "Anagrafica Soci", "members", row=4)
        self.create_menu_button("calendario", "Calendario Corsi", "calendar", row=5)

        ctk.CTkLabel(self.sidebar, text="AMMINISTRAZIONE", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D")).grid(row=6, column=0, padx=24, pady=(30, 10), sticky="w")

        self.create_menu_button("lezioni", "Piani Settimanali", "lessons", row=7)
        self.create_menu_button("tariffe", "Tariffario e Costi", "tiers", row=8)
        self.create_menu_button("attivita", "Gestione Attività", "activities", row=9)
        self.create_menu_button("impostazioni", "Impostazioni", "settings", row=10, extra_pady=(2, 20))

        self.main_content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.show_view("dashboard")

    def get_current_settings(self):
        return {
            "blocco_iscr": ConfigManager.get_setting("blocco_iscr", True),
            "blocco_abb": ConfigManager.get_setting("blocco_abb", True),
            "blocco_orari": ConfigManager.get_setting("blocco_orari", True),
            "blocco_cert": ConfigManager.get_setting("blocco_cert", False)
        }

    def update_logo(self):
        if self.logo_container: self.logo_container.destroy()
        self.logo_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_container.grid(row=0, column=0, padx=20, pady=(30, 30), sticky="ew")
        
        logo_path = ConfigManager.get_setting("percorso_logo", "")
        gym_name = ConfigManager.get_setting("nome_palestra", "Palestra 3000")

        if logo_path and os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((220, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                lbl_img = ctk.CTkLabel(self.logo_container, text="", image=ctk_img)
                lbl_img.pack(anchor="w", pady=(0, 10))
            except Exception: pass 

        self.lbl_gym_name = ctk.CTkLabel(self.logo_container, text=gym_name, font=ctk.CTkFont(family="Montserrat", size=22, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"), wraplength=220, justify="left")
        self.lbl_gym_name.pack(anchor="w")

    def show_view(self, view_name):
        if self.current_view_name == view_name: return
        self.current_view_name = view_name
        
        for name, data in self.menu_buttons.items():
            btn_f, l_icon, l_text = data
            if name == view_name:
                btn_f.configure(fg_color=("#F2F2F7", "#3A3A3C"))
                l_icon.configure(text_color=("#007AFF", "#0A84FF"))
                l_text.configure(text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"))
            else:
                btn_f.configure(fg_color="transparent")
                l_icon.configure(text_color=("#1D1D1F", "#FFFFFF"))
                l_text.configure(text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", size=14, weight="normal"))
        
        if self.current_frame: self.current_frame.pack_forget()
            
        if view_name not in self.views:
            if view_name == "settings": self.views[view_name] = SettingsView(self.main_content, self)
            elif view_name == "turnstile": self.views[view_name] = TurnstileView(self.main_content, self.access_manager, self.access_history, app=self)
            elif view_name == "members": self.views[view_name] = MembersView(self.main_content, self)
            elif view_name == "tiers": self.views[view_name] = TiersView(self.main_content, self)
            elif view_name == "activities": self.views[view_name] = ActivitiesView(self.main_content, self)
            elif view_name == "lessons": self.views[view_name] = LessonsView(self.main_content, self)
            elif view_name == "calendar": self.views[view_name] = CalendarView(self.main_content, self)
            elif view_name == "dashboard": self.views[view_name] = DashboardView(self.main_content, self)

        self.current_frame = self.views[view_name]
        self.current_frame.pack(fill="both", expand=True)

        if hasattr(self.current_frame, "load_data"): self.current_frame.load_data()
        elif hasattr(self.current_frame, "load_table"): self.current_frame.load_table()
        elif hasattr(self.current_frame, "load_stats"): self.current_frame.load_stats()
        elif hasattr(self.current_frame, "draw_calendar"): self.current_frame.draw_calendar()

        if view_name == "turnstile" and hasattr(self.current_frame, "update_in_facility_counter"):
            self.current_frame.update_in_facility_counter()

    def create_menu_button(self, icon_name, text, view_name, row, extra_pady=(2,2)):
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", corner_radius=8, height=42, cursor="hand2")
        btn_frame.grid(row=row, column=0, padx=15, pady=extra_pady, sticky="ew")
        btn_frame.pack_propagate(False)
        
        icon_img = self.load_icon(icon_name, 20)
        if icon_img: lbl_icon = ctk.CTkLabel(btn_frame, text="", image=icon_img, width=35, anchor="center")
        else: lbl_icon = ctk.CTkLabel(btn_frame, text="▪", font=ctk.CTkFont(family="Montserrat", size=18), text_color=("#1D1D1F", "#FFFFFF"), width=35, anchor="center")
        lbl_icon.pack(side="left", padx=(10, 0))
        
        lbl_text = ctk.CTkLabel(btn_frame, text=text, font=ctk.CTkFont(family="Montserrat", size=14, weight="normal"), text_color=("#1D1D1F", "#FFFFFF"), anchor="w")
        lbl_text.pack(side="left", fill="x", expand=True, padx=(5, 10))
        
        def on_click(e): self.show_view(view_name)
        def on_enter(e): 
            if self.current_view_name != view_name: btn_frame.configure(fg_color=("#F2F2F7", "#3A3A3C"))
        def on_leave(e): 
            if self.current_view_name != view_name: btn_frame.configure(fg_color="transparent")

        for w in [btn_frame, lbl_icon, lbl_text]:
            w.bind("<Button-1>", on_click); w.bind("<Enter>", on_enter); w.bind("<Leave>", on_leave)
            
        self.menu_buttons[view_name] = (btn_frame, lbl_icon, lbl_text)

    def load_icon(self, base_name, size):
        path_light = os.path.join(self.icons_dir, f"{base_name}_black.png")
        path_dark = os.path.join(self.icons_dir, f"{base_name}_white.png")
        path_single = os.path.join(self.icons_dir, f"{base_name}.png")
        try:
            if os.path.exists(path_light) and os.path.exists(path_dark): return ctk.CTkImage(light_image=Image.open(path_light), dark_image=Image.open(path_dark), size=(size, size))
            elif os.path.exists(path_single): return ctk.CTkImage(light_image=Image.open(path_single), dark_image=Image.open(path_single), size=(size, size))
        except Exception: pass
        return None

    def register_log(self, message):
        self.access_history.append(message)
        if "turnstile" in self.views:
            self.views["turnstile"].add_log(message, skip_history=True)
        else:
            # Se la view del tornello non è ancora stata creata, la creiamo ora
            # per assicurarci che il log venga visualizzato quando l'utente navigherà lì
            pass  # Il messaggio è già stato aggiunto ad access_history, verrà mostrato all'apertura

    def trigger_counter_update(self):
        if "turnstile" in self.views:
            self.views["turnstile"].update_in_facility_counter()

    def show_toast_notification(self, title, message, bg_color):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True) 
        toast.attributes('-topmost', True) 
        x = self.winfo_screenwidth() - 380
        y = self.winfo_screenheight() - 150
        toast.geometry(f"350x100+{x}+{y}")
        toast.configure(fg_color=bg_color)
        ctk.CTkLabel(toast, text=title, font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(toast, text=message, font=ctk.CTkFont(family="Montserrat", size=14), text_color="white").pack()
        self.after(3500, toast.destroy)

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.dashboard_repository = self.app.di.get_dashboard_repository()
        
        self.font_title = ctk.CTkFont(family="Montserrat", size=34, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Montserrat", size=16)
        self.font_bold13 = ctk.CTkFont(family="Montserrat", weight="bold", size=13)
        self.font_norm13 = ctk.CTkFont(family="Montserrat", size=13)
        self.font_badge = ctk.CTkFont(family="Montserrat", size=11, weight="bold")
        self.font_italic = ctk.CTkFont(family="Montserrat", slant="italic")

        ita_days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        ita_months = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        today = datetime.now()
        date_today = f"{ita_days[today.weekday()]}, {today.day} {ita_months[today.month]} {today.year}"

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text="Dashboard", font=self.font_title, text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text=date_today, font=self.font_subtitle, text_color=("#86868B", "#98989D")).pack(anchor="w", pady=(5, 0))

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 25))
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.var_tot_members = ctk.StringVar(value="...")
        self.var_lessons_today = ctk.StringVar(value="...")
        self.var_expiring_soon = ctk.StringVar(value="...")

        self.create_card(self.cards_frame, 0, "Soci Attivi (In Regola)", self.var_tot_members, "soci", "#007AFF", (0, 10))
        self.create_card(self.cards_frame, 1, "Corsi Odierni", self.var_lessons_today, "calendario", "#FF9500", (10, 10))
        self.create_card(self.cards_frame, 2, "Scadenze Imminenti", self.var_expiring_soon, "impostazioni", "#FF3B30", (10, 0))

        body_layout = ctk.CTkFrame(self, fg_color="transparent")
        body_layout.pack(fill="both", expand=True)
        body_layout.grid_columnconfigure(0, weight=35) 
        body_layout.grid_columnconfigure(1, weight=65)
        body_layout.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(body_layout, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        actions_card = ctk.CTkFrame(left_col, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        actions_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(actions_card, text="⚡ Azioni Rapide", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 15))

        self.create_action_button(actions_card, "👤 Anagrafica Soci", "#007AFF", lambda: self.app.show_view("members"))
        self.create_action_button(actions_card, "🎫 Controllo Accessi", "#FF3B30", lambda: self.app.show_view("turnstile"))
        self.create_action_button(actions_card, "📅 Calendario Corsi", "#FF9500", lambda: self.app.show_view("calendar"), is_last=True)

        lessons_card = ctk.CTkFrame(left_col, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        lessons_card.pack(fill="both", expand=True) 
        
        ctk.CTkLabel(lessons_card, text="📍 Corsi in Programma Oggi", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 15))
        
        self.scroll_lessons_today = ctk.CTkScrollableFrame(lessons_card, fg_color="transparent")
        self.scroll_lessons_today.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        expiring_card = ctk.CTkFrame(body_layout, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        expiring_card.grid(row=0, column=1, sticky="nsew")
        
        header_scad = ctk.CTkFrame(expiring_card, fg_color="transparent")
        header_scad.pack(fill="x", padx=20, pady=(20, 5))
        
        ctk.CTkLabel(header_scad, text="⚠️ Scadenze Mensilità", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
        ctk.CTkLabel(header_scad, text="Prossimi 2 giorni", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color="#FF3B30", fg_color=("#FFE5E5", "#4A1010"), corner_radius=6, padx=8, pady=4).pack(side="left", padx=15)
        
        ctk.CTkLabel(expiring_card, text="Doppio click su un nome per aprire la scheda e registrare il rinnovo", font=ctk.CTkFont(family="Montserrat", size=13), text_color=("#86868B", "#98989D")).pack(anchor="w", padx=20, pady=(0, 15))

        self.scroll_expiring = ctk.CTkScrollableFrame(expiring_card, fg_color="transparent")
        self.scroll_expiring.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.load_stats()

    def open_member_card(self, member_id):
        from src.pkg.view.soci_window import MemberFormWindow
        MemberFormWindow(self.app, self.app, refresh_callback=self.load_stats, member_id=member_id)

    def create_action_button(self, parent, text, color, command, is_last=False):
        btn = ctk.CTkButton(parent, text=text, command=command, font=ctk.CTkFont(family="Montserrat", size=15, weight="bold"), fg_color=("#F8F8F9", "#3A3A3C"), text_color=color, hover_color=("#E5E5EA", "#48484A"), border_width=0, corner_radius=10, height=48, anchor="w")
        pady_val = (0, 10) if not is_last else (0, 20)
        btn.pack(fill="x", padx=20, pady=pady_val)

    def create_card(self, parent, col, title, text_variable, icon_name, accent_color, padx_val):
        card = ctk.CTkFrame(parent, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, height=145, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        card.grid(row=0, column=col, padx=padx_val, sticky="ew")
        card.grid_propagate(False)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 5))
        icon_box = ctk.CTkFrame(header, width=32, height=32, corner_radius=8, fg_color=accent_color)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        
        icon_img = self.app.load_icon(f"{icon_name}_white", 20) or self.app.load_icon(icon_name, 20)
        if icon_img: ctk.CTkLabel(icon_box, text="", image=icon_img).place(relx=0.5, rely=0.5, anchor="center")
        else: ctk.CTkLabel(icon_box, text="▪", text_color="white", font=ctk.CTkFont(family="Montserrat", size=16)).place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=12)
        lbl_val = ctk.CTkLabel(card, textvariable=text_variable, font=ctk.CTkFont(family="Montserrat", size=38, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_val.pack(anchor="w", padx=20, pady=(5, 0))

    def load_stats(self):
        stats = self.dashboard_repository.get_dashboard_stats()

        self.var_tot_members.set(str(stats["active_members"]))
        self.var_lessons_today.set(str(stats["lessons_count"]))
        self.var_expiring_soon.set(str(stats["expiring_count"]))
        
        for widget in self.scroll_lessons_today.winfo_children(): widget.destroy()
        
        if not stats["lessons_today"]:
            ctk.CTkLabel(self.scroll_lessons_today, text="Nessun corso programmato oggi.", font=self.font_italic, text_color=("#86868B", "#98989D")).pack(pady=30)
        else:
            for l in stats["lessons_today"]:
                row_c = ctk.CTkFrame(self.scroll_lessons_today, fg_color="transparent")
                row_c.pack(fill="x", pady=6)
                
                ctk.CTkLabel(row_c, text=l['lesson_name'], font=self.font_bold13, text_color=("#1D1D1F", "#FFFFFF")).pack(side="left", padx=5)
                
                badge_color = "#34C759" if l['occupati'] < l['total_seats'] else "#FF3B30"
                badge = ctk.CTkFrame(row_c, fg_color=badge_color, corner_radius=6, height=22, width=50)
                badge.pack(side="right", padx=5)
                badge.pack_propagate(False)
                ctk.CTkLabel(badge, text=f"{l['occupati']}/{l['total_seats']}", text_color="white", font=self.font_badge).place(relx=0.5, rely=0.5, anchor="center")

        for widget in self.scroll_expiring.winfo_children(): widget.destroy()
        
        if not stats["expiring_list"]:
            ctk.CTkLabel(self.scroll_expiring, text="Nessuna scadenza nei prossimi giorni. 🎉", font=self.font_italic, text_color=("#86868B", "#98989D")).pack(pady=40)
        else:
            for item in stats["expiring_list"]:
                row_s = ctk.CTkFrame(self.scroll_expiring, fg_color=("#F8F8F9", "#3A3A3C"), height=50, corner_radius=10, cursor="hand2")
                row_s.pack(fill="x", pady=4, padx=5)
                row_s.pack_propagate(False)
                
                if item["exp_date"] == stats["date_today"]:
                    exp_text = "🔴 Scade OGGI"
                    exp_color = "#FF3B30"
                elif item["exp_date"] == stats["date_tomorrow"]:
                    exp_text = "🟠 Scade DOMANI"
                    exp_color = "#FF9500"
                else:
                    exp_text = f"🟡 Scade il {item['exp_date'].strftime('%d/%m')}"
                    exp_color = "#FF9500"

                badge_exp = ctk.CTkFrame(row_s, fg_color="transparent")
                badge_exp.pack(side="right", padx=15)
                ctk.CTkLabel(badge_exp, text=exp_text, font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=exp_color).pack()

                badge_txt = f" [{item['badge']}]" if item['badge'] else ""
                
                lbl_n = ctk.CTkLabel(row_s, text=item["full_name"] + badge_txt, font=self.font_bold13, text_color=("#1D1D1F", "#FFFFFF"))
                lbl_n.pack(side="left", padx=20)

                for w in [row_s, lbl_n, badge_exp] + badge_exp.winfo_children():
                    w.bind("<Double-Button-1>", lambda e, mid=item["id"]: self.open_member_card(mid))
                    w.bind("<Enter>", lambda e, fr=row_s: fr.configure(fg_color=("#E5E5EA", "#48484A")))
                    w.bind("<Leave>", lambda e, fr=row_s: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")))
